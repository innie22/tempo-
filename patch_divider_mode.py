# -*- coding: utf-8 -*-
with open('mode.js', 'rb') as f:
    content = f.read()

target = b'<div class="pt-2 sm:pt-4" data-tempo-ui="entry-secondary-cards">'
replacement = b'<div class="pt-6 sm:pt-8 border-t border-[#EAE4DF]/80" data-tempo-ui="entry-secondary-cards">'

if target in content:
    new_content = content.replace(target, replacement, 1)
    if b'\r\n' in new_content:
        raise ValueError("CRLF detected in mode.js! Must remain LF.")
    with open('mode.js', 'wb') as f:
        f.write(new_content)
    print("mode.js updated with border-t divider line, LF preserved.")
else:
    print("Target not found or already updated.")
