import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

file_path = 'stressRelief.js'

with open(file_path, 'rb') as f:
    raw = f.read()

text = raw.decode('utf-8')

text = text.replace(
    '<h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">Gentle Match</h3>',
    '<h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">Ghép cặp Nhẹ nhàng</h3>'
)
text = text.replace(
    """                    <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-[#ECC9BA] text-[#202124]">
                        Gentle Match
                    </span>""",
    """                    <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-[#ECC9BA] text-[#202124]">
                        Ghép cặp Nhẹ nhàng
                    </span>"""
)

# Convert all LFs to CRLFs
text_lf = text.replace('\r\n', '\n')
new_crlf = text_lf.replace('\n', '\r\n')

with open(file_path, 'wb') as f:
    f.write(new_crlf.encode('utf-8'))

with open(file_path, 'rb') as f:
    final_bytes = f.read()

final_crlf = final_bytes.count(b'\r\n')
final_lone_lf = final_bytes.count(b'\n') - final_crlf
print(f"stressRelief.js Gentle Match updated. Final CRLF: {final_crlf}, lone LF: {final_lone_lf}")
