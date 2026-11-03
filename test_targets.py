with open('scratch/exact_render_modal.js', 'r', encoding='utf-8') as f:
    code = f.read()

targets = [
    'Your Tracking Item',
    'Enter tracking name',
    'Type:',
    'Sign of stress',
    'Supportive',
    'Create new type',
    'Tracking method:',
    'Options',
    'Scale',
    'Quantity',
    'Alert system',
    'On',
    'Off',
    'Notice me if my checks are',
    'Alert type:',
    'Sign of Stress',
    'Supportive Reminder',
    'More than',
    '% for',
    'days in a row.',
    'Cancel',
    "draft.mode === 'create' ? 'Add tracking' : 'Save changes'"
]

for t in targets:
    print(f"{t!r:<30}: {t in code}")
