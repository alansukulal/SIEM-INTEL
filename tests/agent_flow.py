from app.agent.graph import build_investigation_graph


graph = build_investigation_graph()

result = graph.invoke(
    {
        "alert": "Check whether Sentinel is receiving Signinlogs logs",
        "siem": "Microsoft Sentinel",
        "plan": "",
        "query":"",
        "evidence": [],
        "finding": "",
        "needs_more_investigation": False,
        "investigation_attempts":0,
        "kql_valid": False,
        "kql_validation_errors": [],
        "kql_attempts":0,
        "kql_reason":"",
        "knowledge":[],
    }
)

print("\nPLAN:")
print(result["plan"])

print("\nEVIDENCE:")
for item in result["evidence"]:
    print("-", item)

print("\nFINDING:")
print(result["finding"])
print("\nKnowledge:")
print(result["knowledge"])