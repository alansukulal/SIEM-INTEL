# Runbook: Log Outage Checks

## 1. Purpose

To identify whether logs from configured tables or specific hosts have stopped arriving in Microsoft Sentinel / Log Analytics, determine the last recorded log timestamp, and initiate troubleshooting.

## 2. Table-Level Log Outage Check

**Objective:** Check the latest log timestamp for each `Type` in a table over the last 24 hours.

### KQL Query

```kql
<TableName>
| where TimeGenerated > ago(1d)
| summarize LastLogTime = max(TimeGenerated) by Type
| order by LastLogTime asc
```

### Procedure

1. Replace `<TableName>` with the table you want to investigate.
2. Run the query in the relevant Log Analytics workspace.
3. Review `LastLogTime` for each `Type` returned.
4. Compare the latest timestamps against the expected log arrival frequency.
5. If a type is missing from the results, check whether it has produced logs outside the 24-hour window or whether ingestion has stopped.

**Expected Result:** Each returned `Type` shows its most recent event timestamp within the last 24 hours.

## 3. Host-Level Log Outage Check

**Objective:** Verify whether a specific host is sending logs to a table.

### KQL Query

```kql
<TableName>
| where TimeGenerated > ago(1d)
| where Computer in ("ComputerName")
| summarize LastLogTime = max(TimeGenerated) by Type, Computer
| order by LastLogTime asc
```

### Procedure

1. Replace `<TableName>` with the relevant table name.
2. Replace `"ComputerName"` with the actual host name.
3. Execute the query in the correct workspace.
4. Review `LastLogTime` for each `Type` and `Computer`.
5. Compare the results against the expected log arrival frequency for that host.
6. If no results appear, verify the host name and investigate whether the host is sending logs.

### Query for Multiple Hosts

```kql
<TableName>
| where TimeGenerated > ago(1d)
| where Computer in ("Host01", "Host02", "Host03")
| summarize LastLogTime = max(TimeGenerated) by Type, Computer
| order by LastLogTime asc
```

## 4. Outage Investigation Workflow

### Step 1: Run the KQL Query

Check the relevant table or host for logs received during the last 24 hours.

### Step 2: Identify the Last Log Timestamp

Compare `LastLogTime` against the expected ingestion frequency and the time the issue was reported.

### Step 3: Determine the Scope

- **One host affected:** Investigate the host, agent, or local connectivity.
- **One table or source affected:** Investigate the connector, API, token, or source configuration.
- **Multiple tables affected:** Investigate workspace ingestion, shared infrastructure, authentication, or upstream outages.

### Step 4: Troubleshoot the Ingestion Path

Verify the following, as applicable:

- Source availability and health.
- Connector status and configuration.
- Authentication failures or token expiry.
- Agent status and connectivity.
- Network connectivity.
- Ingestion errors or delays.
- Any recent configuration changes.

### Step 5: Confirm Recovery

1. Rerun the relevant KQL query.
2. Verify that new logs are arriving.
3. Record the recovery timestamp.
4. Document the findings and root cause.
5. Update or escalate the incident as required.

## 5. Check Ingestion Time

If events have old `TimeGenerated` values, they might still have arrived recently. Where ingestion-time tracking is available, run:

```kql
<TableName>
| where TimeGenerated > ago(1d)
| extend IngestionTime = ingestion_time()
| summarize LastEventTime = max(TimeGenerated),
            LastIngestionTime = max(IngestionTime)
    by Type
```

- `TimeGenerated`: The event timestamp.
- `ingestion_time()`: Estimates when the record was ingested into the workspace.

**Note:** `ingestion_time()` can return null and should not be treated as an exact ordering mechanism.

## 6. Outage Assessment and Escalation

| Observation | Recommended Action |
|---|---|
| Recent logs are present | Confirm that the arrival frequency is normal. |
| Latest logs are older than expected | Investigate a potential ingestion delay or outage. |
| No results in the last 24 hours | Check a longer time range and verify source/table configuration. |
| Host-specific logs are missing | Verify host connectivity, agent health, and hostname. |
| Multiple sources stopped together | Investigate shared dependencies and platform health. |
| Authentication or token errors | Validate credential status and coordinate renewal with the integration owner. |

**Important:** A missing result from the 24-hour query does not, by itself, prove an outage. The source may be inactive, the event timestamp may be delayed, or the host/table may be incorrectly specified. Use the expected log frequency and the last known successful arrival to determine severity.

## 7. Outage Tracking Template

Record the following details for each investigation:

- **Workspace:**
- **Table / Data Source:**
- **Affected Host(s):**
- **Last Event Timestamp:**
- **Last Ingestion Timestamp (if available):**
- **Expected Log Frequency:**
- **Outage Start / Last Known Good Time:**
- **Investigation Findings:**
- **Root Cause:**
- **Resolution / Recovery Time:**
- **Ticket / Escalation Reference:**

---

**End of Runbook**