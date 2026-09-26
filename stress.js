/**
 * Tempo Stress Self-Assessment & Radar Visualization
 * 6-dimension self-check with real-time SVG radar chart and tailored non-clinical next steps.
 */

window.TempoStress = (function() {
    const dimensions = [
        { key: 'perceivedStress', label: 'Perceived Stress', default: 7 },
        { key: 'deadlinePressure', label: 'Deadline Pressure', default: 9 },
        { key: 'sleepQuality', label: 'Sleep Quality', default: 4 },
        { key: 'concentration', label: 'Concentration', default: 5 },
        { key: 'exhaustion', label: 'Exhaustion Level', default: 7 },
        { key: 'burnoutSigns', label: 'Burnout Early Signs', default: 6 }
    ];

    let currentValues = {};

    function init() {
        // Initialize default values
        dimensions.forEach(d => {
            currentValues[d.key] = d.default;
        });

        bindEvents();
        updateScoreAndRadar();
    }

    function bindEvents() {
        dimensions.forEach(d => {
            const slider = document.getElementById(`slider-${d.key}`);
            const valLabel = document.getElementById(`val-${d.key}`);
            if (slider && valLabel) {
                slider.value = currentValues[d.key];
                valLabel.textContent = slider.value;

                slider.addEventListener('input', (e) => {
                    const val = parseInt(e.target.value, 10);
                    currentValues[d.key] = val;
                    valLabel.textContent = val;
                    updateScoreAndRadar();
                });
            }
        });

        const resetBtn = document.getElementById('btn-reset-stress');
        if (resetBtn) {
            resetBtn.addEventListener('click', resetDefaults);
        }

        const saveBtn = document.getElementById('btn-save-stress-result');
        if (saveBtn) {
            saveBtn.addEventListener('click', saveResult);
        }
    }

    function resetDefaults() {
        dimensions.forEach(d => {
            currentValues[d.key] = 5;
            const slider = document.getElementById(`slider-${d.key}`);
            const valLabel = document.getElementById(`val-${d.key}`);
            if (slider) slider.value = 5;
            if (valLabel) valLabel.textContent = 5;
        });
        updateScoreAndRadar();
        window.TempoApp.showToast("Sliders reset to neutral (5/10).");
    }

    function updateScoreAndRadar() {
        let total = 0;
        dimensions.forEach(d => {
            total += currentValues[d.key];
        });

        // Determine Level
        let status = 'Steady Cadence';
        let statusColor = 'text-emerald-700 bg-emerald-50 border-emerald-300';
        let adviceSummary = 'Your workload appears balanced. Focus on maintaining healthy sleep and steady study intervals.';

        if (total >= 42) {
            status = 'Overloaded / Acute Strain';
            statusColor = 'text-amber-800 bg-amber-50 border-amber-300';
            adviceSummary = 'You are experiencing high cognitive saturation. Prioritize task triage immediately and schedule intentional decompression.';
        } else if (total >= 25) {
            status = 'Strained Pressure';
            statusColor = 'text-indigo-800 bg-indigo-50 border-indigo-300';
            adviceSummary = 'Moderate academic friction detected. Time-blocking and sleep protection will prevent escalation into burnout.';
        }

        const scoreEl = document.getElementById('stress-total-score');
        const badgeEl = document.getElementById('stress-status-badge');
        const adviceEl = document.getElementById('stress-advice-text');

        if (scoreEl) scoreEl.textContent = `${total} / 60`;
        if (badgeEl) {
            badgeEl.textContent = status;
            badgeEl.className = `inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border ${statusColor}`;
        }
        if (adviceEl) adviceEl.textContent = adviceSummary;

        // Render Dynamic SVG Radar
        drawRadarChart(currentValues);
        updateTailoredRecommendations(currentValues);
    }

    function drawRadarChart(vals) {
        const svg = document.getElementById('stress-radar-svg');
        if (!svg) return;

        const size = 300;
        const center = size / 2;
        const radius = 100;
        const totalAxes = dimensions.length;
        const angleStep = (Math.PI * 2) / totalAxes;

        // Clear existing dynamic elements
        svg.innerHTML = '';

        // Draw concentric background web circles (levels 2, 4, 6, 8, 10)
        [2, 4, 6, 8, 10].forEach(level => {
            const r = (level / 10) * radius;
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', center);
            circle.setAttribute('cy', center);
            circle.setAttribute('r', r);
            circle.setAttribute('fill', 'none');
            circle.setAttribute('stroke', level === 10 ? '#CBD5E1' : '#E2E8F0');
            circle.setAttribute('stroke-dasharray', level === 10 ? 'none' : '3 3');
            svg.appendChild(circle);
        });

        // Calculate polygon points
        const points = [];
        dimensions.forEach((d, i) => {
            const angle = i * angleStep - Math.PI / 2;
            const val = vals[d.key] || 5;
            const r = (val / 10) * radius;
            const x = center + r * Math.cos(angle);
            const y = center + r * Math.sin(angle);
            points.push(`${x.toFixed(1)},${y.toFixed(1)}`);

            // Draw axis spoke line
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', center);
            line.setAttribute('y1', center);
            line.setAttribute('x2', center + radius * Math.cos(angle));
            line.setAttribute('y2', center + radius * Math.sin(angle));
            line.setAttribute('stroke', '#E2E8F0');
            svg.appendChild(line);

            // Draw axis label
            const labelR = radius + 24;
            const lx = center + labelR * Math.cos(angle);
            const ly = center + labelR * Math.sin(angle);
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', lx);
            text.setAttribute('y', ly + 4);
            text.setAttribute('font-size', '10');
            text.setAttribute('fill', '#4B5563');
            text.setAttribute('font-weight', '500');
            text.setAttribute('text-anchor', 'middle');
            text.textContent = d.label;
            svg.appendChild(text);
        });

        // Draw filled polygon for student's snapshot
        const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        polygon.setAttribute('points', points.join(' '));
        polygon.setAttribute('fill', 'rgba(45, 106, 79, 0.25)');
        polygon.setAttribute('stroke', '#2D6A4F');
        polygon.setAttribute('stroke-width', '2.5');
        polygon.setAttribute('stroke-linejoin', 'round');
        svg.appendChild(polygon);

        // Draw point dots
        points.forEach(pt => {
            const [px, py] = pt.split(',');
            const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            dot.setAttribute('cx', px);
            dot.setAttribute('cy', py);
            dot.setAttribute('r', '4');
            dot.setAttribute('fill', '#2D6A4F');
            dot.setAttribute('stroke', '#FFFFFF');
            dot.setAttribute('stroke-width', '1.5');
            svg.appendChild(dot);
        });
    }

    function updateTailoredRecommendations(vals) {
        // Find highest strain dimension
        let highest = dimensions[0];
        dimensions.forEach(d => {
            if (vals[d.key] > vals[highest.key]) {
                highest = d;
            }
        });

        const recContainer = document.getElementById('stress-tailored-actions');
        if (!recContainer) return;

        let recTitle = "Activate Emergency Triage";
        let recDesc = "Deadline pressure is your primary source of cognitive friction today.";
        let recAction = "window.TempoApp.navigateTo('emergency')";
        let recBtn = "Launch Triage Plan →";

        if (highest.key === 'sleepQuality') {
            recTitle = "Sleep Protection Protocol";
            recDesc = "Poor sleep is magnifying your academic anxiety. Read the guide on cognitive offloading before bed.";
            recAction = "window.TempoKnowledge.openArticle('art-3')";
            recBtn = "Read Sleep Guide (3m) →";
        } else if (highest.key === 'concentration') {
            recTitle = "Overcome Brain Fog";
            recDesc = "Your prefrontal cortex is depleted. Try the 20-20 cognitive reset technique.";
            recAction = "window.TempoKnowledge.openArticle('art-4')";
            recBtn = "Read Focus Reset →";
        } else if (highest.key === 'exhaustion' || highest.key === 'burnoutSigns') {
            recTitle = "Ask for Human Support";
            recDesc = "You are carrying high sustained exhaustion. Reaching out for an extension or advisor chat will lighten the load.";
            recAction = "window.TempoApp.navigateTo('support')";
            recBtn = "Connect with Advisor →";
        }

        recContainer.innerHTML = `
            <div class="p-5 bg-stone-50 border border-stone-200 rounded-xl space-y-2">
                <span class="text-xs font-semibold uppercase tracking-wider text-emerald-800">Primary Stress Driver: ${highest.label} (${vals[highest.key]}/10)</span>
                <h4 class="text-base font-bold text-gray-900">${recTitle}</h4>
                <p class="text-xs text-gray-600">${recDesc}</p>
                <div class="pt-2">
                    <button onclick="${recAction}" class="px-4 py-2 bg-emerald-700 text-white rounded-lg text-xs font-medium hover:bg-emerald-800 transition">
                        ${recBtn}
                    </button>
                </div>
            </div>
        `;
    }

    function saveResult() {
        const stored = {
            completedAt: 'Just now',
            dimensions: { ...currentValues },
            overallScore: Object.values(currentValues).reduce((a, b) => a + b, 0)
        };
        localStorage.setItem('tempo_last_stress', JSON.stringify(stored));
        window.TempoApp.showToast("Stress assessment saved to your profile.");
    }

    return {
        init,
        resetDefaults
    };
})();
