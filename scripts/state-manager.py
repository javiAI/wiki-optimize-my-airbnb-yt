#!/usr/bin/env python3
"""
State Manager for CLAUDE_AUTOMATED.md

Reads and writes YAML state section (lines 1-162) of CLAUDE_AUTOMATED.md.
Handles phase transitions, task completion, and progress tracking.

Usage:
  python3 state-manager.py --read-state       # Print entire state
  python3 state-manager.py --get-phase        # Get current phase number
  python3 state-manager.py --get-next-task    # Get next incomplete task
  python3 state-manager.py --complete <ID>    # Mark task complete
  python3 state-manager.py --approve <ID>...  # Approve task(s)
"""

import yaml
import json
import sys
from pathlib import Path
from datetime import datetime


class CLAUDEStateManager:
    def __init__(self, claude_path="CLAUDE_AUTOMATED.md"):
        self.path = Path(claude_path)
        if not self.path.exists():
            raise FileNotFoundError(f"{claude_path} not found")

    def read_state(self):
        """Extract YAML frontmatter from CLAUDE_AUTOMATED.md"""
        with open(self.path, 'r') as f:
            content = f.read()
            try:
                _, frontmatter, _ = content.split("---", 2)
                return yaml.safe_load(frontmatter)
            except ValueError:
                raise ValueError("CLAUDE_AUTOMATED.md missing YAML frontmatter (---)")
            except yaml.YAMLError as e:
                raise ValueError(f"YAML parse error: {e}")

    def write_state(self, state):
        """Update YAML frontmatter in CLAUDE_AUTOMATED.md"""
        with open(self.path, 'r') as f:
            content = f.read()
            parts = content.split("---", 2)

        if len(parts) != 3:
            raise ValueError("CLAUDE_AUTOMATED.md missing proper YAML markers")

        # Reconstruct with updated YAML
        updated_yaml = yaml.dump(state, default_flow_style=False, sort_keys=False)
        updated_content = f"---\n{updated_yaml}---\n{parts[2]}"

        with open(self.path, 'w') as f:
            f.write(updated_content)

    def get_current_phase(self):
        """Return current phase number"""
        state = self.read_state()
        return state['execution_state']['current_phase']

    def get_next_task(self):
        """Return next incomplete task ID in current phase"""
        state = self.read_state()
        phase_num = state['execution_state']['current_phase']
        phase_key = f'phase_{phase_num}'
        next_task = state['phases'][phase_key].get('next_incomplete_task')
        return next_task

    def mark_task_complete(self, task_id):
        """Mark a task as complete and update progress"""
        state = self.read_state()
        phase_num = state['execution_state']['current_phase']
        phase_key = f'phase_{phase_num}'

        # Update optimization status
        if task_id in state['optimizations']:
            state['optimizations'][task_id]['status'] = 'complete'

        # Add to completed tasks
        completed = state['phases'][phase_key]['completed_tasks']
        if task_id not in completed:
            completed.append(task_id)

        # Recalculate progress
        total_tasks = state['phases'][phase_key]['total_tasks']
        progress = int(100 * len(completed) / total_tasks)
        state['phases'][phase_key]['progress_percent'] = progress

        # Find next incomplete task
        all_tasks = [opt_id for opt_id, opt in state['optimizations'].items()
                     if opt['phase'] == phase_num and opt['status'] != 'complete']
        next_incomplete = next((t for t in all_tasks if t not in completed), None)
        state['phases'][phase_key]['next_incomplete_task'] = next_incomplete

        # Update timestamp
        state['automation']['last_update'] = datetime.now().isoformat() + 'Z'

        self.write_state(state)
        return {
            'task_id': task_id,
            'status': 'complete',
            'progress': progress,
            'next_task': next_incomplete
        }

    def approve_tasks(self, *task_ids):
        """Approve one or more tasks for execution"""
        state = self.read_state()
        phase_num = state['execution_state']['current_phase']
        phase_key = f'phase_{phase_num}'

        for task_id in task_ids:
            if task_id in state['optimizations']:
                state['optimizations'][task_id]['status'] = 'in_progress'

        state['phases'][phase_key]['status'] = 'in_progress'
        state['execution_state']['phase_status'] = 'in_progress'
        state['automation']['last_update'] = datetime.now().isoformat() + 'Z'

        self.write_state(state)
        return {
            'approved': list(task_ids),
            'phase': phase_num,
            'status': 'in_progress'
        }

    def get_progress_report(self):
        """Generate human-readable progress report"""
        state = self.read_state()
        report = []

        report.append("╔════════════════════════════════════════════╗")
        report.append("║       LLM Wiki Optimization Progress       ║")
        report.append("╚════════════════════════════════════════════╝")
        report.append("")

        vault = state['vault']
        baseline = state['baseline_metrics']
        report.append(f"Vault: {vault['name']}")
        report.append(f"Quality: {vault['quality_score']}/10 → Target: {vault['target_score']}/10")
        report.append(f"Baseline Tokens: {baseline['baseline_overhead_tokens']:,} → Target: ~1,200")
        report.append("")

        for phase_num in range(1, 5):
            phase_key = f'phase_{phase_num}'
            phase = state['phases'][phase_key]
            report.append(f"PHASE {phase_num}: {phase['name']}")
            report.append(f"  Status: {phase['status']}")
            completed = len(phase['completed_tasks'])
            total = phase['total_tasks']
            report.append(f"  Progress: {completed}/{total} tasks ({phase['progress_percent']}%)")
            if phase.get('next_incomplete_task'):
                report.append(f"  Next: {phase['next_incomplete_task']}")
            report.append("")

        total_hours = sum(opt['effort_hours'] for opt in state['optimizations'].values())
        report.append("═" * 46)
        report.append(f"Total Effort: {total_hours:.1f} hours across 4 phases")
        report.append(f"Estimated: {int(total_hours/2)} days @ 2h/day")

        return '\n'.join(report)


def main():
    manager = CLAUDEStateManager()

    if len(sys.argv) < 2:
        print(manager.get_progress_report())
        return

    cmd = sys.argv[1]

    if cmd == '--read-state':
        state = manager.read_state()
        print(json.dumps(state, indent=2))

    elif cmd == '--get-phase':
        print(manager.get_current_phase())

    elif cmd == '--get-next-task':
        task = manager.get_next_task()
        print(task if task else "No incomplete tasks")

    elif cmd == '--complete' and len(sys.argv) > 2:
        result = manager.mark_task_complete(sys.argv[2])
        print(f"✅ {result['task_id']} marked complete")
        print(f"Progress: {result['progress']}%")
        if result['next_task']:
            print(f"Next: {result['next_task']}")

    elif cmd == '--approve' and len(sys.argv) > 2:
        task_ids = sys.argv[2:]
        result = manager.approve_tasks(*task_ids)
        print(f"✅ Approved: {', '.join(result['approved'])}")
        print(f"Phase {result['phase']} now in_progress")

    else:
        print(manager.get_progress_report())


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
