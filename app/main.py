from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.github_client import GitHubClient
from app.database import engine, get_db
from app import models
from datetime import datetime
# Create database tables FIRST
models.Base.metadata.create_all(bind=engine)

# Create the app (ONLY ONCE!)
app = FastAPI(title="PipelineInsight")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Create GitHub client
github = GitHubClient()

# Dashboard route
@app.get("/dashboard")
def dashboard():
    """Serve the dashboard HTML page"""
    return FileResponse("app/static/dashboard.html")

@app.get("/")
def read_root():
    return {
        "message": "Welcome to PipelineInsight!",
        "status": "running",
        "version": "0.1.0"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/repos")
def get_repos():
    """Get all repositories"""
    repos = github.get_repositories()
    if isinstance(repos, list):
        return {
            "count": len(repos),
            "repositories": [
                {
                    "name": repo["name"],
                    "full_name": repo["full_name"],
                    "private": repo["private"],
                    "has_workflows": repo.get("has_actions", False)
                }
                for repo in repos
            ]
        }
    return repos

@app.get("/repos/{repo_name}/workflows")
def get_workflows(repo_name: str):
    """Get workflows for a specific repository"""
    workflows = github.get_workflows(repo_name)
    return workflows

@app.get("/repos/{repo_name}/workflows/{workflow_id}/runs")
def get_workflow_runs(repo_name: str, workflow_id: int):
    """Get recent runs for a specific workflow"""
    runs = github.get_workflow_runs(repo_name, workflow_id)
    return runs

@app.post("/collect/{repo_name}")
def collect_workflow_data(repo_name: str, db: Session = Depends(get_db)):
    """Collect and store workflow data for a repository"""
    # Get workflows for the repo
    workflows_response = github.get_workflows(repo_name)
    
    if "error" in workflows_response:
        return workflows_response
    
    workflows = workflows_response.get("workflows", [])
    collected_count = 0
    
    for workflow in workflows:
        workflow_id = workflow["id"]
        workflow_name = workflow["name"]
        
        # Get recent runs for this workflow
        runs_response = github.get_workflow_runs(repo_name, workflow_id)
        
        if "error" not in runs_response:
            runs = runs_response.get("workflow_runs", [])
            
            for run in runs:
                # Check if we already have this run
                existing_run = db.query(models.WorkflowRun).filter(
                    models.WorkflowRun.run_id == run["id"]
                ).first()
                
                if not existing_run:
                    # Calculate duration if completed
                    duration = None
                    if run.get("run_started_at") and run.get("updated_at"):
                        start = datetime.fromisoformat(run["run_started_at"].replace("Z", "+00:00"))
                        end = datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
                        duration = (end - start).total_seconds()
                    
                    # Create new workflow run record
                    workflow_run = models.WorkflowRun(
                        repo_name=repo_name,
                        workflow_name=workflow_name,
                        workflow_id=workflow_id,
                        run_id=run["id"],
                        status=run["status"],
                        conclusion=run.get("conclusion"),
                        run_number=run["run_number"],
                        created_at=datetime.fromisoformat(run["created_at"].replace("Z", "+00:00")),
                        updated_at=datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00")),
                        run_started_at=datetime.fromisoformat(run["run_started_at"].replace("Z", "+00:00")) if run.get("run_started_at") else None,
                        duration_seconds=duration
                    )
                    
                    db.add(workflow_run)
                    collected_count += 1
    
    db.commit()
    
    return {
        "message": f"Collected workflow data for {repo_name}",
        "workflows_found": len(workflows),
        "new_runs_collected": collected_count
    }

@app.get("/stats/{repo_name}")
def get_repo_stats(repo_name: str, db: Session = Depends(get_db)):
    """Get statistics for a repository's workflows"""
    runs = db.query(models.WorkflowRun).filter(
        models.WorkflowRun.repo_name == repo_name
    ).all()
    
    if not runs:
        return {"message": "No data collected yet. Use /collect/{repo_name} first"}
    
    total_runs = len(runs)
    successful = len([r for r in runs if r.conclusion == "success"])
    failed = len([r for r in runs if r.conclusion == "failure"])
    
    # Calculate average duration for completed runs
    completed_with_duration = [r for r in runs if r.duration_seconds is not None]
    avg_duration = sum(r.duration_seconds for r in completed_with_duration) / len(completed_with_duration) if completed_with_duration else 0
    
    return {
        "repo_name": repo_name,
        "total_runs": total_runs,
        "successful": successful,
        "failed": failed,
        "success_rate": f"{(successful/total_runs*100):.1f}%" if total_runs > 0 else "0%",
        "average_duration_seconds": round(avg_duration, 2),
        "average_duration_minutes": round(avg_duration / 60, 2)
    }