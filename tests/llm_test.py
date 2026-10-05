from app.llm.client import LLMClient

llm=LLMClient()

response=llm.invoke("Tell me a word on sentinel")
print(response.content)