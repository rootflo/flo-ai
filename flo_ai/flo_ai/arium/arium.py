from flo_ai.arium.base import BaseArium
from flo_ai.arium.memory import MessageMemory, BaseMemory
from flo_ai.llm.base_llm import ImageMessage
from flo_ai.models.document import DocumentMessage
from typing import List, Dict, Any, Optional, Callable
from flo_ai.models.agent import Agent
from flo_ai.tool.base_tool import Tool
from flo_ai.arium.models import StartNode, EndNode
from flo_ai.arium.events import AriumEventType, AriumEvent
from flo_ai.utils.logger import logger
from flo_ai.utils.variable_extractor import (
    extract_variables_from_inputs,
    extract_agent_variables,
    validate_multi_agent_variables,
    resolve_variables,
)
import asyncio
import time


class Arium(BaseArium):
    def __init__(self, memory: BaseMemory):
        super().__init__()
        self.is_compiled = False
        self.memory = memory if memory else MessageMemory()

    def compile(self):
        self.validate_graph()
        self.is_compiled = True

    async def run(
        self,
        inputs: List[str | ImageMessage | DocumentMessage],
        variables: Optional[Dict[str, Any]] = None,
        event_callback: Optional[Callable[[AriumEvent], None]] = None,
        events_filter: Optional[List[AriumEventType]] = None,
    ):
        """
        Execute the Arium workflow with optional event monitoring.

        Args:
            inputs: Input messages for the workflow
            variables: Variable substitutions for templated prompts
            event_callback: Function to call for each event (if None, no events are emitted)
            events_filter: List of event types to listen for (defaults to all)

        Returns:
            List of workflow execution results
        """
        if not self.is_compiled:
            raise ValueError('Arium is not compiled')

        if not self.memory:
            raise ValueError('Arium has no memory')

        if not self.nodes:
            raise ValueError('Arium has no nodes')

        # Set default event filters to all event types if not specified
        if events_filter is None:
            events_filter = list(AriumEventType)

        # Emit workflow started event
        self._emit_event(AriumEventType.WORKFLOW_STARTED, event_callback, events_filter)

        try:
            # Extract and validate variables from inputs and all agents
            self._extract_and_validate_variables(inputs, variables)

            # Resolve variables in inputs and agent prompts
            resolved_inputs = self._resolve_inputs(inputs, variables)
            self._resolve_agent_prompts(variables)

            # Execute the workflow with event support
            result = await self._execute_graph(
                resolved_inputs, event_callback, events_filter
            )

            # Emit workflow completed event
            self._emit_event(
                AriumEventType.WORKFLOW_COMPLETED, event_callback, events_filter
            )

            return result

        except Exception as e:
            # Emit workflow failed event
            self._emit_event(
                AriumEventType.WORKFLOW_FAILED,
                event_callback,
                events_filter,
                error=str(e),
            )
            raise

    def _emit_event(
        self,
        event_type: AriumEventType,
        callback: Optional[Callable[[AriumEvent], None]],
        events_filter: Optional[List[AriumEventType]],
        **kwargs,
    ) -> None:
        """
        Emit an event if callback is provided and event type is in filtered list.

        Args:
            event_type: The type of event to emit
            callback: Function to call with the event (if None, no event is emitted)
            events_filter: List of event types to listen for
            **kwargs: Additional event data (node_name, error, etc.)
        """
        if callback and event_type in events_filter:
            event = AriumEvent(event_type=event_type, timestamp=time.time(), **kwargs)
            callback(event)

    async def _execute_graph(
        self,
        inputs: List[str | ImageMessage | DocumentMessage],
        event_callback: Optional[Callable[[AriumEvent], None]] = None,
        events_filter: Optional[List[AriumEventType]] = None,
    ):
        [self.memory.add(msg) for msg in inputs]

        current_node = self.nodes[self.start_node_name]
        current_edge = self.edges[self.start_node_name]

        # Loop prevention: track execution steps and node visits
        max_iterations = 20  # Reasonable limit to prevent infinite loops
        iteration_count = 0
        node_visit_count = {}  # Track how many times each node is visited
        execution_path = []  # Track the path for debugging

        logger.info(f'Executing graph from {current_node.name}')
        while current_node.name not in self.end_node_names:
            # Check for iteration limit
            iteration_count += 1
            if iteration_count > max_iterations:
                logger.error(
                    f"Maximum iterations ({max_iterations}) exceeded. Execution path: {' -> '.join(execution_path)}"
                )
                raise RuntimeError(
                    f'Workflow exceeded maximum iterations ({max_iterations}). Possible infinite loop detected.'
                )

            # Track node visits
            node_visit_count[current_node.name] = (
                node_visit_count.get(current_node.name, 0) + 1
            )
            execution_path.append(current_node.name)

            # Check for excessive node visits (same node visited too many times)
            if node_visit_count[current_node.name] > 3:
                logger.error(
                    f"Node '{current_node.name}' visited {node_visit_count[current_node.name]} times. Execution path: {' -> '.join(execution_path)}"
                )
                raise RuntimeError(
                    f"Node '{current_node.name}' visited too many times ({node_visit_count[current_node.name]}). Possible infinite loop detected."
                )

            logger.info(
                f'Executing node: {current_node.name} (iteration {iteration_count})'
            )
            # execute current node
            result = await self._execute_node(
                current_node, event_callback, events_filter
            )

            # update results to memory
            self._add_to_memory(result)

            # find next node post current node
            # Prepare execution context for router functions
            execution_context = {
                'node_visit_count': node_visit_count,
                'execution_path': execution_path,
                'iteration_count': iteration_count,
                'current_node': current_node.name,
            }

            # Handle both sync and async router functions
            # Try to call with execution context, fallback to memory only
            try:
                router_result = current_edge.router_fn(
                    memory=self.memory, execution_context=execution_context
                )
            except TypeError:
                # Router function doesn't accept execution_context parameter
                router_result = current_edge.router_fn(memory=self.memory)

            if asyncio.iscoroutine(router_result):
                next_node_name = await router_result
            else:
                next_node_name = router_result

            # Emit router decision event
            self._emit_event(
                AriumEventType.ROUTER_DECISION,
                event_callback,
                events_filter,
                node_name=current_node.name,
                router_choice=next_node_name,
            )

            # Emit edge traversed event
            self._emit_event(
                AriumEventType.EDGE_TRAVERSED,
                event_callback,
                events_filter,
                node_name=current_node.name,
            )

            # find next edge
            # TODO: next_node_name might not be in self.edges if it's the end node. Handle this case
            next_edge = (
                self.edges[next_node_name] if next_node_name in self.edges else None
            )

            # update current node
            current_node = self.nodes[next_node_name]
            current_edge = next_edge

        return self.memory.get()

    def _extract_and_validate_variables(
        self,
        inputs: List[str | ImageMessage | DocumentMessage],
        variables: Dict[str, Any],
    ) -> None:
        """Extract variables from inputs and agents, then validate them.

        Args:
            inputs: List of input messages
            variables: Dictionary of variable name to value mappings

        Raises:
            ValueError: If any required variables are missing
        """
        # Extract variables from inputs
        input_variables = extract_variables_from_inputs(inputs)

        # Extract variables from all agents in the workflow
        agents_variables = {}
        for node in self.nodes.values():
            if isinstance(node, Agent):
                agent_vars = extract_agent_variables(node)
                if agent_vars:
                    agents_variables[node.name] = agent_vars

        # Validate input variables separately with cleaner error message
        if input_variables:
            missing_input_vars = input_variables - set(variables.keys())
            if missing_input_vars:
                provided_keys = sorted(variables.keys())
                raise ValueError(
                    f'Input contains missing variables: {sorted(missing_input_vars)}. '
                    f'Provided variables: {provided_keys}'
                )

        # Validate agent variables with detailed agent breakdown
        if agents_variables:
            validate_multi_agent_variables(agents_variables, variables)

    def _resolve_inputs(
        self,
        inputs: List[str | ImageMessage | DocumentMessage],
        variables: Dict[str, Any],
    ) -> List[str | ImageMessage | DocumentMessage]:
        """Resolve variables in input messages.

        Args:
            inputs: List of input messages
            variables: Dictionary of variable name to value mappings

        Returns:
            List of inputs with variables resolved
        """
        resolved_inputs = []
        for input_item in inputs:
            if isinstance(input_item, str):
                # Resolve variables in text input
                resolved_input = resolve_variables(input_item, variables)
                resolved_inputs.append(resolved_input)
            else:
                # ImageMessage and DocumentMessage objects don't need variable resolution
                resolved_inputs.append(input_item)
        return resolved_inputs

    def _resolve_agent_prompts(self, variables: Dict[str, Any]) -> None:
        """Resolve variables in all agent system prompts and mark them as resolved.

        Args:
            variables: Dictionary of variable name to value mappings
        """
        for node in self.nodes.values():
            if isinstance(node, Agent):
                node.system_prompt = resolve_variables(node.system_prompt, variables)
                node.resolved_variables = True

    async def _execute_node(
        self,
        node: Agent | Tool | StartNode | EndNode,
        event_callback: Optional[Callable[[AriumEvent], None]] = None,
        events_filter: Optional[List[AriumEventType]] = None,
    ):
        """
        Execute a single node with optional event emission.

        Args:
            node: The node to execute
            event_callback: Function to call for events (if None, no events are emitted)
            events_filter: List of event types to listen for

        Returns:
            The result of node execution
        """
        # Determine node type for events
        if isinstance(node, Agent):
            node_type = 'agent'
        elif isinstance(node, Tool):
            node_type = 'tool'
        elif isinstance(node, StartNode):
            node_type = 'start'
        elif isinstance(node, EndNode):
            node_type = 'end'
        else:
            node_type = 'unknown'

        # Emit node started event
        self._emit_event(
            AriumEventType.NODE_STARTED,
            event_callback,
            events_filter,
            node_name=node.name,
            node_type=node_type,
        )

        start_time = time.time()

        try:
            # Execute the node based on its type
            if isinstance(node, Agent):
                # Variables are already resolved, pass empty dict to avoid re-processing
                result = await node.run(self.memory.get(), variables={})
            elif isinstance(node, Tool):
                result = await node.execute()
            elif isinstance(node, StartNode):
                result = None
            elif isinstance(node, EndNode):
                result = None
            else:
                result = None

            # Calculate execution time
            execution_time = time.time() - start_time

            # Emit node completed event
            self._emit_event(
                AriumEventType.NODE_COMPLETED,
                event_callback,
                events_filter,
                node_name=node.name,
                node_type=node_type,
                execution_time=execution_time,
            )

            return result

        except Exception as e:
            # Calculate execution time even on failure
            execution_time = time.time() - start_time

            # Emit node failed event
            self._emit_event(
                AriumEventType.NODE_FAILED,
                event_callback,
                events_filter,
                node_name=node.name,
                node_type=node_type,
                execution_time=execution_time,
                error=str(e),
            )

            # Re-raise the exception
            raise

    def _add_to_memory(self, result: str):
        # TODO result will be None for start and end nodes
        if result:
            self.memory.add(result)
