#!/usr/bin/env python3
import argparse
import re
import os
import uuid
import sys

# Default file path if the user hasn't configured it.
OBSIDIAN_FILE = '/Users/tanue/Documents/antigravity/friendly-lavoisier/schedule.md'

def ensure_file_exists():
    if not os.path.exists(OBSIDIAN_FILE):
        with open(OBSIDIAN_FILE, 'w', encoding='utf-8') as f:
            f.write("# 34周日程大计\n\n")

def read_lines():
    ensure_file_exists()
    with open(OBSIDIAN_FILE, 'r', encoding='utf-8') as f:
        return f.readlines()

def write_lines(lines):
    with open(OBSIDIAN_FILE, 'w', encoding='utf-8') as f:
        f.writelines(lines)

def generate_block_id():
    return "^" + str(uuid.uuid4().hex)[:6]

def parse_tasks(lines):
    """
    Parses tasks. If a user manually added a task in Obsidian without a Block ID,
    this function will universally auto-generate one, append it to the line, and save the file.
    This guarantees precision and prevents the AI from losing track of manual entries.
    """
    tasks = []
    current_week = None
    week_pattern = re.compile(r'^#+\s+Week\s+(\d+)', re.IGNORECASE)
    
    # Matches any valid markdown checklist line
    task_pattern = re.compile(r'^(\s*-\s*\[([ xX])\])\s+(.*?)$')
    # Matches if the text ends with an Obsidian Block ID
    block_id_pattern = re.compile(r'(.*?)\s+(\^[a-zA-Z0-9_-]+)\s*$')
    
    modified_file = False

    for i, line in enumerate(lines):
        w_match = week_pattern.match(line)
        if w_match:
            current_week = int(w_match.group(1))
            continue
        
        t_match = task_pattern.match(line)
        if t_match:
            prefix = t_match.group(1)
            status_char = t_match.group(2)
            raw_text = t_match.group(3)
            
            b_match = block_id_pattern.match(raw_text)
            if b_match:
                task_text = b_match.group(1)
                block_id = b_match.group(2)
            else:
                # Missing Block ID! User typed this manually.
                # Auto-heal by appending a new block ID
                task_text = raw_text.rstrip()
                block_id = generate_block_id()
                lines[i] = f"{prefix} {task_text} {block_id}\n"
                modified_file = True
                
            tasks.append({
                "line_index": i,
                "prefix": prefix,
                "status": "Done" if status_char.lower() == 'x' else "Pending",
                "text": task_text,
                "block_id": block_id,
                "week": current_week
            })
            
    if modified_file:
        write_lines(lines)
        
    return tasks

def find_or_create_week(lines, week):
    week_pattern = re.compile(r'^#+\s+Week\s+(\d+)', re.IGNORECASE)
    for i, line in enumerate(lines):
        match = week_pattern.match(line)
        if match and int(match.group(1)) == week:
            return i
    
    if lines and not lines[-1].endswith('\n'):
        lines.append('\n')
    lines.append(f"\n## Week {week}\n")
    return len(lines) - 1

def add_task(args):
    lines = read_lines()
    _ = parse_tasks(lines) # Run parse to auto-heal any existing missing IDs first
    
    week_idx = find_or_create_week(lines, args.week)
    block_id = generate_block_id()
    new_task_line = f"- [ ] {args.title} {block_id}\n"
    
    lines.insert(week_idx + 1, new_task_line)
    write_lines(lines)
    print(f"Task added successfully. Block ID: {block_id}")

def list_tasks(args):
    lines = read_lines()
    tasks = parse_tasks(lines)
    
    if args.week is not None:
        tasks = [t for t in tasks if t['week'] == args.week]
    if args.status is not None:
        tasks = [t for t in tasks if t['status'].lower() == args.status.lower()]
    
    if not tasks:
        print("No tasks found matching criteria.")
        return
        
    print(f"{'Block ID':<10} | {'Week':<5} | {'Status':<10} | {'Title'}")
    print("-" * 80)
    for t in tasks:
        print(f"{t['block_id']:<10} | {t.get('week', 'N/A'):<5} | {t['status']:<10} | {t['text']}")

def update_task(args):
    lines = read_lines()
    tasks = parse_tasks(lines)
    
    target_task = next((t for t in tasks if t['block_id'] == args.id), None)
    if not target_task:
        print(f"Error: Task with Block ID {args.id} not found.")
        return
        
    idx = target_task['line_index']
    line = lines[idx]
    
    if args.status:
        box = "[x]" if args.status.lower() in ['done', 'x'] else "[ ]"
        line = re.sub(r'\[[ xX]\]', box, line, count=1)
        
    if args.title:
        prefix = target_task['prefix']
        if args.status:
            prefix = prefix.replace('[ ]', box).replace('[x]', box).replace('[X]', box)
        line = f"{prefix} {args.title} {target_task['block_id']}\n"
        
    if args.week and args.week != target_task['week']:
        lines.pop(idx)
        new_week_idx = find_or_create_week(lines, args.week)
        lines.insert(new_week_idx + 1, line)
    else:
        lines[idx] = line
        
    write_lines(lines)
    print(f"Task {args.id} updated successfully.")

def rollover(args):
    lines = read_lines()
    tasks = parse_tasks(lines)
    current_week = args.current_week
    
    tasks_to_move = []
    for t in reversed(tasks):
        if t['status'] == 'Pending' and t['week'] is not None and t['week'] < current_week:
            tasks_to_move.append(t)
            lines.pop(t['line_index'])
            
    if not tasks_to_move:
        print("No tasks needed to be rolled over.")
        return
        
    target_week_idx = find_or_create_week(lines, current_week)
    
    rolled_over_count = 0
    for t in tasks_to_move:
        text = t['text']
        if '#顺延' not in text:
            text += " #顺延"
        new_line = f"- [ ] {text} {t['block_id']}\n"
        lines.insert(target_week_idx + 1, new_line)
        rolled_over_count += 1
        print(f" - Task {t['block_id']} rolled over to week {current_week}.")
        
    write_lines(lines)
    print(f"Rolled over {rolled_over_count} tasks to week {current_week}.")

def main():
    parser = argparse.ArgumentParser(description="Obsidian Dynamic Schedule Manager")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_add = subparsers.add_parser('add', help="Add a new task")
    parser_add.add_argument('--title', required=True, help="Task text")
    parser_add.add_argument('--week', type=int, required=True, help="Target week number")

    parser_list = subparsers.add_parser('list', help="List tasks")
    parser_list.add_argument('--week', type=int, help="Filter by week")
    parser_list.add_argument('--status', help="Filter by status (Pending, Done)")

    parser_update = subparsers.add_parser('update', help="Update a task")
    parser_update.add_argument('--id', required=True, help="Block ID (e.g. ^a1b2c3)")
    parser_update.add_argument('--status', help="New status (Done, Pending)")
    parser_update.add_argument('--week', type=int, help="Move to new week")
    parser_update.add_argument('--title', help="New task text")

    parser_rollover = subparsers.add_parser('rollover', help="Roll over past pending tasks")
    parser_rollover.add_argument('--current-week', type=int, required=True, help="The current week number")

    args = parser.parse_args()

    if args.command == 'add':
        add_task(args)
    elif args.command == 'list':
        list_tasks(args)
    elif args.command == 'update':
        update_task(args)
    elif args.command == 'rollover':
        rollover(args)

if __name__ == '__main__':
    main()
