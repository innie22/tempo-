import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

file_path = 'mode.js'

with open(file_path, 'rb') as f:
    raw = f.read()

text = raw.decode('utf-8')

# Replace Quick Relief on its own line
text = re.sub(r'(\n\s*)Quick Relief(\s*\n)', r'\1Giải tỏa nhanh\2', text)

# Replace Focus Now on its own line
text = re.sub(r'(\n\s*)Focus Now(\s*\n)', r'\1Tập trung ngay\2', text)

# Also check any other occurrences
text = text.replace(">Quick Relief<", ">Giải tỏa nhanh<")
text = text.replace(">Focus Now<", ">Tập trung ngay<")

text_lf = text.replace('\r\n', '\n')

with open(file_path, 'wb') as f:
    f.write(text_lf.encode('utf-8'))

with open(file_path, 'rb') as f:
    final_bytes = f.read()

final_crlf = final_bytes.count(b'\r\n')
final_lone_lf = final_bytes.count(b'\n') - final_crlf
print(f"mode.js card titles updated. Final CRLF: {final_crlf}, lone LF: {final_lone_lf}")
