import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('mode.js', 'r', encoding='utf-8') as f:
    text = f.read()

start = text.find('function renderRmodeHome()')
# Find next major function after renderRmodeHome
end = text.find('function renderUnclearModeHome()', start)
if end == -1:
    end = text.find('\n    function ', start + 1000)

print(f"renderRmodeHome length: {end - start}")
with open('scratch/rmode_home_dump.js', 'w', encoding='utf-8') as f_out:
    f_out.write(text[start:end])

print("Wrote scratch/rmode_home_dump.js")
