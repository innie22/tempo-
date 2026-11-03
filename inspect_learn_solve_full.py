import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('learnSolve.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Print renderModalContent from start to next top-level function
start_rmc = text.find('function renderModalContent() {')
end_rmc = text.find('\n    function ', start_rmc + 30)
print(f"renderModalContent length: {end_rmc - start_rmc}")

with open('scratch/render_modal_content_dump.js', 'w', encoding='utf-8') as f_out:
    f_out.write(text[start_rmc:end_rmc])

print("Wrote renderModalContent to scratch/render_modal_content_dump.js")
