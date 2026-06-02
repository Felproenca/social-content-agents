"""Base class for all skills in the framework."""

from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel


class SkillInput(BaseModel):
    pass


class SkillOutput(BaseModel):
    success: bool = True
    error: str | None = None


class Skill(ABC):
    """
    Unit of reusable capability. Each skill has a single, well-defined function
    and can be composed into agents or called directly from workflows.
    """

    name: str
    description: str

    @abstractmethod
    async def run(self, input: SkillInput) -> SkillOutput:
        """Execute the skill with the given input."""
        ...

    def to_tool_definition(self) -> dict[str, Any]:
        """Return an Anthropic-compatible tool definition for this skill."""
        schema = self.input_schema()
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": schema,
        }

    def input_schema(self) -> dict[str, Any]:
        """Override to provide a JSON Schema for the skill's input."""
        return {"type": "object", "properties": {}, "required": []}
