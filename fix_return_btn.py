with open('communityPosts.js', 'rb') as f:
    text = f.read().decode('utf-8')

old_code = '''        if (sourceContext === 'recovery' || currentMode === 'recovery') {
            backLabel.textContent = 'Back to Recovery Mode';
        } else if (sourceContext === 'emergency' || currentMode === 'emergency') {
            backLabel.textContent = 'Back to Emergency Support';
        } else {
            backLabel.textContent = 'Back to Today';
        }
    }

    function handleReturnNavigation() {
        const currentMode = (window.TempoMode && typeof window.TempoMode.getActiveContext === 'function' && window.TempoMode.getActiveContext())
            || (window.TempoMode && typeof window.TempoMode.getMode === 'function' ? window.TempoMode.getMode() : null);
        const sourceContext = (window.TempoMode && typeof window.TempoMode.getSourceContext === 'function')
            ? window.TempoMode.getSourceContext()
            : (currentMode || 'today');

        if (sourceContext === 'recovery' || currentMode === 'recovery') {'''

new_code = '''        if (sourceContext === 'recovery' || (!sourceContext && currentMode === 'recovery')) {
            backLabel.textContent = 'Back to Recovery Mode';
        } else if (sourceContext === 'emergency' || (!sourceContext && currentMode === 'emergency')) {
            backLabel.textContent = 'Back to Emergency Support';
        } else {
            backLabel.textContent = 'Back to Today';
        }
    }

    function handleReturnNavigation() {
        const currentMode = (window.TempoMode && typeof window.TempoMode.getActiveContext === 'function' && window.TempoMode.getActiveContext())
            || (window.TempoMode && typeof window.TempoMode.getMode === 'function' ? window.TempoMode.getMode() : null);
        const sourceContext = (window.TempoMode && typeof window.TempoMode.getSourceContext === 'function')
            ? window.TempoMode.getSourceContext()
            : (currentMode || 'today');

        if (sourceContext === 'recovery' || (!sourceContext && currentMode === 'recovery')) {'''

# Normalize line endings to find and replace
text_lf = text.replace('\r\n', '\n')
old_code_lf = old_code.replace('\r\n', '\n')
new_code_lf = new_code.replace('\r\n', '\n')

if old_code_lf in text_lf:
    text_lf = text_lf.replace(old_code_lf, new_code_lf, 1)
    text_crlf = text_lf.replace('\n', '\r\n')
    with open('communityPosts.js', 'wb') as f:
        f.write(text_crlf.encode('utf-8'))
    print("Successfully updated return button logic in communityPosts.js")
else:
    print("Error: old_code_lf not found")
