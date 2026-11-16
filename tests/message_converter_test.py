
from app.services.conversation_service import get_conversation_history
from app.services.message_converter import convert_to_langchain_messages

tenant_id = "ac1fabf0-6a93-48ff-85d9-3862a8c2feca"
investigation_id = "46200beb-7bb8-4a5a-aee0-a60b88fd1990"

# Retrieve messages from PostgreSQL
history = get_conversation_history(
    tenant_id,
    investigation_id
)

# Convert to LangChain objects
messages = convert_to_langchain_messages(history)

# Inspect the result
for message in messages:
    print("Type:", type(message).__name__)
    print("Content:", message.content)
    print("--------------------")
