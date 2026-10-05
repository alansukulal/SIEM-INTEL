from app.agent.graph import build_investigation_graph


graph = build_investigation_graph()

result = graph.invoke(
    {
        "alert": "Check whether Sentinel is receiving heartbeat logs",
        "siem": "Microsoft Sentinel",
        "plan": "",
        "query":"",
        "evidence": [],
        "finding": "",
    }
)

print("\nPLAN:")
print(result["plan"])

print("\nEVIDENCE:")
for item in result["evidence"]:
    print("-", item)

print("\nFINDING:")
print(result["finding"])