from typing import Dict, Any, Callable
from flo_ai.models.agent_error import AgentError
from flo_ai.utils.logger import logger


class ToolExecutionError(AgentError):
    """Error during tool execution"""

    pass


class Tool:
    def __init__(
        self,
        name: str,
        description: str,
        function: Callable,
        parameters: Dict[str, Dict[str, Any]],
    ):
        self.name = name
        self.description = description
        self.function = function

        # Ensure parameters have required field
        self.parameters = {}
        for param_name, param_info in parameters.items():
            self.parameters[param_name] = {
                **param_info,
                'required': param_info.get('required', True),
            }

    async def execute(self, **kwargs) -> Any:
        """Execute the tool with error handling"""
        try:
            logger.info(f'Executing tool {self.name} with kwargs: {kwargs}')
            tool_result = await self.function(**kwargs)
            logger.info(f'Tool {self.name} returned: {tool_result}')
            return tool_result
        except Exception as e:
            raise ToolExecutionError(
                f'Error executing tool {self.name}: {str(e)}', original_error=e
            )
