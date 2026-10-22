from typing import TypeVar

from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.config import settings


T = TypeVar("T", bound=BaseModel)


class LLMClient:
    def __init__(self) -> None:
        self.model = ChatOpenAI(
            model="gpt-5.6",
            temperature=0,
            api_key=settings.openai_api_key,
        )

    def invoke(self, prompt: str):
        return self.model.invoke(prompt)

    def invoke_structured(
        self,
        prompt: str,
        schema: type[T],
    ) -> T:
        structured_model = self.model.with_structured_output(schema)
        return structured_model.invoke(prompt)