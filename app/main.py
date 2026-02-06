from fastapi import FastAPI

app = FastAPI(title="PipelineInsight")

@app.get("/")
def read_root():
    return{
        "message": "Welcome to PipelineInsight!",
        "status": "running"
    }
    
@app.get("/health")
def health_check():
    return{"status": "healthy"}