
# Ingestion Spike Investigation Runbook

## Purpose

Investigate an unusual increase in billed ingestion for a Microsoft Sentinel table, identify the main contributors, drill down into the suspicious activity, and produce an evidence-based finding.

## Inputs

- Table name
- Alert time or suspected spike period
- Investigation time range
- Comparison period representing normal ingestion
- Main schema field to investigate, selected after reviewing the table schema

The investigation period is configurable. Use 30 days as a starting example, not a fixed requirement. Select a suitable comparison period based on the alert and available historical data.

## Stage 1: Visualize and quantify the ingestion spike

Execute the following query after substituting the validated table name and appropriate time range.

```kusto
TableName
| where TimeGenerated > ago(30d)
| where _IsBillable == true
| summarize GB_of_data = round(sum(_BilledSize) / pow(1024, 3), 2)
    by bin(TimeGenerated, 1d), Type
| order by TimeGenerated asc
```

### Investigation actions

1. Review the daily billed-ingestion timechart.
2. Identify the date or interval with unusual ingestion.
3. Compare the suspected spike against normal days.
4. Adjust the time range and comparison period according to the alert.
5. Record the baseline volume, spike volume, absolute difference in GB, and percentage change when the baseline is nonzero.

### Expected output

- Affected table
- Suspected spike period
- Daily ingestion trend
- Normal baseline and observed spike
- Difference in billed GB
- Whether further investigation is warranted

### Important checks

- Confirm that the table supports the queried columns.
- `_IsBillable` and `_BilledSize` must be available for this analysis.
- This query measures billed ingestion; it is not necessarily equivalent to raw event count or EPS.
- If the table does not support these fields, report the limitation and select a suitable alternative metric.

## Stage 2: Identify the main contributor

Review the table schema and identify the most relevant field for explaining the increase.

Possible fields depend on the table and may include event type, operation, category, source, device, vendor, or another meaningful schema field.

Use the selected field in the following query:

```kusto
TableName
| where TimeGenerated > ago(30d)
| summarize EventCount = count()
    by bin(TimeGenerated, 1d), MainSchemaField
| order by TimeGenerated asc
```

Replace `MainSchemaField` with a real, documented column from the selected table.

### Investigation actions

1. Review the schema before choosing the field.
2. Examine the daily event-count trend by the selected field.
3. Identify contributors that increased during the spike.
4. Compare those contributors against normal days.
5. Select the most suspicious contributor or contributors for deeper investigation.

Event count is a diagnostic metric. It does not directly establish which contributor caused the billed-GB increase.

## Stage 3: Drill down into the suspected cause

Use the results from Stage 2 to determine the next investigation query.

Possible follow-up dimensions include:

- Specific event types or operations
- Source systems or devices
- Vendors or integration sources
- Relevant timestamps and activity patterns
- Error codes, status values, or other table-specific fields

Choose follow-up queries based on the actual table schema and evidence collected.

### Investigation actions

1. Narrow the query to the suspicious time period.
2. Filter or summarize by the suspected contributor.
3. Compare the contributor with its normal activity.
4. Collect relevant supporting records and aggregate results.
5. Check whether a configuration change, unusual activity, duplicate events, or an integration issue is supported by the evidence.
6. Continue only when another query can answer a specific outstanding question.

Do not assume a root cause from correlation alone. If evidence is insufficient, state what is known, what remains uncertain, and which additional evidence is needed.

## Stage 4: Produce the investigation report

Return the following:

- Alert and affected table
- Time range investigated
- Baseline and spike-period ingestion in GB
- Absolute and percentage change, where calculable
- Main contributing schema field and observed change
- Supporting evidence from follow-up queries
- Most likely explanation, with confidence and evidence limitations
- Recommended next steps
- Any unanswered questions

Clearly distinguish observed facts from hypotheses. Do not claim a root cause unless the collected evidence supports it.
