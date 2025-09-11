"""
Event system for Arium workflow execution monitoring.

This module provides event types and data structures for tracking workflow execution,
including node starts/completions, router decisions, and workflow lifecycle events.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional
import time


class AriumEventType(Enum):
    """Enumeration of all possible Arium workflow events."""

    WORKFLOW_STARTED = 'workflow_started'
    WORKFLOW_COMPLETED = 'workflow_completed'
    WORKFLOW_FAILED = 'workflow_failed'
    NODE_STARTED = 'node_started'
    NODE_COMPLETED = 'node_completed'
    NODE_FAILED = 'node_failed'
    ROUTER_DECISION = 'router_decision'
    EDGE_TRAVERSED = 'edge_traversed'


@dataclass
class AriumEvent:
    """
    Data structure representing a single workflow execution event.

    Attributes:
        event_type: The type of event that occurred
        timestamp: Unix timestamp when the event occurred
        node_name: Name of the node involved (if applicable)
        node_type: Type of node ('agent', 'tool', 'start', 'end')
        execution_time: Time taken for node execution in seconds
        error: Error message if the event represents a failure
        router_choice: The node chosen by a router decision
        metadata: Additional event-specific data
    """

    event_type: AriumEventType
    timestamp: float
    node_name: Optional[str] = None
    node_type: Optional[str] = None
    execution_time: Optional[float] = None
    error: Optional[str] = None
    router_choice: Optional[str] = None
    metadata: Optional[dict] = None


def default_event_callback(event: AriumEvent) -> None:
    """
    Default callback function that prints workflow events to console with formatting.

    This provides useful output for debugging and monitoring workflow execution
    without requiring any custom callback setup.

    Args:
        event: The AriumEvent to process and display
    """
    timestamp = time.strftime('%H:%M:%S', time.localtime(event.timestamp))

    if event.event_type == AriumEventType.WORKFLOW_STARTED:
        print(f'🚀 [{timestamp}] Workflow started')

    elif event.event_type == AriumEventType.WORKFLOW_COMPLETED:
        print(f'✅ [{timestamp}] Workflow completed')

    elif event.event_type == AriumEventType.WORKFLOW_FAILED:
        print(f'❌ [{timestamp}] Workflow failed: {event.error}')

    elif event.event_type == AriumEventType.NODE_STARTED:
        node_desc = (
            f'{event.node_type}: {event.node_name}'
            if event.node_type
            else event.node_name
        )
        print(f'⚡ [{timestamp}] Started {node_desc}')

    elif event.event_type == AriumEventType.NODE_COMPLETED:
        duration = f' ({event.execution_time:.2f}s)' if event.execution_time else ''
        print(f'✅ [{timestamp}] Completed {event.node_name}{duration}')

    elif event.event_type == AriumEventType.NODE_FAILED:
        print(f'❌ [{timestamp}] Failed {event.node_name}: {event.error}')

    elif event.event_type == AriumEventType.ROUTER_DECISION:
        print(f'🔀 [{timestamp}] Router chose: {event.router_choice}')

    elif event.event_type == AriumEventType.EDGE_TRAVERSED:
        print(f'➡️  [{timestamp}] Moving from {event.node_name} to next node')
