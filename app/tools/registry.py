
from typing import Any, Callable

from app.models.tool_definition import ToolDefinition


class ToolRegistry:
    """Central registry for all capabilities available to SIEM-INTEL."""

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}
        self._functions: dict[str, Callable[..., Any]] = {}

    def register(
        self,
        definition: ToolDefinition,
        function: Callable[..., Any] | None = None,
    ) -> None:
        name = definition.name

        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered.")

        if definition.execution_type == "direct" and function is None:
            raise ValueError(
                f"Direct tool '{name}' must have an implementation."
            )

        self._tools[name] = definition

        if function is not None:
            self._functions[name] = function

    def get_definition(self, name: str) -> ToolDefinition:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered.")

        return self._tools[name]

    def get_function(self, name: str) -> Callable[..., Any]:
        if name not in self._functions:
            raise KeyError(
                f"No direct implementation registered for '{name}'."
            )

        return self._functions[name]

    def list_definitions(self) -> list[ToolDefinition]:
        return [
            definition
            for definition in self._tools.values()
            if definition.enabled
        ]

    def list_tools(self) -> list[str]:
        return [
            definition.name
            for definition in self.list_definitions()
        ]

    def execute(
        self,
        name: str,
        arguments: dict[str, Any],
    ) -> Any:
        definition = self.get_definition(name)

        if not definition.enabled:
            raise PermissionError(f"Tool '{name}' is disabled.")

        if definition.execution_type != "direct":
            raise ValueError(
                f"Tool '{name}' must be executed through LangGraph."
            )

        if definition.requires_approval:
            raise PermissionError(
                f"Tool '{name}' requires approval before execution."
            )

        function = self.get_function(name)
        return function(**arguments)
