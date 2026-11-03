function renderModalContent() {
        const card = document.getElementById('tempo-learn-solve-modal-card');
        if (!card) return;

        const currentId = modalNavStack[modalNavStack.length - 1];
        const item = getItemById(currentId);
        if (!item) {
            closeModal();
            return;
        }

        const hasBack = modalNavStack.length > 1;
        const prevId = hasBack ? modalNavStack[modalNavStack.length - 2] : null;
        const prevItem = prevId ? getItemById(prevId) : null;

        // 1. Header with Back button + Badge + Close button
        let headerHTML = `
            <div class="flex items-center justify-between pb-3 border-b border-stone-100 gap-3">
                <div class="flex items-center space-x-2">
                    ${hasBack ? `
                        <button type="button" onclick="window.TempoLearnSolve.goBackModal()"
                                class="inline-flex items-center space-x-1 text-xs font-bold text-stone-500 hover:text-stone-900 transition cursor-pointer mr-1">
                            <span>←</span>
                            <span>${prevItem ? escapeHTML(prevItem.title) : 'Back'}</span>
                        </button>
                        <span class="text-stone-300">|</span>
                    ` : ''}
                    <span class="text-xs font-extrabold uppercase tracking-wider ${item.type === 'solve' ? 'text-[#FF6B2C]' : 'text-[#7E22CE]'}">
                        ${escapeHTML(item.badge)}
                    </span>
                </div>
                <button type="button" onclick="window.TempoLearnSolve.closeModal()"
                        aria-label="Close dialog"
                        class="text-stone-400 hover:text-stone-800 p-1.5 rounded-xl transition cursor-pointer text-base">
                    ✕
                </button>
            </div>
        `;

        // 2. Title & Context
        let titleContextHTML = `
            <div class="space-y-1.5 text-left">
                <div class="flex items-center space-x-2">
                    <span class="text-2xl">${item.icon}</span>
                    <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124] leading-snug">
                        ${escapeHTML(item.title)}
                    </h3>
                </div>
                ${item.shortDescription ? `
                    <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                        ${escapeHTML(item.shortDescription)}
                    </p>
                ` : ''}
            </div>
        `;

        // 3. Body Content
        let bodyHTML = '';

        // If context paragraph
        if (item.context) {
            bodyHTML += `
                <div class="p-4 rounded-2xl bg-stone-50 border border-stone-200/80 text-xs sm:text-sm text-[#474543] leading-relaxed">
                    ${escapeHTML(item.context)}
                </div>
            `;
        }

        // If general paragraphs (Learn topics)
        if (item.contentParagraphs && item.contentParagraphs.length > 0) {
            bodyHTML += `
                <div class="space-y-3 text-xs sm:text-sm text-[#474543] leading-relaxed">
                    ${item.contentParagraphs.map(p => `<p>${escapeHTML(p)}</p>`).join('')}
                </div>
            `;
        }

        // If steps
        if (item.steps && item.steps.length > 0) {
            bodyHTML += `
                <div class="space-y-3 pt-2">
                    <span class="text-xs font-extrabold uppercase tracking-wider text-stone-500">ACTION STEPS</span>
                    <div class="space-y-2.5">
                        ${item.steps.map((s, idx) => `
                            <div class="p-4 rounded-2xl border border-stone-200 bg-white space-y-1 shadow-2xs">
                                <div class="flex items-center space-x-2">
                                    <span class="w-5 h-5 rounded-full bg-[#FFE9DC] text-[#B83D08] text-[11px] font-extrabold flex items-center justify-center shrink-0">
                                        ${idx + 1}
                                    </span>
                                    <h5 class="text-xs sm:text-sm font-bold text-[#202124]">
                                        ${escapeHTML(s.heading)}
                                    </h5>
                                </div>
                                <p class="text-xs text-[#6F6B68] leading-relaxed pl-7">
                                    ${escapeHTML(s.detail)}
                                </p>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        // If case distinctions (e.g. Falling Behind, Teamwork)
        if (item.caseDistinctions && item.caseDistinctions.length > 0) {
            bodyHTML += `
                <div class="space-y-3.5 pt-2">
                    <span class="text-xs font-extrabold uppercase tracking-wider text-stone-500">DIFFERENT CONTEXTS / CASES</span>
                    <div class="space-y-3">
                        ${item.caseDistinctions.map(c => `
                            <div class="p-4 sm:p-5 rounded-2xl border border-[#FFD2BA] bg-[#FFF9F5] space-y-2.5 shadow-2xs">
                                <h5 class="text-xs sm:text-sm font-extrabold text-[#B83D08] flex items-center space-x-1.5">
                                    <span>👉</span>
                                    <span>${escapeHTML(c.caseTitle)}</span>
                                </h5>
                                <ul class="space-y-1.5 text-xs text-[#474543] pl-1">
                                    ${c.items.map(it => `
                                        <li class="flex items-start space-x-2 leading-relaxed">
                                            <span class="text-[#FF6B2C] font-bold">•</span>
                                            <span>${escapeHTML(it)}</span>
                                        </li>
                                    `).join('')}
                                </ul>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        // If descriptive list (e.g. 5 areas of stress problem)
        if (item.descriptiveList && item.descriptiveList.length > 0) {
            bodyHTML += `
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-2">
                    ${item.descriptiveList.map(dl => `
                        <div class="p-3.5 rounded-xl border border-stone-200 bg-stone-50/60 space-y-0.5">
                            <h6 class="text-xs font-bold text-[#202124]">${escapeHTML(dl.title)}</h6>
                            <p class="text-xs text-[#6F6B68] leading-relaxed">${escapeHTML(dl.detail)}</p>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        // If 4 groups (Thoughts, Emotions, Body, Behavior)
        if (item.fourGroups && item.fourGroups.length > 0) {
            bodyHTML += `
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                    ${item.fourGroups.map(grp => `
                        <div class="p-4 rounded-2xl border border-stone-200 bg-stone-50 space-y-2">
                            <h6 class="text-xs font-extrabold text-[#202124] uppercase tracking-wide">${escapeHTML(grp.name)}</h6>
                            <ul class="space-y-1 text-xs text-[#474543]">
                                ${grp.items.map(it => `
                                    <li class="flex items-center space-x-1.5">
                                        <span class="text-[#FF6B2C] font-bold">·</span>
                                        <span>${escapeHTML(it)}</span>
                                    </li>
                                `).join('')}
                            </ul>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        // If Visual Loop diagram (The stress loop)
        if (item.hasVisualLoop && item.loopNodes) {
            bodyHTML += `
                <div class="p-5 rounded-3xl border-2 border-[#FFD2BA] bg-gradient-to-br from-[#FFF9F5] to-white space-y-3.5 shadow-2xs">
                    <span class="text-[10px] font-extrabold uppercase tracking-wider text-[#FF6B2C]">VISUAL STRESS CYCLE</span>
                    <div class="flex flex-wrap items-center justify-center gap-2 text-center py-2">
                        ${item.loopNodes.map((n, i) => `
                            <div class="px-3 py-1.5 rounded-xl bg-white border border-[#FFD2BA] shadow-2xs text-xs font-bold text-[#202124] flex items-center space-x-1">
                                <span>${n.icon}</span>
                                <span>${escapeHTML(n.label)}</span>
                            </div>
                            ${i < item.loopNodes.length - 1 ? `<span class="text-[#FF6B2C] font-bold">→</span>` : `<span class="text-stone-300 font-bold">↺</span>`}
                        `).join('')}
                    </div>
                    ${item.keyTakeaway ? `
                        <div class="p-3 rounded-xl bg-white/90 border border-stone-200 text-xs text-[#474543] leading-relaxed">
                            <strong class="text-[#202124]">Key Insight:</strong> ${escapeHTML(item.keyTakeaway)}
                        </div>
                    ` : ''}
                </div>
            `;
        }

        // If Burnout dimensions
        if (item.burnoutDimensions && item.burnoutDimensions.length > 0) {
            bodyHTML += `
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-2">
                    ${item.burnoutDimensions.map(d => `
                        <div class="p-4 rounded-2xl border border-purple-200 bg-purple-50/50 space-y-1.5 text-left">
                            <div class="text-lg">${d.icon}</div>
                            <h6 class="text-xs font-bold text-[#202124]">${escapeHTML(d.name)}</h6>
                            <p class="text-[11px] text-[#6F6B68] leading-relaxed">${escapeHTML(d.detail)}</p>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        // If Non-diagnostic note
        if (item.nonDiagnosticNote) {
            bodyHTML += `
                <div class="p-3.5 rounded-xl bg-stone-50 border border-stone-200 text-xs text-stone-600 leading-relaxed italic">
                    ${escapeHTML(item.nonDiagnosticNote)}
                </div>
            `;
        }

        // If Routing options (What do I need when I'm stressed?)
        if (item.routingOptions && item.routingOptions.length > 0) {
            bodyHTML += `
                <div class="space-y-2.5 pt-2">
                    <span class="text-xs font-extrabold uppercase tracking-wider text-stone-500">FINDING YOUR NEXT STEP</span>
                    <div class="space-y-2">
                        ${item.routingOptions.map(ro => `
                            <div class="p-3.5 sm:p-4 rounded-2xl border border-stone-200 bg-white flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-2xs">
                                <div class="space-y-0.5">
                                    <h6 class="text-xs font-bold text-[#202124]">${escapeHTML(ro.condition)}</h6>
                                    <p class="text-xs text-[#6F6B68] leading-relaxed">${escapeHTML(ro.actionText)}</p>
                                </div>
                                <button type="button" onclick="window.TempoLearnSolve.handleRoutingAction('${ro.actionKey}')"
                                        class="btn-primary px-3.5 py-1.5 rounded-xl text-xs font-bold shadow-2xs shrink-0 cursor-pointer">
                                    ${escapeHTML(ro.btnLabel)} →
                                </button>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        // If Support conclusion
        if (item.supportConclusion) {
            bodyHTML += `
                <div class="p-4 rounded-2xl bg-[#EDF7F1] border border-[#CDE9DA] text-xs text-[#166545] leading-relaxed">
                    ${escapeHTML(item.supportConclusion)}
                </div>
            `;
        }

        // Embedded Reusable Tempo Tip
        if (item.tipId) {
            bodyHTML += renderTipCalloutHTML(item.tipId);
        }

        // 4. Related Links & Cross-Linking Section
        let relatedHTML = '';
        const hasRelatedLearn = item.relatedLearnIds && item.relatedLearnIds.length > 0;
        const hasRelatedSolve = item.relatedSolveIds && item.relatedSolveIds.length > 0;
        const hasRelatedTool = Boolean(item.relatedTool);
        const hasRelatedMode = Boolean(item.relatedMode);

        if (hasRelatedLearn || hasRelatedSolve || hasRelatedTool || hasRelatedMode) {
            relatedHTML += `
                <div class="pt-4 border-t border-stone-100 space-y-3">
                    <span class="text-xs font-extrabold uppercase tracking-wider text-stone-400">
                        RELATED GUIDES &amp; ACTIONS
                    </span>
                    <div class="flex flex-wrap items-center gap-2">
                        ${hasRelatedLearn ? item.relatedLearnIds.map(rid => {
                            const rItem = getItemById(rid);
                            if (!rItem) return '';
                            return `
                                <button type="button" onclick="window.TempoLearnSolve.openModal('${rItem.id}')"
                                        class="px-3 py-1.5 rounded-xl bg-purple-50 text-[#7E22CE] border border-purple-200 text-xs font-bold hover:bg-purple-100 transition cursor-pointer flex items-center space-x-1">
                                    <span>🧠</span>
                                    <span>${escapeHTML(rItem.title)} →</span>
                                </button>
                            `;
                        }).join('') : ''}

                        ${hasRelatedSolve ? item.relatedSolveIds.map(rid => {
                            const rItem = getItemById(rid);
                            if (!rItem) return '';
                            return `
                                <button type="button" onclick="window.TempoLearnSolve.openModal('${rItem.id}')"
                                        class="px-3 py-1.5 rounded-xl bg-[#FFF5EC] text-[#B83D08] border border-[#FFD2BA] text-xs font-bold hover:bg-[#FFE9DC] transition cursor-pointer flex items-center space-x-1">
                                    <span>🧩</span>
                                    <span>${escapeHTML(rItem.title)} →</span>
                                </button>
                            `;
                        }).join('') : ''}

                        ${hasRelatedTool ? `
                            <button type="button" onclick="window.TempoLearnSolve.handleToolAction('${item.relatedTool.action}')"
                                    class="px-3 py-1.5 rounded-xl bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-bold hover:bg-emerald-100 transition cursor-pointer flex items-center space-x-1">
                                <span>🛠️</span>
                                <span>${escapeHTML(item.relatedTool.label)}</span>
                            </button>
                        ` : ''}

                        ${hasRelatedMode ? `
                            <button type="button" onclick="window.TempoLearnSolve.handleModeAction('${item.relatedMode.mode}')"
                                    class="px-3 py-1.5 rounded-xl bg-[#FFE9DC] text-[#B83D08] border border-[#FFD2BA] text-xs font-bold hover:bg-[#FFD2BA] transition cursor-pointer flex items-center space-x-1">
                                <span>⚡</span>
                                <span>${escapeHTML(item.relatedMode.label)}</span>
                            </button>
                        ` : ''}
                    </div>
                </div>
            `;
        }

        // Assemble Modal Card
        card.innerHTML = `
            ${headerHTML}
            ${titleContextHTML}
            <div class="space-y-4">
                ${bodyHTML}
            </div>
            ${relatedHTML}
            <div class="pt-3 border-t border-stone-100 flex items-center justify-end">
                <button type="button" onclick="window.TempoLearnSolve.closeModal()"
                        class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer">
                    Close
                </button>
            </div>
        `;
    }

    // =========================================================================
    // 8. PUBLIC TOOL & MODE CROSS-LINK ACTIONS
    // =========================================================================