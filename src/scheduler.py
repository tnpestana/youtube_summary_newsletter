#!/usr/bin/env python3
"""
YouTube Summary Newsletter Scheduler

This script handles missed executions when the computer was off during the scheduled time.
It should be run on system startup or when the computer comes online.
"""

import os
import sys
import json
import datetime
from pathlib import Path

# Add the src directory to the Python path
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(script_dir))

def get_last_run_file():
    """Get the path to the last run timestamp file."""
    return project_root / "logs" / "last_run.json"

def load_last_run():
    """Load the last successful run timestamp."""
    last_run_file = get_last_run_file()
    if not last_run_file.exists():
        return None

    try:
        with open(last_run_file, 'r') as f:
            data = json.load(f)
            return datetime.datetime.fromisoformat(data['last_run'])
    except (json.JSONDecodeError, KeyError, ValueError):
        return None

def save_last_run():
    """Save the current timestamp as the last successful run."""
    last_run_file = get_last_run_file()
    last_run_file.parent.mkdir(exist_ok=True)

    data = {
        'last_run': datetime.datetime.now().isoformat(),
        'status': 'completed'
    }

    with open(last_run_file, 'w') as f:
        json.dump(data, f, indent=2)

def should_run_now():
    """Determine if the newsletter should run now based on last run time."""
    last_run = load_last_run()
    now = datetime.datetime.now()

    # If never run before, run now
    if last_run is None:
        return True, "First time running"

    # Calculate time since last run
    time_since_last = now - last_run

    # If more than 23 hours since last run, we should run
    if time_since_last > datetime.timedelta(hours=23):
        return True, f"Last run was {time_since_last} ago"

    return False, f"Last run was {time_since_last} ago (too recent)"

def run_newsletter():
    """Run the main newsletter application."""
    try:
        import subprocess
        import sys

        print(f"Running newsletter at {datetime.datetime.now()}")

        # Run main.py as a subprocess
        main_script = project_root / "src" / "main.py"
        result = subprocess.run([sys.executable, str(main_script)],
                              capture_output=True, text=True, cwd=str(project_root))

        if result.returncode == 0:
            print("Newsletter completed successfully")
            print("STDOUT:", result.stdout)
            save_last_run()
            return True
        else:
            print(f"Newsletter failed with return code {result.returncode}")
            print("STDERR:", result.stderr)
            return False

    except Exception as e:
        print(f"Error running newsletter: {e}")
        return False

def main():
    """Main scheduler function."""
    print(f"Scheduler started at {datetime.datetime.now()}")

    should_run, reason = should_run_now()
    print(f"Should run: {should_run} - {reason}")

    if should_run:
        success = run_newsletter()
        sys.exit(0 if success else 1)
    else:
        print("Newsletter not needed at this time")
        sys.exit(0)

if __name__ == "__main__":
    main()