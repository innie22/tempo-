# -*- coding: utf-8 -*-
with open('mode.js', 'r', encoding='utf-8') as f:
    content = f.read()

target1 = '''                    <!-- RIGHT COLUMN (approx 42%): From the Tempo Community Panel -->
                    <div class="lg:col-span-5 w-full">
                        ${renderTempoPostsSection()}
                    </div>'''

replacement1 = '''                    <!-- RIGHT COLUMN (approx 42%): From the Tempo Community Panel -->
                    <div class="lg:col-span-5 w-full flex flex-col items-center">
                        ${renderTempoPostsSection()}
                    </div>'''

target2 = '''            <div class="urgent-section-posts bg-[#FEFAF4] border border-[#EAE4DF] rounded-3xl sm:rounded-[32px] p-4.5 sm:p-5 shadow-xs flex flex-col justify-between w-full space-y-3.5" data-tempo-ui="urgent-posts">'''

replacement2 = '''            <div class="urgent-section-posts bg-[#FEFAF4] border border-[#EAE4DF] rounded-3xl sm:rounded-[32px] p-4.5 sm:p-5 shadow-xs flex flex-col justify-between space-y-3.5 box-border" 
                 data-tempo-ui="urgent-posts"
                 style="width: calc(100% + 20px); margin-left: -10px; margin-right: -10px; box-sizing: border-box;">'''

content_lf = content.replace('\r\n', '\n')
target1_lf = target1.replace('\r\n', '\n')
replacement1_lf = replacement1.replace('\r\n', '\n')
target2_lf = target2.replace('\r\n', '\n')
replacement2_lf = replacement2.replace('\r\n', '\n')

assert target1_lf in content_lf, "Target 1 not found in mode.js"
assert target2_lf in content_lf, "Target 2 not found in mode.js"

new_content = content_lf.replace(target1_lf, replacement1_lf, 1)
new_content = new_content.replace(target2_lf, replacement2_lf, 1)
new_content = new_content.replace('\r\n', '\n')

with open('mode.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(new_content)

print("mode.js updated with +20px width on Tempo Community container.")
