from fastapi import FastAPI, HTTPException
import time
import uvicorn
import uuid  # Import for generating unique job IDs

app = FastAPI()

# Configuration
pending_duration = 10  # Time in seconds before the result becomes "completed"

# Map to store job start times
job_start_times = {}


@app.get("/status")
@app.get("/status/{job_id}")
def get_status(job_id: str = ""):
    """
    API to return the current status of a job by job_id.
    If job_id is not provided or is an empty string, a new job is created and returned as "pending".
    """
    if job_id == "":
        # Generate a new unique job ID
        new_job_id = str(uuid.uuid4())
        job_start_times[new_job_id] = time.time()
        return {"job_id": new_job_id, "result": "pending"}
    
    if job_id not in job_start_times:
        raise HTTPException(status_code=404, detail="Job ID not found")
    
    elapsed_time = time.time() - job_start_times[job_id]
    if elapsed_time >= pending_duration:
        # Remove the job from the dictionary
        del job_start_times[job_id]
        return {"result": "completed"}
    else:
        return {"result": "pending"}

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=9000, reload=True)