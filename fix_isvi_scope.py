with open('selfCheckWorkspace.js', 'r', encoding='utf-8', newline='') as f:
    c = f.read()

assert '\r' not in c, "selfCheckWorkspace.js must be strictly LF"

target_top = """    function render() {
        const root = document.getElementById('self-check-workspace-root');
        if (!root) return;"""

replace_top = """    function render() {
        const root = document.getElementById('self-check-workspace-root');
        if (!root) return;

        const isVi = isViLocale();"""

assert target_top in c, "target_top not found"
c = c.replace(target_top, replace_top, 1)

target_mid = """        const originMode = (window.TempoMode && typeof window.TempoMode.getOriginatingMode === 'function') 
            ? window.TempoMode.getOriginatingMode() 
            : ((window.TempoMode && typeof window.TempoMode.getSourceContext === 'function') ? window.TempoMode.getSourceContext() : null);
        const isVi = isViLocale();
        let returnLabel = isVi ? 'Quay lại trang chủ' : 'Return Home';"""

replace_mid = """        const originMode = (window.TempoMode && typeof window.TempoMode.getOriginatingMode === 'function') 
            ? window.TempoMode.getOriginatingMode() 
            : ((window.TempoMode && typeof window.TempoMode.getSourceContext === 'function') ? window.TempoMode.getSourceContext() : null);
        let returnLabel = isVi ? 'Quay lại trang chủ' : 'Return Home';"""

assert target_mid in c, "target_mid not found"
c = c.replace(target_mid, replace_mid, 1)

assert '\r' not in c, "selfCheckWorkspace.js must retain strictly LF line endings"

with open('selfCheckWorkspace.js', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

print("isVi scope fixed successfully!")
