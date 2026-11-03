import os

# 1. Update i18n.js
with open('i18n.js', 'r', encoding='utf-8') as f:
    i18n_code = f.read()

vi_title_target = 'title: "Tự kiểm tra Tempo",'
vi_title_replacement = 'title: "Tempo Self-check",'

assert vi_title_target in i18n_code, "vi_title_target not found in i18n.js"
i18n_code = i18n_code.replace(vi_title_target, vi_title_replacement, 1)

i18n_code = i18n_code.replace('\r\n', '\n')
assert '\r' not in i18n_code, "CRLF found in i18n.js"

with open('i18n.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(i18n_code)
print("i18n.js updated successfully")

# 2. Update selfCheckWorkspace.js
with open('selfCheckWorkspace.js', 'r', encoding='utf-8') as f:
    scw_code = f.read()

target_render_title = """                    <!-- Centered Title -->
                    <div class="absolute left-1/2 -translate-x-1/2 text-center pointer-events-none">
                        <h1 class="font-heading text-2xl sm:text-3xl md:text-4xl font-extrabold text-[#234E3B] tracking-tight">
                            ${isVi ? 'Tự kiểm tra Tempo' : 'Tempo Self-check'}
                        </h1>
                    </div>"""

refined_render_title = """                    <!-- Centered Title -->
                    <div class="absolute left-1/2 -translate-x-1/2 text-center pointer-events-none">
                        <h1 class="font-heading text-2xl sm:text-3xl md:text-4xl font-extrabold text-[#234E3B] tracking-tight">
                            ${window.t ? window.t('selfCheckWorkspace.title', {}, 'Tempo Self-check') : 'Tempo Self-check'}
                        </h1>
                    </div>"""

assert target_render_title in scw_code, "target_render_title not found in selfCheckWorkspace.js"
scw_code = scw_code.replace(target_render_title, refined_render_title, 1)

comment_target = "* Implements the Tự kiểm tra Tempo tool page matching the reference design:"
comment_replacement = "* Implements the Tempo Self-check tool page matching the reference design:"
if comment_target in scw_code:
    scw_code = scw_code.replace(comment_target, comment_replacement, 1)

scw_code = scw_code.replace('\r\n', '\n')
assert '\r' not in scw_code, "CRLF found in selfCheckWorkspace.js"

with open('selfCheckWorkspace.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(scw_code)
print("selfCheckWorkspace.js updated successfully")
