"""
MLOps Batch Processing Pipeline

Processes cryptocurrency OHLCV data to compute rolling mean on close prices,
generates trading signals, and outputs structured metrics.
"""

import argparse
import json
import logging
import os
import sys
import time

import numpy as np
import pandas as pd
import yaml


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="MetaStackerBandit: crypto signal generation pipeline"
    )
    parser.add_argument(
        "--input", required=True, help="Path to input CSV data file"
    )
    parser.add_argument(
        "--config", required=True, help="Path to YAML configuration file"
    )
    parser.add_argument(
        "--output", required=True, help="Path to output metrics JSON file"
    )
    parser.add_argument(
        "--log-file", required=True, help="Path to log output file"
    )
    return parser.parse_args()


def setup_logging(log_file_path):
    """Configure logging to write to the specified file."""
    logger = logging.getLogger("metastackerbandit")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    file_handler = logging.FileHandler(log_file_path, mode="w")
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    return logger


def load_config(config_path, logger):
    """Load and validate YAML configuration file."""
    if not os.path.isfile(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    if config is None:
        raise ValueError("Configuration file is empty or invalid")

    required_keys = ["seed", "window", "version"]
    missing = [k for k in required_keys if k not in config]
    if missing:
        raise KeyError(f"Missing required configuration keys: {missing}")

    logger.info(
        "Config loaded: seed=%d, window=%d, version=%s",
        config["seed"], config["window"], config["version"]
    )
    return config


def load_data(input_path, logger):
    """Load and validate the input CSV data file."""
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    try:
        df = pd.read_csv(input_path)
    except pd.errors.ParserError as e:
        raise ValueError(f"Invalid CSV file format: {e}")

    if df.empty:
        raise ValueError("Input CSV file is empty")

    if "close" not in df.columns:
        raise KeyError("Required column 'close' not found in input data")

    logger.info("Data loaded: %d rows", len(df))
    return df


def compute_rolling_mean(df, window, logger):
    """Compute rolling mean on the close column."""
    df["rolling_mean"] = df["close"].rolling(window=window).mean()
    logger.info("Rolling mean calculated with window=%d", window)
    return df


def generate_signals(df, logger):
    """Generate trading signals based on close vs rolling mean comparison.

    Signal = 1 if close > rolling_mean, Signal = 0 otherwise.
    Rows with insufficient data for rolling mean get Signal = 0.
    """
    df["signal"] = 0
    valid_mask = df["rolling_mean"].notna()
    df.loc[valid_mask, "signal"] = (
        df.loc[valid_mask, "close"] > df.loc[valid_mask, "rolling_mean"]
    ).astype(int)

    logger.info("Signals generated")
    return df


def calculate_metrics(df, config, start_time, logger):
    """Calculate and return pipeline metrics."""
    rows_processed = len(df)
    signal_rate = round(float(df["signal"].mean()), 4)
    latency_ms = int((time.time() - start_time) * 1000)

    logger.info(
        "Metrics: signal_rate=%.4f, rows_processed=%d",
        signal_rate, rows_processed
    )

    metrics = {
        "version": config["version"],
        "rows_processed": rows_processed,
        "metric": "signal_rate",
        "value": signal_rate,
        "latency_ms": latency_ms,
        "seed": config["seed"],
        "status": "success"
    }
    return metrics


def write_output(metrics, output_path, logger):
    """Write metrics dictionary to JSON file."""
    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info("Metrics written to %s", output_path)


def write_error_output(output_path, error_message, version="v1"):
    """Write error-format output JSON when pipeline fails."""
    error_metrics = {
        "version": version,
        "status": "error",
        "error_message": str(error_message)
    }
    with open(output_path, "w") as f:
        json.dump(error_metrics, f, indent=2)


def main():
    """Main pipeline execution."""
    start_time = time.time()
    args = parse_arguments()

    # Setup logging
    logger = setup_logging(args.log_file)
    logger.info("Job started")

    version = "v1"

    try:
        # Step 1: Load configuration
        config = load_config(args.config, logger)
        version = config["version"]
        np.random.seed(config["seed"])

        # Step 2: Ingest data
        df = load_data(args.input, logger)

        # Step 3: Rolling mean computation
        df = compute_rolling_mean(df, config["window"], logger)

        # Step 4: Signal generation
        df = generate_signals(df, logger)

        # Step 5: Metrics calculation
        metrics = calculate_metrics(df, config, start_time, logger)

        # Write output
        write_output(metrics, args.output, logger)

        # Print metrics to stdout
        print(json.dumps(metrics, indent=2))

        latency_ms = int((time.time() - start_time) * 1000)
        logger.info("Job completed successfully in %dms", latency_ms)

    except FileNotFoundError as e:
        logger.error("File error: %s", str(e))
        write_error_output(args.output, str(e), version)
        sys.exit(1)

    except KeyError as e:
        msg = str(e).strip("'\"")
        logger.error("Key error: %s", msg)
        write_error_output(args.output, msg, version)
        sys.exit(1)

    except ValueError as e:
        logger.error("Validation error: %s", str(e))
        write_error_output(args.output, str(e), version)
        sys.exit(1)

    except Exception as e:
        logger.error("Unexpected error: %s", str(e))
        write_error_output(args.output, str(e), version)
        sys.exit(1)


if __name__ == "__main__":
    main()
