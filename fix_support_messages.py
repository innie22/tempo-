# -*- coding: utf-8 -*-
with open('support.js', 'r', encoding='utf-8', newline='') as f:
    content = f.read()

target = '''                    <!-- Conversation Thread -->
                    <div class="space-y-3 pt-3 border-t border-gray-100">
                        ${t.messages.map(m => `'''

replacement = '''                    <!-- Conversation Thread -->
                    <div class="space-y-3 pt-3 border-t border-gray-100">
                        ${(Array.isArray(t.messages) ? t.messages : []).map(m => `'''

t_crlf = target.replace('\r\n', '\n').replace('\n', '\r\n')
r_crlf = replacement.replace('\r\n', '\n').replace('\n', '\r\n')

if t_crlf not in content:
    raise ValueError("Target not found in support.js")

content = content.replace(t_crlf, r_crlf, 1)

with open('support.js', 'w', encoding='utf-8', newline='') as f:
    f.write(content)

print("SUCCESS: support.js defensive fix applied")
