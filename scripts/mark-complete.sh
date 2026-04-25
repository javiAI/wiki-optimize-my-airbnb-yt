#!/bin/bash
# Mark task as complete and show next task

if [ $# -eq 0 ]; then
    echo "Usage: ./scripts/mark-complete.sh <TASK_ID>"
    echo "Example: ./scripts/mark-complete.sh O1"
    exit 1
fi

python3 "$(dirname "$0")/state-manager.py" --complete "$1"
echo ""
./scripts/next-task.sh
