#!/usr/bin/env python3
"""
Phase Executor — Determines what task to execute in current phase

Reads state from CLAUDE_AUTOMATED.md and shows:
1. Current phase
2. Next incomplete task
3. Full task instructions (from reference)
4. Estimated effort

Usage:
  python3 phase-executor.py              # Show next task
  python3 phase-executor.py --run        # Execute task (placeholder)
  python3 phase-executor.py --info <ID>  # Show details of specific task
"""

import sys
import json
from pathlib import Path

# Import state manager from same directory
sys.path.insert(0, str(Path(__file__).parent))
from state_manager import CLAUDEStateManager


def show_task_info(state, task_id):
    """Display detailed info about a specific task"""
    if task_id not in state['optimizations']:
        print(f"Task {task_id} not found")
        return

    task = state['optimizations'][task_id]
    print(f"\n{'═' * 60}")
    print(f"Task: {task['name']}")
    print(f"{'═' * 60}")
    print(f"ID:              {task_id}")
    print(f"Phase:           {task['phase']}")
    print(f"Effort:          {task['effort_hours']} hours")
    print(f"Status:          {task['status']}")
    print(f"Impact (High):   {'Yes' if task.get('impact_high') else 'No'}")
    print(f"Reference:       {task.get('reference', 'N/A')}")
    print(f"\nNext step: Review the reference document above.")
    print(f"Then: ./scripts/mark-complete.sh {task_id}")
    print(f"{'═' * 60}\n")


def main():
    manager = CLAUDEStateManager()
    state = manager.read_state()

    if len(sys.argv) > 1:
        if sys.argv[1] == '--run':
            print("⚠️  Automatic execution not yet implemented.")
            print("For now, execute tasks manually per the instructions below.\n")
            # Fall through to show next task
        elif sys.argv[1] == '--info' and len(sys.argv) > 2:
            show_task_info(state, sys.argv[2])
            return

    # Show next task
    current_phase = state['execution_state']['current_phase']
    phase_key = f'phase_{current_phase}'
    phase = state['phases'][phase_key]

    next_task = phase.get('next_incomplete_task')

    if not next_task or next_task == 'None':
        print(f"✅ Phase {current_phase} is complete!")
        print("Ready to move to next phase.\n")
        return

    task = state['optimizations'].get(next_task)
    if not task:
        print(f"❌ Task {next_task} not found in state")
        return

    print(f"\n{'━' * 60}")
    print(f"PHASE {current_phase}: {phase['name']}")
    print(f"{'━' * 60}")
    print(f"Progress: {phase['progress_percent']}% ({len(phase['completed_tasks'])}/{phase['total_tasks']})")
    print(f"\n📋 Next Task to Execute:\n")
    print(f"  ID:      {next_task}")
    print(f"  Name:    {task['name']}")
    print(f"  Effort:  {task['effort_hours']}h")
    print(f"  Status:  {task['status']}")

    if task['status'] == 'pending_approval':
        print(f"\n⚠️  This task is PENDING APPROVAL")
        print(f"   Run: ./scripts/approve-phase.sh {next_task}")
    elif task['status'] == 'in_progress':
        print(f"\n📖 Reference: {task.get('reference', 'See ARCHITECTURE.md')}")
        print(f"\n✅ When complete, run:")
        print(f"   ./scripts/mark-complete.sh {next_task}")

    print(f"\n{'━' * 60}\n")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
