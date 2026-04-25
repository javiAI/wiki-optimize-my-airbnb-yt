#!/bin/bash
# Approve tasks and transition to in_progress

if [ $# -eq 0 ]; then
    echo "Usage: ./scripts/approve-phase.sh O1 O2 [O3 ...]"
    echo "Example: ./scripts/approve-phase.sh O1 O2"
    exit 1
fi

echo "Approving tasks: $@"
python3 "$(dirname "$0")/state-manager.py" --approve "$@"
echo ""
echo "✅ Tasks approved. Phase now in_progress."
echo ""
./scripts/next-task.sh
