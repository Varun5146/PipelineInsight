import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class GitHubClient:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.username = os.getenv("GITHUB_USERNAME")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def get_repositories(self):
        """Get all repositories for the authenticated user"""
        url = f"{self.base_url}/user/repos"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Failed to fetch repos: {response.status_code}"}
    
    def get_workflows(self, repo_name):
        """Get all workflows for a specific repository"""
        url = f"{self.base_url}/repos/{self.username}/{repo_name}/actions/workflows"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Failed to fetch workflows: {response.status_code}"}
    
    def get_workflow_runs(self, repo_name, workflow_id):
        """Get recent runs for a specific workflow"""
        url = f"{self.base_url}/repos/{self.username}/{repo_name}/actions/workflows/{workflow_id}/runs"
        response = requests.get(url, headers=self.headers, params={"per_page": 10})
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Failed to fetch workflow runs: {response.status_code}"}