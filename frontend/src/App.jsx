import React, { useState } from "react";

const App = () => {
  const [status, setStatus] = useState("Click the button to fetch status");
  const [log, setLog] = useState([]);
  const [sseConnection, setSseConnection] = useState(null);

  const connectToSSE = () => {
    // Close any existing SSE connection
    if (sseConnection) {
      sseConnection.close();
    }

    // Create a new SSE connection
    const eventSource = new EventSource("http://127.0.0.1:8000/client_status");

    eventSource.onmessage = (event) => {
      console.log(event.data);
      const rawData = event.data;
      const cleanData = rawData.startsWith("data:")
        ? rawData.slice(5).trim()
        : rawData;
      const jsonData = cleanData.replace(/'/g, '"');
      const data = JSON.parse(jsonData);
      setStatus(data.result);
      setLog((prevLog) => [...prevLog, `Status updated: ${data.result}`]);

      // Close the connection if the job is completed or errored
      if (data.result === "completed" || data.result === "error") {
        eventSource.close();
        setSseConnection(null);
      }
    };

    eventSource.onerror = (error) => {
      console.error("SSE connection error:", error);
      setLog((prevLog) => [...prevLog, "SSE connection error"]);
      eventSource.close();
      setSseConnection(null);
    };

    setSseConnection(eventSource);
  };

  return (
    <div>
      <h1>Job Status</h1>
      <p>
        Current Status: <strong>{status}</strong>
      </p>
      <button onClick={connectToSSE} disabled={!!sseConnection}>
        {sseConnection ? "Listening for Updates..." : "Fetch Status"}
      </button>
      <h2>Logs:</h2>
      <ul>
        {log.map((entry, index) => (
          <li key={index}>{entry}</li>
        ))}
      </ul>
    </div>
  );
};

export default App;
