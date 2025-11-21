"""
Advanced streaming utilities for LangGraph workflow.

Provides real-time node execution tracking with detailed metadata
for the frontend "Working State" visualization.
"""

import json
from datetime import datetime
from typing import Dict, Any, AsyncIterator, Optional
from enum import Enum


class EventType(str, Enum):
    """Types of events emitted during research."""
    START = "start"
    AGENT_START = "agent_start"
    AGENT_PROGRESS = "agent_progress"
    AGENT_COMPLETE = "agent_complete"
    SUBQUERY_START = "subquery_start"
    SUBQUERY_COMPLETE = "subquery_complete"
    PROGRESS = "progress"
    LOG = "log"
    ERROR = "error"
    COMPLETE = "complete"


class StreamEventFormatter:
    """Formats LangGraph events for frontend consumption."""

    def __init__(self):
        self.node_order = [
            "clarifier",
            "decomposer",
            "strategist",
            "researcher_hub",
            "fact_checker",
            "synthesizer",
            "reviewer"
        ]

    def format_node_event(
        self,
        node_name: str,
        event_type: EventType,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Format a node execution event."""
        return {
            "type": event_type.value,
            "timestamp": datetime.now().isoformat(),
            "agent": node_name,
            "data": data or {}
        }

    def calculate_progress(self, node_name: str) -> int:
        """Calculate progress percentage based on current node."""
        try:
            index = self.node_order.index(node_name)
            return int(((index + 1) / len(self.node_order)) * 100)
        except ValueError:
            return 0

    def format_sse_event(self, event: Dict[str, Any]) -> str:
        """Format event as Server-Sent Event."""
        event_type = event.get("type", "message")
        data = json.dumps(event)
        return f"event: {event_type}\ndata: {data}\n\n"


async def stream_langgraph_execution(
    graph,
    initial_state: Dict[str, Any],
    thread_id: str
) -> AsyncIterator[Dict[str, Any]]:
    """
    Stream LangGraph execution with detailed progress tracking.

    Yields events for:
    - Each node start/complete
    - Progress updates
    - Subquery execution (for researcher_hub)
    - Errors
    - Final completion

    Args:
        graph: Compiled LangGraph application
        initial_state: Initial state for the workflow
        thread_id: Unique thread identifier

    Yields:
        Event dictionaries with type, timestamp, agent, and data
    """
    formatter = StreamEventFormatter()

    try:
        # Emit start event
        yield formatter.format_node_event(
            "system",
            EventType.START,
            {"thread_id": thread_id, "message": "Research workflow starting"}
        )

        current_node = None
        node_start_time = None

        # Stream with multiple modes to get detailed information
        async for chunk in graph.astream(
            initial_state,
            stream_mode=["updates", "debug"],
            config={"configurable": {"thread_id": thread_id}}
        ):
            # Handle different chunk types
            if isinstance(chunk, tuple):
                # Debug mode: (node_name, event_type, data)
                stream_mode, data = chunk
                if stream_mode == "debug":
                    # Extract node information
                    if "type" in data and data["type"] == "task":
                        task_data = data.get("payload", {})
                        node_name = task_data.get("name", "unknown")

                        if node_name != "__start__" and node_name != "__end__":
                            # Node started
                            current_node = node_name
                            node_start_time = datetime.now()

                            yield formatter.format_node_event(
                                node_name,
                                EventType.AGENT_START,
                                {
                                    "progress": formatter.calculate_progress(node_name),
                                    "message": f"Starting {node_name}"
                                }
                            )

            elif isinstance(chunk, dict):
                # Updates mode: {node_name: output}
                for node_name, node_output in chunk.items():
                    if node_name == "__start__" or node_name == "__end__":
                        continue

                    # Check for researcher_hub special handling
                    if node_name == "researcher_hub" and isinstance(node_output, dict):
                        files = node_output.get("files", {})

                        # Try to extract subquery information
                        subqueries_file = files.get("subqueries.json", "")
                        if subqueries_file:
                            try:
                                subqueries = json.loads(subqueries_file)
                                if isinstance(subqueries, list):
                                    yield formatter.format_node_event(
                                        "researcher_hub",
                                        EventType.AGENT_PROGRESS,
                                        {
                                            "message": f"Researching {len(subqueries)} sub-questions in parallel",
                                            "subquery_count": len(subqueries)
                                        }
                                    )
                            except:
                                pass

                    # Node completed
                    if current_node == node_name:
                        elapsed_time = None
                        if node_start_time:
                            elapsed = datetime.now() - node_start_time
                            elapsed_time = elapsed.total_seconds()

                        yield formatter.format_node_event(
                            node_name,
                            EventType.AGENT_COMPLETE,
                            {
                                "progress": formatter.calculate_progress(node_name),
                                "elapsed_time": elapsed_time,
                                "message": f"Completed {node_name}"
                            }
                        )

                        # Emit progress update
                        yield formatter.format_node_event(
                            "system",
                            EventType.PROGRESS,
                            {"progress": formatter.calculate_progress(node_name)}
                        )

                    current_node = None
                    node_start_time = None

        # Emit completion event
        yield formatter.format_node_event(
            "system",
            EventType.COMPLETE,
            {
                "thread_id": thread_id,
                "message": "Research workflow completed successfully",
                "progress": 100
            }
        )

    except Exception as e:
        # Emit error event
        yield formatter.format_node_event(
            "system",
            EventType.ERROR,
            {
                "thread_id": thread_id,
                "error": str(e),
                "message": f"Error during research: {str(e)}"
            }
        )
        raise


async def stream_with_verbose_logs(
    graph,
    initial_state: Dict[str, Any],
    thread_id: str,
    include_logs: bool = False
) -> AsyncIterator[Dict[str, Any]]:
    """
    Stream execution with optional verbose logs.

    This supports the "Show Logs" toggle from the design doc.

    Args:
        graph: Compiled LangGraph application
        initial_state: Initial state for the workflow
        thread_id: Unique thread identifier
        include_logs: Whether to include verbose debug logs

    Yields:
        Event dictionaries
    """
    formatter = StreamEventFormatter()

    try:
        stream_modes = ["updates"]
        if include_logs:
            stream_modes.append("debug")

        async for chunk in graph.astream(
            initial_state,
            stream_mode=stream_modes,
            config={"configurable": {"thread_id": thread_id}}
        ):
            # Process based on stream mode
            if isinstance(chunk, tuple):
                stream_mode, data = chunk

                if stream_mode == "debug" and include_logs:
                    # Emit log event
                    yield formatter.format_node_event(
                        "system",
                        EventType.LOG,
                        {
                            "log_type": data.get("type", "unknown"),
                            "log_data": data
                        }
                    )

            elif isinstance(chunk, dict):
                # Regular updates
                for node_name, node_output in chunk.items():
                    if node_name != "__start__" and node_name != "__end__":
                        yield formatter.format_node_event(
                            node_name,
                            EventType.AGENT_COMPLETE,
                            {
                                "progress": formatter.calculate_progress(node_name)
                            }
                        )

    except Exception as e:
        yield formatter.format_node_event(
            "system",
            EventType.ERROR,
            {"error": str(e)}
        )
        raise


def format_activity_feed_message(node_name: str, status: str) -> str:
    """
    Format user-friendly messages for the activity feed.

    Maps technical node names to human-readable descriptions
    matching the design doc's activity feed examples.
    """
    messages = {
        "clarifier": {
            "running": "🔍 Analyzing query for ambiguities and clarifications needed...",
            "completed": "✓ Query analyzed and clarified"
        },
        "decomposer": {
            "running": "📊 Breaking down complex query into manageable sub-questions...",
            "completed": "✓ Query decomposed into sub-questions"
        },
        "strategist": {
            "running": "🎯 Planning optimal research strategy and approach...",
            "completed": "✓ Research strategy planned"
        },
        "researcher_hub": {
            "running": "🔬 Conducting parallel research across multiple sources...",
            "completed": "✓ Research completed for all sub-questions"
        },
        "fact_checker": {
            "running": "✅ Verifying facts and checking for contradictions...",
            "completed": "✓ Facts verified and validated"
        },
        "synthesizer": {
            "running": "📝 Synthesizing findings into comprehensive report...",
            "completed": "✓ Report synthesized"
        },
        "reviewer": {
            "running": "👁️ Performing final quality checks and validation...",
            "completed": "✓ Quality review completed"
        }
    }

    return messages.get(node_name, {}).get(
        status,
        f"{status.capitalize()} {node_name}"
    )
