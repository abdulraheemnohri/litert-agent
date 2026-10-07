"""FastAPI Web UI backend."""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="LiteRT Agent Web UI")

@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <html>
        <head><title>LiteRT Autonomous Agent</title></head>
        <body>
            <h1>LiteRT Agent Dashboard</h1>
            <p>Model: LiteRT-LM CLI</p>
        </body>
    </html>
    """
