import pytest
import asyncio
from httpx import AsyncClient
from multiprocessing import Process
import uvicorn
from server import app as job_server_app  # Import the job status server
from client_library import app as client_sse_app  # Import the SSE client server
import logging
import time

logging.basicConfig(level=logging.INFO)

@pytest.fixture(scope="module")
def run_job_server():
    process = Process(target=uvicorn.run, args=("server:app",), kwargs={"host": "0.0.0.0", "port": 9000, "log_level": "info"})
    process.start()
    time.sleep(1)  # Wait for the server to initialize
    yield
    process.terminate()
    process.join()



@pytest.fixture(scope="module")
def run_client_sse_server():
    process = Process(target=uvicorn.run, args=("client_library:app",), kwargs={"host": "0.0.0.0", "port": 8000, "log_level": "info"})
    process.start()
    time.sleep(1)  # Wait for the server to initialize
    yield
    process.terminate()
    process.join()

@pytest.mark.asyncio
async def test_integration_status_updates(run_job_server, run_client_sse_server):
    """
    Integration test for the SSE endpoint to verify the streaming of statuses from the job server.
    """
    async with AsyncClient(base_url="http://localhost:8000", timeout=20.0) as client:
        async with client.stream("GET", "/client_status") as response:

            assert response.status_code == 200

            # Stream and capture events
            received_events = []
            async for event in response.aiter_lines():
                if event.startswith("data:"):
                    data = event[len("data: "):]
                    if len(data) > 0: 
                        print(data)
                        received_events.append(data)

                # Break when "completed" status is received
                if "completed" in event:
                    break


            # Assert the expected sequence
            assert len(received_events) >= 2  # At least "pending" and "completed"
            assert received_events[-1] == "{'result': 'completed'}"
            for event in received_events[:-1]:
                assert event == "{'result': 'pending'}"