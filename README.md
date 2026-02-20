# MLOps Engineering Internship: Technical Assessment

Multi-agent reinforcement learning trading system using real-time crypto data, rolling statistics, signal generation, and Docker deployment.

## Overview

This project implements a miniature MLOps-style pipeline that:

1. Reads cryptocurrency OHLCV data from a CSV file
2. Computes a rolling mean on the `close` column
3. Generates trading signals (buy/hold) based on price vs rolling mean
4. Outputs structured metrics as JSON
5. Logs the complete execution process
6. Runs as a containerized batch job via Docker

## Project Structure

```
assign0/
├── run.py              # Main pipeline script
├── config.yaml         # Configuration file
├── data.csv            # 10,000-row crypto OHLCV dataset
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container definition
├── .dockerignore       # Docker ignore rules
├── metrics.json        # Example output (from a successful run)
├── run.log             # Example log file (from a successful run)
└── README.md           # This file
```

## Setup Instructions

```bash
# Install dependencies
pip install -r requirements.txt
```

## Local Execution Instructions

```bash
# Run locally
python run.py --input data.csv --config config.yaml --output metrics.json --log-file run.log
```

### Command-Line Arguments

| Argument     | Required | Description                      |
|-------------|----------|----------------------------------|
| `--input`    | Yes      | Path to input CSV data file      |
| `--config`   | Yes      | Path to YAML configuration file  |
| `--output`   | Yes      | Path to output metrics JSON file |
| `--log-file` | Yes      | Path to log output file          |

## Docker Instructions

```bash
# Build the Docker image
docker build -t mlops-task .

# Run the container
docker run --rm mlops-task
```

## Configuration

The pipeline reads from `config.yaml`:

```yaml
seed: 42
window: 5
version: "v1"
```

| Field    | Type    | Description                    |
|---------|---------|--------------------------------|
| `seed`   | integer | Random seed for reproducibility |
| `window` | integer | Rolling mean window size        |
| `version`| string  | Version tag in output metrics   |

## Expected Output

### `metrics.json` (Success)

```json
{
  "version": "v1",
  "rows_processed": 10000,
  "metric": "signal_rate",
  "value": 0.4978,
  "latency_ms": 127,
  "seed": 42,
  "status": "success"
}
```

| Field             | Type    | Description                           |
|------------------|---------|---------------------------------------|
| `version`         | string  | Value extracted from config.yaml      |
| `rows_processed`  | integer | Total row count of the input dataset  |
| `metric`          | string  | Must always be "signal_rate"          |
| `value`           | float   | The computed signal rate (range: 0-1) |
| `latency_ms`      | integer | Total execution time in milliseconds  |
| `seed`            | integer | Value extracted from config.yaml      |
| `status`          | string  | "success" or "error"                  |

### `metrics.json` (Error)

```json
{
  "version": "v1",
  "status": "error",
  "error_message": "Description of what went wrong"
}
```

## Dependencies

```
numpy==1.26.4
pandas==2.2.1
PyYAML==6.0.1
```

## Error Handling

The pipeline gracefully handles:

- Missing input file
- Invalid CSV file format
- Empty input file
- Missing required columns in the dataset
- Invalid configuration file structure

All errors produce a structured JSON error output and non-zero exit code.

## Logging

Logs are written to the file specified by `--log-file`. The log includes:

1. **Job Start**: Timestamp and configuration loaded
2. **Configuration Verification**: Confirmation of seed, window, and version values
3. **Data Ingestion**: Number of rows loaded
4. **Processing Steps**: Rolling mean calculation, signal generation
5. **Metrics Summary**: Final signal_rate and rows_processed
6. **Job Completion**: Timestamp and final status
7. **Error Reporting**: Any validation errors or exceptions

Example log format:

```
2024-01-06 16:00:00 - INFO - Job started
2024-01-06 16:00:00 - INFO - Config loaded: seed=42, window=5, version=v1
2024-01-06 16:00:00 - INFO - Data loaded: 10000 rows
2024-01-06 16:00:01 - INFO - Rolling mean calculated with window=5
2024-01-06 16:00:01 - INFO - Signals generated
2024-01-06 16:00:01 - INFO - Metrics: signal_rate=0.4990, rows_processed=10000
2024-01-06 16:00:01 - INFO - Job completed successfully in 127ms
```

## Dataset

The `data.csv` file contains 10,000 rows of cryptocurrency OHLCV data:

| Column       | Description                    | Usage                  |
|-------------|--------------------------------|------------------------|
| `timestamp`  | Date and time of each point    | Reference              |
| `open`       | Opening price (USD)            |                        |
| `high`       | Highest price in period (USD)  |                        |
| `low`        | Lowest price in period (USD)   |                        |
| `close`      | Closing price (USD)            | Required for calculations |
| `volume_btc` | Trading volume in BTC          |                        |
| `volume_usd` | Trading volume in USD          |                        |
