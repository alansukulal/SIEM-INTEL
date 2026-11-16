from app.services.conversation_service import get_conversation_history

# Use the IDs of your existing investigation
tenant_id = "ac1fabf0-6a93-48ff-85d9-3862a8c2feca"
investigation_id = "46200beb-7bb8-4a5a-aee0-a60b88fd1990"

history = get_conversation_history(
    tenant_id,
    investigation_id
)

for message in history:
    print(f"{message['role']}: {message['content']}")