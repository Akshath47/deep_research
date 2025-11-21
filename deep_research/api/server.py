"""
FastAPI Server for Deep Research Agent

Provides streaming endpoints for the LangGraph workflow to support
the three UI states from design.md:
1. The Prompt (Idle State)
2. The Process (Working State) - with live activity feed
3. The Result (Output State)
"""

import sys
import os
import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, AsyncIterator
from contextlib import asynccontextmanager

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
# Use override=True so the repo's .env values win over any shell defaults
load_dotenv(env_path, override=True)

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

# Import LangGraph workflow
from graphs.workflow import graph  # Import the graph, not the compiled app
from state import ResearchFlowState, read_text, read_json
from langgraph.checkpoint.memory import MemorySaver

# Thread management
from threading import Lock

# Compile the graph with a checkpointer for API usage
checkpointer = MemorySaver()
langgraph_app = graph.compile(checkpointer=checkpointer)


# ===== Data Models =====

class ResearchRequest(BaseModel):
    """Request to start a new research task."""
    query: str = Field(..., description="The research query to investigate")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Optional configuration")


class ResearchResponse(BaseModel):
    """Response when starting a research task."""
    thread_id: str = Field(..., description="Unique thread ID for this research session")
    status: str = Field(..., description="Status: queued, running, completed, error")
    message: str = Field(..., description="Human-readable message")


class ResearchStatus(BaseModel):
    """Current status of a research thread."""
    thread_id: str
    status: str  # queued, running, completed, error
    current_agent: Optional[str] = None
    progress_percentage: Optional[int] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


class AgentMetadata(BaseModel):
    """Metadata about an agent node for frontend tracking."""
    name: str
    display_name: str
    description: str
    icon: str
    order: int


# ===== In-Memory Thread Storage =====

class ThreadManager:
    """Manages research threads and their states."""

    def __init__(self):
        self.threads: Dict[str, Dict[str, Any]] = {}
        self.lock = Lock()

    def create_thread(self, query: str) -> str:
        """Create a new research thread."""
        thread_id = str(uuid.uuid4())
        with self.lock:
            self.threads[thread_id] = {
                "thread_id": thread_id,
                "query": query,
                "status": "queued",
                "current_agent": None,
                "progress_percentage": 0,
                "started_at": None,
                "completed_at": None,
                "error": None,
                "state": None,
                "events": []
            }
        return thread_id

    def get_thread(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get thread data."""
        with self.lock:
            return self.threads.get(thread_id)

    def update_thread(self, thread_id: str, updates: Dict[str, Any]):
        """Update thread data."""
        with self.lock:
            if thread_id in self.threads:
                self.threads[thread_id].update(updates)

    def add_event(self, thread_id: str, event: Dict[str, Any]):
        """Add an event to thread history."""
        with self.lock:
            if thread_id in self.threads:
                self.threads[thread_id]["events"].append(event)


thread_manager = ThreadManager()


# ===== Agent Metadata =====

AGENT_METADATA = {
    "clarifier": AgentMetadata(
        name="clarifier",
        display_name="Clarifier",
        description="Analyzing query for ambiguities and clarifications",
        icon="search",
        order=1
    ),
    "decomposer": AgentMetadata(
        name="decomposer",
        display_name="Decomposer",
        description="Breaking down complex query into sub-questions",
        icon="split",
        order=2
    ),
    "strategist": AgentMetadata(
        name="strategist",
        display_name="Strategist",
        description="Planning research strategy and approach",
        icon="target",
        order=3
    ),
    "researcher_hub": AgentMetadata(
        name="researcher_hub",
        display_name="Researcher Hub",
        description="Conducting parallel research across sub-questions",
        icon="users",
        order=4
    ),
    "fact_checker": AgentMetadata(
        name="fact_checker",
        display_name="Fact Checker",
        description="Verifying facts and detecting contradictions",
        icon="check-circle",
        order=5
    ),
    "synthesizer": AgentMetadata(
        name="synthesizer",
        display_name="Synthesizer",
        description="Synthesizing findings into comprehensive report",
        icon="file-text",
        order=6
    ),
    "reviewer": AgentMetadata(
        name="reviewer",
        display_name="Reviewer",
        description="Performing final quality checks and validation",
        icon="eye",
        order=7
    )
}


# ===== FastAPI App =====

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI app."""
    # Startup
    print("🚀 Deep Research API starting up...")
    yield
    # Shutdown
    print("👋 Deep Research API shutting down...")


app = FastAPI(
    title="Deep Research API",
    description="Streaming API for LangGraph-based research agent",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Next.js dev ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== Helper Functions =====

def calculate_progress(node_name: str) -> int:
    """Calculate progress percentage based on current node."""
    node_order = AGENT_METADATA.get(node_name, AgentMetadata(name="", display_name="", description="", icon="", order=0)).order
    total_nodes = len(AGENT_METADATA)
    return int((node_order / total_nodes) * 100) if total_nodes > 0 else 0


async def run_research_workflow(thread_id: str, query: str):
    """
    Run the LangGraph workflow and track progress.
    This runs in the background and updates the thread state.
    """
    try:
        # Update status to running
        thread_manager.update_thread(thread_id, {
            "status": "running",
            "started_at": datetime.now().isoformat()
        })

        # Prepare initial state
        initial_state: ResearchFlowState = {
            "files": {
                "query.txt": query
            }
        }

        # Config with thread_id for checkpointer
        config = {"configurable": {"thread_id": thread_id}}

        # Stream the workflow execution
        async for event in langgraph_app.astream(
            initial_state,
            config=config,
            stream_mode=["updates", "debug"]
        ):
            # Process different event types
            if isinstance(event, dict):
                # Handle updates stream mode
                for node_name, node_output in event.items():
                    if node_name != "__start__" and node_name != "__end__":
                        # Update current agent
                        thread_manager.update_thread(thread_id, {
                            "current_agent": node_name,
                            "progress_percentage": calculate_progress(node_name)
                        })

                        # Add event
                        agent_metadata = AGENT_METADATA.get(node_name)
                        thread_manager.add_event(thread_id, {
                            "type": "agent_update",
                            "timestamp": datetime.now().isoformat(),
                            "agent": node_name,
                            "agent_display_name": agent_metadata.display_name if agent_metadata else node_name,
                            "agent_description": agent_metadata.description if agent_metadata else "",
                            "status": "running"
                        })

        # Get final state (the state is already stored by the checkpointer)
        # We'll extract it from the last stream event instead
        final_state = initial_state  # Will be updated by streaming

        # Mark as completed
        thread_manager.update_thread(thread_id, {
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "progress_percentage": 100,
            "state": final_state
        })

        # Add completion event
        thread_manager.add_event(thread_id, {
            "type": "complete",
            "timestamp": datetime.now().isoformat(),
            "message": "Research completed successfully"
        })

    except Exception as e:
        # Handle errors
        error_message = str(e)
        thread_manager.update_thread(thread_id, {
            "status": "error",
            "error": error_message,
            "completed_at": datetime.now().isoformat()
        })

        thread_manager.add_event(thread_id, {
            "type": "error",
            "timestamp": datetime.now().isoformat(),
            "error": error_message
        })

        print(f"❌ Error in thread {thread_id}: {error_message}")


# ===== API Endpoints =====

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "Deep Research API",
        "status": "running",
        "version": "0.1.0"
    }


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/api/agents")
async def list_agents():
    """Get metadata about all available agents."""
    return {
        "agents": [agent.model_dump() for agent in AGENT_METADATA.values()]
    }


@app.post("/api/research/start", response_model=ResearchResponse)
async def start_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks
):
    """
    Start a new research task.

    This creates a thread and starts the LangGraph workflow in the background.
    The client should then connect to the streaming endpoint to receive updates.
    """
    # Create thread
    thread_id = thread_manager.create_thread(request.query)

    # Start workflow in background
    background_tasks.add_task(run_research_workflow, thread_id, request.query)

    return ResearchResponse(
        thread_id=thread_id,
        status="queued",
        message=f"Research started for query: {request.query[:50]}..."
    )


@app.get("/api/research/status/{thread_id}", response_model=ResearchStatus)
async def get_research_status(thread_id: str):
    """
    Get current status of a research thread.

    This is useful for polling-based clients or checking status before connecting to stream.
    """
    thread = thread_manager.get_thread(thread_id)

    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    return ResearchStatus(
        thread_id=thread["thread_id"],
        status=thread["status"],
        current_agent=thread["current_agent"],
        progress_percentage=thread["progress_percentage"],
        started_at=thread["started_at"],
        completed_at=thread["completed_at"],
        error=thread["error"]
    )


@app.get("/api/research/stream/{thread_id}")
async def stream_research(thread_id: str):
    """
    Stream real-time updates for a research thread using Server-Sent Events (SSE).

    This endpoint provides the live activity feed for the "Working State" in the UI.

    Events emitted:
    - agent_update: When an agent starts/completes
    - progress: Progress percentage updates
    - complete: Research completed
    - error: Error occurred
    """
    thread = thread_manager.get_thread(thread_id)

    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    async def event_generator() -> AsyncIterator[str]:
        """Generate SSE events."""
        last_event_index = 0

        # Send initial status
        yield {
            "event": "status",
            "data": json.dumps({
                "type": "status",
                "status": thread["status"],
                "progress_percentage": thread["progress_percentage"]
            })
        }

        # Stream events
        while True:
            current_thread = thread_manager.get_thread(thread_id)

            if not current_thread:
                break

            # Send new events
            events = current_thread["events"]
            if len(events) > last_event_index:
                for event in events[last_event_index:]:
                    yield {
                        "event": event["type"],
                        "data": json.dumps(event)
                    }
                last_event_index = len(events)

            # Check if completed or errored
            if current_thread["status"] in ["completed", "error"]:
                yield {
                    "event": "done",
                    "data": json.dumps({
                        "type": "done",
                        "status": current_thread["status"]
                    })
                }
                break

            # Wait before checking again
            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())


@app.get("/api/research/result/{thread_id}")
async def get_research_result(thread_id: str):
    """
    Get the final research results.

    This provides the data for the "Result State" in the UI.
    """
    thread = thread_manager.get_thread(thread_id)

    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    if thread["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Research not completed yet. Current status: {thread['status']}"
        )

    # Extract results from state
    state = thread.get("state", {})
    files = state.get("files", {}) if state else {}

    # Read the final report
    report = files.get("final_report.md", "")

    # Read sub-questions
    subqueries = []
    try:
        subqueries_data = json.loads(files.get("subqueries.json", "[]"))
        subqueries = subqueries_data if isinstance(subqueries_data, list) else []
    except:
        pass

    # Read citations/sources
    citations = []
    for file_path, content in files.items():
        if file_path.startswith("research/") and file_path.endswith(".md"):
            # Extract sources from research files
            # This is a simple implementation - can be enhanced
            if "Sources:" in content or "References:" in content:
                citations.append({
                    "file": file_path,
                    "content": content
                })

    return {
        "thread_id": thread_id,
        "status": "completed",
        "report": report,
        "subqueries": subqueries,
        "citations": citations,
        "files": files,
        "metadata": {
            "started_at": thread["started_at"],
            "completed_at": thread["completed_at"],
            "total_time": thread["completed_at"]  # Could calculate duration
        }
    }


@app.get("/api/research/logs/{thread_id}")
async def get_research_logs(thread_id: str):
    """
    Get verbose logs for technical users.

    This supports the "Show Logs" toggle mentioned in the design doc.
    """
    thread = thread_manager.get_thread(thread_id)

    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    return {
        "thread_id": thread_id,
        "events": thread["events"],
        "status": thread["status"]
    }


@app.post("/api/research/pdf/{thread_id}")
async def generate_pdf(thread_id: str):
    """
    Generate a PDF report from the research results.

    This implements the "Download PDF" button from the design doc.
    """
    thread = thread_manager.get_thread(thread_id)

    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    if thread["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail="Research not completed yet"
        )

    # For now, return a simple response
    # In production, implement PDF generation using WeasyPrint or similar
    return {
        "message": "PDF generation not yet implemented",
        "thread_id": thread_id
    }

    # TODO: Implement PDF generation
    # from weasyprint import HTML
    # html_content = markdown_to_html(report)
    # pdf = HTML(string=html_content).write_pdf()
    # return FileResponse(pdf_path, media_type="application/pdf", filename=f"research_{thread_id}.pdf")


# ===== Development Server =====

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
