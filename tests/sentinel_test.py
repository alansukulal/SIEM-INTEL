from app.tools.sentinel import SentinelClient


sentinel = SentinelClient()

response = sentinel.run_query(
    """
    Heartbeat
    | take 10
    """
)

print(response)