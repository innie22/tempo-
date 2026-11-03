import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('mode.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Check specific key phrases in mode.js
targets = [
    "Quick Relief", "Focus Now", "Your Working Plan", "Daily Self-check", "TASKS", "TASK DONE",
    "From the Tempo Community", "See all", "Now", "Scheduled", "Up Next", "Done", "Task details",
    "Action Steps", "Task Notes", "Start focus now", "Mark completed", "Reopen task", "Save changes",
    "Close", "Academic Task", "No description", "No fixed deadline", "Add subtask", "What do you need right now?",
    "Choose a grounding method", "You haven't set up your working plan yet", "You're still setting up your plan."
]

for t in targets:
    count = text.count(t)
    if count > 0:
        print(f"'{t}': {count} occurrences")
