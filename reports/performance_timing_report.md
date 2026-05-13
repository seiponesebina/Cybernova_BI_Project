# CyberNova Dashboard Performance Timing Report

Dataset: `data\output\cybernova_enriched_logs.csv`
Rows measured: `60,551`
Columns measured: `133`
Timing runs per operation: `3`

## Summary

| Operation | Before caching avg | After caching avg | Improvement |
|---|---:|---:|---:|
| Dataset loading | 3.5869s | 0.0677s | 98.1% |
| Data transformation | 0.4850s | 0.1411s | 70.9% |
| Chart preparation | 0.4251s | 0.0864s | 79.7% |
| Filter response | 0.1360s | 0.0418s | 69.3% |

## Notes

- Before caching measures repeated CSV/dataframe work.
- After caching measures cached parquet/dataframe/filter/chart results in the same Python process.
- Filter scenario: Botswana, Cybersecurity, Engaged, HTTP 200.
- Filtered rows returned after caching: `2,007`

## Detailed Timings

| Operation | Before best | Before worst | After best | After worst |
|---|---:|---:|---:|---:|
| Dataset loading | 3.4946s | 3.6978s | 0.0000s | 0.2032s |
| Data transformation | 0.4707s | 0.5069s | 0.0000s | 0.4232s |
| Chart preparation | 0.2668s | 0.6980s | 0.0000s | 0.2591s |
| Filter response | 0.1256s | 0.1497s | 0.0000s | 0.1253s |
