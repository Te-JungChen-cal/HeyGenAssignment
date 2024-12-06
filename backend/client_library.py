from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import aiohttp
import asyncio
import uvicorn

app = FastAPI()

# Allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
pending_duration = 10  # Make sure this matches the server's configuration
server_url = "http://localhost:9000/status"  # Base URL of the status API


@app.get("/client_status")
async def status_updates(request: Request):
    """
    SSE endpoint to stream real-time status updates of a job to the client.

    This endpoint establishes a Server-Sent Events (SSE) connection and streams 
    the status updates of a job retrieved from an external job management API. 
    The updates are sent in real-time as JSON objects, prefixed with `data:` 
    and terminated with two newline characters, adhering to the SSE protocol.

    Workflow:
    - A new job is created by sending a request to the external API, and its ID (`job_id`) is returned.
    - The status of the job is queried periodically until the job is completed, an error occurs, or the client disconnects.
    - Status updates are streamed back to the client.

    Streamed Data Format:
    - Messages are sent in sse the following format:
      data: {"result": "<status>", "message": "<optional message>"}
    - Status values include:
        - "pending": Job is in progress.
        - "completed": Job has finished successfully.
        - "error": An error occurred during job processing.

    Behavior:
    - If the job creation fails, an error message is sent, and the stream is closed.
    - If the job ID is not found during subsequent queries, an error message is sent, and the stream is closed.
    - If the client disconnects during the stream, the server stops processing.

    Args:
        request (Request): The incoming HTTP request, used to detect client disconnections.

    Returns:
        EventSourceResponse: A streaming response that sends job status updates in real-time.
    """
    async def event_generator(request: Request):
        async with aiohttp.ClientSession() as session:
            # Get a new job ID from the server
            async with session.get(server_url) as response:
                if response.status != 200:
                    yield f"{{'result': 'error', 'message': 'Unable to create job'}}\n\n"
                    return
                
                job_data = await response.json()
                job_id = job_data.get("job_id")

            while True:
                # Query the job status
                async with session.get(f"{server_url}/{job_id}") as response:
                    if response.status != 200:
                        yield f"{{'result': 'error', 'message': 'Job not found'}}\n\n"
                        return

                    status = await response.json()

                # Yield the current status to the client
                yield f"{status}\n\n"

                # Break the loop if status is "completed" or "error"
                if status.get("result") in ["completed", "error"]:
                    break

                # Check if the client has disconnected
                if await request.is_disconnected():
                    break

                await asyncio.sleep(1)  # Sleep for a second before sending the next update

    return EventSourceResponse(event_generator(request))


if __name__ == "__main__":
    uvicorn.run("client_library:app", host="0.0.0.0", port=8000, reload=True)