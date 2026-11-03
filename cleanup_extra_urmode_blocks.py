with open('mode.js', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'\n    // =========================================================================\n    // URMODE \(EMERGENCY\) TASK DETAIL POPUP MODAL', text)]
print('Found matches:', len(matches))

# The intended block is Block 5 (index 5)
blocks_to_remove = [6, 4, 3, 2, 1, 0]

for idx in blocks_to_remove:
    pos = matches[idx]
    fn_idx = text.find('function renderUrmodeTaskDetailModalHTML', pos)
    end_fn = text.find(';\n    }', fn_idx) + len(';\n    }')
    text = text[:pos] + text[end_fn:]

with open('mode.js', 'wb') as f:
    f.write(text.encode('utf-8'))

print('Cleaned mode.js successfully!')
