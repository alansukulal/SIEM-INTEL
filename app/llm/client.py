from langchain_openai import ChatOpenAI

from app.config import settings


class LLMClient:
    def __init__(self) -> None:
        self.model = ChatOpenAI(
            model="gpt-5.6",
            temperature=0,
            api_key=settings.openai_api_key,
        )

    def invoke(self, prompt: str):
        return self.model.invoke(prompt)