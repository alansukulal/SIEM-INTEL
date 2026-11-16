
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage
)


def convert_to_langchain_messages(history):

    messages = []

    for message in history:

        role = message["role"]
        content = message["content"]

        if role == "user":
            messages.append(HumanMessage(content=content))

        elif role == "assistant":
            messages.append(AIMessage(content=content))

        elif role == "system":
            messages.append(SystemMessage(content=content))

    return messages
