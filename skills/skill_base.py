from abc import ABC, abstractmethod

class BaseSkill(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def get_specification(self) -> dict:
        """Returns the specification for Function Calling (Gemini/Groq format)."""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Execute the skill with provided arguments and return a string result."""
        pass

    def set_context(self, context):
        """Set the execution context (e.g., ReminderManager)."""
        self.context = context
