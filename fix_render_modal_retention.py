with open('selfCheckWorkspace.js', 'r', encoding='utf-8') as f:
    code = f.read()

target_render_start = """    // Main Render Function
    function render() {
        const root = document.getElementById('self-check-workspace-root');
        if (!root) return;"""

refined_render_start = """    // Main Render Function
    function render() {
        const root = document.getElementById('self-check-workspace-root');
        if (!root) return;

        const fcModalBefore = document.getElementById('modal-selfcheck-fullcheck');
        const wasFullCheckOpen = !!(fcModalBefore && !fcModalBefore.classList.contains('hidden') && fullCheckTrackerId);
        const moModalBefore = document.getElementById('modal-selfcheck-monthly-overview');
        const wasOverviewOpen = !!(moModalBefore && !moModalBefore.classList.contains('hidden') && monthlyOverviewTrackerId);"""

assert target_render_start in code, "target_render_start not found in selfCheckWorkspace.js"
code = code.replace(target_render_start, refined_render_start, 1)

target_render_end = """                        <button type="button" onclick="window.TempoSelfCheckWorkspace.closeWeeklyReport()" 
                                class="px-5 py-2 rounded-xl text-xs font-bold bg-[#7B9688] hover:bg-[#6D8475] text-white transition cursor-pointer shadow-xs">
                            ${isVi ? 'Đóng' : 'Close'}
                        </button>
                    </div>
                </div>
            </div>
        `;
    }"""

refined_render_end = """                        <button type="button" onclick="window.TempoSelfCheckWorkspace.closeWeeklyReport()" 
                                class="px-5 py-2 rounded-xl text-xs font-bold bg-[#7B9688] hover:bg-[#6D8475] text-white transition cursor-pointer shadow-xs">
                            ${isVi ? 'Đóng' : 'Close'}
                        </button>
                    </div>
                </div>
            </div>
        `;

        if (wasFullCheckOpen && fullCheckTrackerId) {
            const fcModal = document.getElementById('modal-selfcheck-fullcheck');
            if (fcModal) fcModal.classList.remove('hidden');
            renderFullCheckModal(fullCheckTrackerId, fullCheckYear, fullCheckMonth);
        }
        if (wasOverviewOpen && monthlyOverviewTrackerId) {
            const moModal = document.getElementById('modal-selfcheck-monthly-overview');
            if (moModal) moModal.classList.remove('hidden');
            renderMonthlyOverview(monthlyOverviewTrackerId);
        }
    }"""

assert target_render_end in code, "target_render_end not found in selfCheckWorkspace.js"
code = code.replace(target_render_end, refined_render_end, 1)

code = code.replace('\r\n', '\n')
assert '\r' not in code, "CRLF found in selfCheckWorkspace.js"

with open('selfCheckWorkspace.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(code)
print("selfCheckWorkspace.js updated successfully with modal retention in render()")
