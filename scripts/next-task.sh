#!/bin/bash
# Show next incomplete task in current phase (human-friendly)

PHASE=$(python3 "$(dirname "$0")/state-manager.py" --get-phase)
NEXT_TASK=$(python3 "$(dirname "$0")/state-manager.py" --get-next-task)

if [ -z "$NEXT_TASK" ] || [ "$NEXT_TASK" == "None" ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🎉 Phase $PHASE is COMPLETE!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 0
fi

# Extract task details from state
STATE=$(python3 "$(dirname "$0")/state-manager.py" --read-state 2>/dev/null)

if ! command -v jq &> /dev/null; then
    # Fallback if jq not available
    echo "Next Task: $NEXT_TASK (Phase $PHASE)"
    exit 0
fi

TASK_NAME=$(echo "$STATE" | jq -r ".optimizations[\"$NEXT_TASK\"].name // \"Unknown\"")
EFFORT=$(echo "$STATE" | jq -r ".optimizations[\"$NEXT_TASK\"].effort_hours // 0")
REFERENCE=$(echo "$STATE" | jq -r ".optimizations[\"$NEXT_TASK\"].reference // \"\"")
STATUS=$(echo "$STATE" | jq -r ".optimizations[\"$NEXT_TASK\"].status // \"pending\"")

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase $PHASE — Next Task"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Task ID:    $NEXT_TASK"
echo "Name:       $TASK_NAME"
echo "Effort:     ${EFFORT}h"
echo "Status:     $STATUS"
[ -n "$REFERENCE" ] && echo "Reference:  $REFERENCE"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
