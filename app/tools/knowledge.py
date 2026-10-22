from rank_bm25 import BM25Okapi

KNOWLEDGE_BASE = [
    {
        "name": "SigninLogs",
        "description": "Microsoft Entra ID sign-in and authentication events.",
        "columns": [
            "TimeGenerated",
            "UserPrincipalName",
            "ResultType",
            "IPAddress",
            "Location",
            "AppDisplayName",
        ],
    },
    {
        "name": "Heartbeat",
        "description": "Heartbeat information from agents connected to Microsoft Sentinel.",
        "columns": [
            "TimeGenerated",
            "Computer",
            "Category",
            "Version",
        ],
    },
    {
        "name": "SecurityEvent",
        "description": "Windows security events collected from Windows machines.",
        "columns": [
            "TimeGenerated",
            "Computer",
            "Account",
            "EventID",
            "Activity",
            "IpAddress",
        ],
    },
    {
        "name": "DeviceProcessEvents",
        "description": "Microsoft Defender process creation and execution events.",
        "columns": [
            "Timestamp",
            "DeviceName",
            "AccountName",
            "FileName",
            "ProcessCommandLine",
            "InitiatingProcessFileName",
        ],
    },
    {
        "name": "DeviceNetworkEvents",
        "description": "Microsoft Defender network connection events from devices.",
        "columns": [
            "Timestamp",
            "DeviceName",
            "RemoteIP",
            "RemotePort",
            "RemoteUrl",
            "InitiatingProcessFileName",
        ],
    },
    {
        "name": "AzureActivity",
        "description": "Azure resource management and administrative activity events.",
        "columns": [
            "TimeGenerated",
            "Caller",
            "OperationNameValue",
            "ActivityStatusValue",
            "ResourceGroup",
            "ResourceId",
        ],
    },
]


from rank_bm25 import BM25Okapi





def _document_text(document: dict) -> str:
    return " ".join(
        [
            document["name"],
            document["description"],
            *document["columns"],
        ]
    )


DOCUMENTS = [
    _document_text(document)
    for document in KNOWLEDGE_BASE
]


TOKENIZED_DOCUMENTS = [
    document.lower().split()
    for document in DOCUMENTS
]


BM25_INDEX = BM25Okapi(TOKENIZED_DOCUMENTS)


def search_knowledge(
    query: str,
    top_k: int = 3,
) -> list[dict]:

    query_tokens = query.lower().split()

    scores = BM25_INDEX.get_scores(query_tokens)

    ranked_indexes = sorted(
        range(len(scores)),
        key=lambda index: scores[index],
        reverse=True,
    )

    return [
        KNOWLEDGE_BASE[index]
        for index in ranked_indexes[:top_k]
    ]