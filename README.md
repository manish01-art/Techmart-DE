# TechMart Data Engineering Pipeline

End-to-end Data Engineering project built using ERPNext as the operational source system.

## Architecture

ERPNext
→ REST API
→ Python Ingestion
→ Amazon S3 Bronze
→ PySpark Silver
→ dbt
→ Amazon Redshift
→ Power BI

Airflow will be used for pipeline orchestration.

## Current Stage

- ERPNext configured as source system
- ERPNext REST API authentication implemented
- Python API client created
- Item extraction pipeline implemented
- Git version control initialized

## Planned Engineering Features

- Automated source data generation
- Incremental ingestion
- Pagination
- Retry and error handling
- Batch tracking
- Data quality checks
- S3 Bronze layer
- PySpark transformations
- SCD Type 2
- Dimensional data warehouse
- dbt transformations and testing
- Redshift
- Airflow orchestration
- CI/CD
- Monitoring and logging

## Project Structure

```text
src/
├── config.py
├── erpnext_client.py
└── extract_items.py

data/
└── raw/