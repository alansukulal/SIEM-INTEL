from app.agent.nodes.kql_generator import _extract_requested_table

tests = [
    "Check if we have recent logs in signinlogs",
    "Check table SigninLogs",
    "Check events from SecurityEvent",
    "Check StorageBlobLogs_CL",
]

for alert in tests:
    print(alert, "=>", _extract_requested_table(alert))