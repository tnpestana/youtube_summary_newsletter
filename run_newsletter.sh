#!/bin/bash

# YouTube Summary Newsletter Runner
# This script runs the newsletter application with proper environment setup

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the project directory
cd "$SCRIPT_DIR"

# Log file for cron job output
LOG_FILE="$SCRIPT_DIR/logs/newsletter_cron.log"

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

# Function to log with timestamp
log_with_timestamp() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" >> "$LOG_FILE"
}

# Start logging
log_with_timestamp "Starting YouTube Summary Newsletter job"

# Check if .env file exists
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    log_with_timestamp "ERROR: .env file not found in $SCRIPT_DIR"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        log_with_timestamp "ERROR: Python not found in PATH"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

log_with_timestamp "Using Python command: $PYTHON_CMD"

# Run the newsletter application via scheduler (handles missed executions)
log_with_timestamp "Running newsletter scheduler..."

if $PYTHON_CMD "$SCRIPT_DIR/src/scheduler.py" >> "$LOG_FILE" 2>&1; then
    log_with_timestamp "Newsletter scheduler completed successfully"
    exit 0
else
    log_with_timestamp "Newsletter scheduler failed with exit code $?"
    exit 1
fi