/**
 * Tempo Dedicated Learn & Solve Page Controller
 * Practical, action-oriented guides, evidence-based coping strategies,
 * searchable and filterable by broad categories and specific topic tags.
 */

window.TempoKnowledge = (function() {
    'use strict';

    let articles = [];
    let currentCategory = 'all';
    let currentTag = null;
    let searchQuery = '';
    let isTagsExpanded = false;
    const DEFAULT_VISIBLE_TAGS = 9;
    let isInitialized = false;

    // Defined Broad Categories
    const CATEGORIES = [
        { key: 'all', label: 'All Guides' },
        { key: 'urgent', label: "Can't Start" },
        { key: 'study', label: 'Study & Deadlines' },
        { key: 'focus', label: 'Focus & Brain Fog' },
        { key: 'sleep', label: 'Sleep & Worry' },
        { key: 'communication', label: 'Asking for Help' },
        { key: 'future', label: 'Myself & Future' },
        { key: 'relationships', label: 'Relationships' },
        { key: 'learn', label: 'Stress Science' }
    ];

    // Curated situations & topics tag mapping to ensure rich, accurate tag coverage
    const SITUATION_TAGS_MAP = {
        'deadline_pileup': ['Deadlines', 'Prioritization', 'Starting Small'],
        'falling_behind': ['Study Strategy', 'Catching Up', 'Prioritization'],
        'teamwork': ['Teamwork', 'Communication', 'Boundaries'],
        'grades': ['Academic Disappointment', 'Self-Compassion', 'Mindset'],
        'perfectionism_paralysis': ['Perfectionism', 'Procrastination', 'Starting Small'],
        'direction_uncertainty': ['Future Anxiety', 'Self-Discovery', 'Mindset'],
        'comparison_trap': ['Social Comparison', 'Self-Compassion', 'Mindset'],
        'identity_pressure': ['Expectations', 'Self-Worth', 'Identity'],
        'overcommitted': ['Boundaries', 'Saying No', 'Time Management'],
        'presentation_dread': ['Public Speaking', 'Breathing', 'Anxiety Reset'],
        'difficult_conversation': ['Communication', 'Conflict Resolution', 'Boundaries'],
        'roommate_friction': ['Communication', 'Roommates', 'Boundaries'],
        'loneliness': ['Campus Connection', 'Belonging', 'Peer Support'],
        'family_expectations': ['Family Pressure', 'Boundaries', 'Communication'],
        'irregular_sleep': ['Sleep Protocol', 'Circadian Rhythm', 'Evening Routine'],
        'emotional_eating': ['Habits', 'Self-Awareness', 'Physical Reset'],
        'burnout_warning': ['Burnout', 'Recovery', 'Physical Reset'],
        'what_is_stress': ['Stress Science', 'Biology', 'Mind-Body'],
        'stress_loop': ['Stress Science', 'Biology', 'Mind-Body'],
        'window_of_tolerance': ['Stress Science', 'Nervous System', 'Self-Regulation'],
        'threat_vs_challenge': ['Mindset', 'Reframing', 'Performance'],
        'academic_burnout': ['Burnout', 'Recovery', 'Academic Stress'],
        'recovery': ['Recovery', 'Rest Protocol', 'Mind-Body'],
        'protective_factors': ['Resilience', 'Wellbeing', 'Habits']
    };

    function escapeHTML(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function init() {
        loadArticles();
        bindEvents();
        renderCategories();
        renderTags();
        renderArticles();
        isInitialized = true;
    }

    function loadArticles() {
        // Ensure TempoLearnSolve.openModal() without args routes to learn
        if (window.TempoLearnSolve && !window.TempoLearnSolve.__learnPatched) {
            window.TempoLearnSolve.__learnPatched = true;
            const origOpen = window.TempoLearnSolve.openModal;
            window.TempoLearnSolve.openModal = function(id) {
                if (!id) {
                    if (window.TempoApp) {
                        window.TempoApp.navigateTo('learn');
                    }
                    return;
                }
                if (typeof origOpen === 'function') {
                    origOpen(id);
                }
            };
        }

        // 1. Base articles from TEMPO_DATA
        const base = (window.TEMPO_DATA && window.TEMPO_DATA.articles) ? [...window.TEMPO_DATA.articles] : [];

        // 2. Load situations from TempoLearnSolve if available
        let situations = [];
        if (window.TempoLearnSolve && typeof window.TempoLearnSolve.getSituations === 'function') {
            const rawSits = window.TempoLearnSolve.getSituations();
            situations = rawSits.map(s => {
                let cat = s.category;
                let catLabel = 'Study & Deadlines';
                if (cat === 'future') catLabel = 'Myself & Future';
                else if (cat === 'work') { cat = 'study'; catLabel = 'Study & Deadlines'; }
                else if (cat === 'relationships') catLabel = 'Relationships';
                else if (cat === 'life') {
                    if (s.id === 'irregular_sleep') { cat = 'sleep'; catLabel = 'Sleep & Worry'; }
                    else if (s.id === 'burnout_warning') { cat = 'urgent'; catLabel = "Can't Start"; }
                    else { cat = 'focus'; catLabel = 'Focus & Brain Fog'; }
                }

                // Map tip text if present
                let tipObj = null;
                if (s.tipId && window.TempoLearnSolve.getTips) {
                    const tips = window.TempoLearnSolve.getTips();
                    tipObj = tips[s.tipId];
                }

                return {
                    id: s.id,
                    title: s.title,
                    summary: s.shortDescription || s.context,
                    category: cat,
                    categoryLabel: catLabel,
                    readTime: s.readTime || '3 min read',
                    tags: SITUATION_TAGS_MAP[s.id] || ['Study Strategy', 'Mindset'],
                    steps: s.steps || [],
                    caseDistinctions: s.caseDistinctions || null,
                    context: s.context || '',
                    quote: tipObj ? tipObj.text : null,
                    tipTitle: tipObj ? tipObj.title : null,
                    keyTakeaways: s.keyTakeaways || (s.steps ? s.steps.map(st => typeof st === 'string' ? st : st.heading) : []),
                    relatedTool: s.relatedTool || null,
                    relatedMode: s.relatedMode || null
                };
            });
        }

        // 3. Load stress topics from TempoLearnSolve if available
        let topics = [];
        if (window.TempoLearnSolve && typeof window.TempoLearnSolve.getTopics === 'function') {
            const rawTops = window.TempoLearnSolve.getTopics();
            topics = rawTops.map(t => {
                let tipObj = null;
                if (t.tipId && window.TempoLearnSolve.getTips) {
                    const tips = window.TempoLearnSolve.getTips();
                    tipObj = tips[t.tipId];
                }

                return {
                    id: t.id,
                    title: t.title,
                    summary: t.shortDescription || (t.contentParagraphs ? t.contentParagraphs[0] : ''),
                    category: 'learn',
                    categoryLabel: 'Stress Science',
                    readTime: t.readTime || '4 min read',
                    tags: SITUATION_TAGS_MAP[t.id] || ['Stress Science', 'Biology'],
                    steps: t.steps || [],
                    contentParagraphs: t.contentParagraphs || [],
                    quote: tipObj ? tipObj.text : null,
                    tipTitle: tipObj ? tipObj.title : null,
                    keyTakeaways: t.keyTakeaways || (t.contentParagraphs ? t.contentParagraphs.slice(0, 3) : []),
                    relatedTool: t.relatedTool || null,
                    relatedMode: t.relatedMode || null
                };
            });
        }

        // Combine into unified articles catalog without duplicate IDs
        const combined = [...base];
        [...situations, ...topics].forEach(item => {
            if (!combined.some(a => a.id === item.id)) {
                combined.push(item);
            }
        });

        articles = combined;
    }

    function bindEvents() {
        // Search Input
        const searchInput = document.getElementById('hub-search-input');
        const clearSearchBtn = document.getElementById('btn-clear-hub-search');

        if (searchInput && !searchInput.dataset.bound) {
            searchInput.dataset.bound = 'true';
            searchInput.addEventListener('input', (e) => {
                searchQuery = e.target.value.trim().toLowerCase();
                if (clearSearchBtn) {
                    if (searchQuery.length > 0) {
                        clearSearchBtn.classList.remove('hidden');
                    } else {
                        clearSearchBtn.classList.add('hidden');
                    }
                }
                renderArticles();
                renderTags();
                renderActiveFiltersBar();
            });

            if (clearSearchBtn) {
                clearSearchBtn.addEventListener('click', () => {
                    searchInput.value = '';
                    searchQuery = '';
                    clearSearchBtn.classList.add('hidden');
                    renderArticles();
                    renderTags();
                    renderActiveFiltersBar();
                    searchInput.focus();
                });
            }
        }

        // Close Modal Events
        const modal = document.getElementById('article-detail-modal');
        const closeBtn = document.getElementById('btn-close-article-modal');
        if (closeBtn && !closeBtn.dataset.bound) {
            closeBtn.dataset.bound = 'true';
            closeBtn.addEventListener('click', closeModal);
        }

        if (modal && !modal.dataset.bound) {
            modal.dataset.bound = 'true';
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    closeModal();
                }
            });
        }

        // Keyboard Escape listener
        if (!window.__tempoKnowledgeEscBound) {
            window.__tempoKnowledgeEscBound = true;
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    const m = document.getElementById('article-detail-modal');
                    if (m && !m.classList.contains('hidden')) {
                        closeModal();
                    }
                }
            });
        }
    }

    function closeModal() {
        const modal = document.getElementById('article-detail-modal');
        if (modal) {
            modal.classList.add('hidden');
            document.body.classList.remove('overflow-hidden');
        }
    }

    function renderCategories() {
        const container = document.getElementById('hub-categories-container');
        if (!container) return;

        container.innerHTML = CATEGORIES.map(cat => {
            const isSelected = currentCategory === cat.key;
            const btnClass = isSelected
                ? "hub-filter-pill px-4 py-2 rounded-full text-xs font-bold bg-[#FF6B2C] text-white shadow-xs cursor-pointer transition transform active:scale-95"
                : "hub-filter-pill px-4 py-2 rounded-full text-xs font-semibold bg-white text-[#6F6B68] hover:text-[#202124] hover:bg-[#F8F6F4] border border-[#EAE4DF] cursor-pointer transition transform active:scale-95";

            // Count for category
            const count = cat.key === 'all'
                ? articles.length
                : articles.filter(a => a.category === cat.key).length;

            return `
                <button type="button" 
                        data-category="${cat.key}"
                        onclick="window.TempoKnowledge.selectCategory('${cat.key}')"
                        class="${btnClass}">
                    <span>${escapeHTML(cat.label)}</span>
                    <span class="ml-1 text-[11px] opacity-80">(${count})</span>
                </button>
            `;
        }).join('');

        // Update total counter
        const countEl = document.getElementById('learn-total-count');
        if (countEl) {
            countEl.textContent = `${articles.length} guides available`;
        }
    }

    function selectCategory(categoryKey) {
        currentCategory = categoryKey;
        renderCategories();
        renderTags();
        renderArticles();
        renderActiveFiltersBar();
    }

    function renderTags() {
        const container = document.getElementById('hub-tags-container');
        const headerControl = document.getElementById('hub-tags-header-control');
        if (!container) return;

        // Collect tag frequencies deterministically for current category
        const relevantArticles = currentCategory === 'all'
            ? articles
            : articles.filter(a => a.category === currentCategory);

        const tagCounts = new Map();
        relevantArticles.forEach(a => {
            if (Array.isArray(a.tags)) {
                a.tags.forEach(t => {
                    tagCounts.set(t, (tagCounts.get(t) || 0) + 1);
                });
            }
        });

        // Also bring in global tags if category has very few
        if (tagCounts.size < 4) {
            articles.forEach(a => {
                if (Array.isArray(a.tags)) {
                    a.tags.forEach(t => {
                        if (!tagCounts.has(t)) {
                            tagCounts.set(t, 1);
                        }
                    });
                }
            });
        }

        // Deterministic sort: frequency descending, then alphabetical for ties
        const allTags = Array.from(tagCounts.keys()).sort((a, b) => {
            const countDiff = tagCounts.get(b) - tagCounts.get(a);
            if (countDiff !== 0) return countDiff;
            return a.localeCompare(b);
        });

        const totalTagsCount = allTags.length;

        if (totalTagsCount === 0) {
            container.innerHTML = `<span class="text-xs text-[#A09D9A]">No tags available</span>`;
            if (headerControl) headerControl.innerHTML = '';
            return;
        }

        const hasOverflow = totalTagsCount > DEFAULT_VISIBLE_TAGS;
        let visibleTags = [];

        if (isTagsExpanded || !hasOverflow) {
            visibleTags = allTags;
        } else {
            visibleTags = allTags.slice(0, DEFAULT_VISIBLE_TAGS);
            // Invariant: if a tag is selected and not in top slice, include it so user can see it!
            if (currentTag && !visibleTags.includes(currentTag)) {
                visibleTags.push(currentTag);
            }
        }

        // Render header control (Show all / Show less)
        if (headerControl) {
            if (hasOverflow) {
                const label = isTagsExpanded ? 'Show less ▴' : `Show all (${totalTagsCount}) ▾`;
                headerControl.innerHTML = `
                    <button type="button" 
                            id="btn-toggle-tags-header"
                            onclick="window.TempoKnowledge.toggleTagsExpanded()" 
                            class="text-xs font-semibold text-[#DF9F82] hover:text-[#C68567] hover:underline transition cursor-pointer flex items-center space-x-1 focus:outline-none focus:ring-1 focus:ring-[#DF9F82]/40 rounded px-1.5 py-0.5">
                        <span>${label}</span>
                    </button>
                `;
            } else {
                headerControl.innerHTML = '';
            }
        }

        // Render tag pills
        let tagsHTML = visibleTags.map(tag => {
            const isSelected = currentTag === tag;
            const tagClass = isSelected
                ? "px-3 py-1 rounded-full text-xs font-semibold bg-[#8EA391] text-white border border-[#7A907E] shadow-2xs cursor-pointer transition flex items-center focus:outline-none focus:ring-2 focus:ring-[#8EA391]/40 active:scale-95"
                : "px-3 py-1 rounded-full text-xs font-medium bg-white text-[#55524E] hover:border-[#8CA5B4] hover:bg-[#F2F6F8] hover:text-[#2E4857] border border-[#EAE4DF] cursor-pointer transition flex items-center focus:outline-none focus:ring-2 focus:ring-[#8CA5B4]/30 active:scale-95";

            const hashColor = isSelected ? "text-white/80" : "text-[#8CA5B4]";

            return `
                <button type="button" 
                        data-tag="${escapeHTML(tag)}"
                        onclick="window.TempoKnowledge.selectTag('${escapeHTML(tag)}')" 
                        aria-pressed="${isSelected}"
                        class="${tagClass}">
                    <span class="${hashColor} font-semibold mr-0.5 select-none">#</span>
                    <span>${escapeHTML(tag)}</span>
                    ${isSelected ? `<span class="ml-1.5 text-[10px] text-white/90 hover:text-white font-bold" title="Remove filter">✕</span>` : ''}
                </button>
            `;
        }).join('');

        // If has overflow, add inline button at end of list
        if (hasOverflow) {
            const hiddenCount = totalTagsCount - visibleTags.length;
            const inlineBtnText = isTagsExpanded 
                ? 'Show less ▴' 
                : (hiddenCount > 0 ? `+${hiddenCount} more ▾` : 'Show all ▾');

            tagsHTML += `
                <button type="button" 
                        id="btn-toggle-tags-inline"
                        onclick="window.TempoKnowledge.toggleTagsExpanded()" 
                        class="px-3 py-1 rounded-full text-xs font-semibold text-[#B87556] bg-[#FCF6F2] hover:bg-[#F7ECE4] border border-[#ECD3C6] hover:border-[#DF9F82] transition cursor-pointer flex items-center space-x-1 shadow-2xs focus:outline-none focus:ring-1 focus:ring-[#DF9F82]">
                    <span>${inlineBtnText}</span>
                </button>
            `;
        }

        container.innerHTML = tagsHTML;
    }

    function toggleTagsExpanded() {
        isTagsExpanded = !isTagsExpanded;
        renderTags();
    }

    function selectTag(tag) {
        if (currentTag === tag) {
            currentTag = null; // Toggle off
        } else {
            currentTag = tag;
        }
        renderTags();
        renderArticles();
        renderActiveFiltersBar();
    }

    function renderActiveFiltersBar() {
        const bar = document.getElementById('hub-active-filters-bar');
        const chips = document.getElementById('hub-active-filters-chips');
        if (!bar || !chips) return;

        const hasCategoryFilter = currentCategory !== 'all';
        const hasTagFilter = !!currentTag;
        const hasSearchFilter = searchQuery.length > 0;

        if (!hasCategoryFilter && !hasTagFilter && !hasSearchFilter) {
            bar.classList.add('hidden');
            return;
        }

        bar.classList.remove('hidden');

        let chipsHTML = `<span class="text-xs font-bold text-[#736F68] mr-1">Active filters:</span>`;

        if (hasCategoryFilter) {
            const catObj = CATEGORIES.find(c => c.key === currentCategory);
            const label = catObj ? catObj.label : currentCategory;
            chipsHTML += `
                <span class="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-semibold bg-[#FFE9DC] text-[#B83D08] border border-[#FFD2BA]">
                    <span>Category: ${escapeHTML(label)}</span>
                    <button type="button" onclick="window.TempoKnowledge.selectCategory('all')" class="ml-1.5 font-bold hover:text-black">✕</button>
                </span>
            `;
        }

        if (hasTagFilter) {
            chipsHTML += `
                <span class="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-semibold bg-[#8EA391] text-white border border-[#7A907E] shadow-2xs">
                    <span class="text-white/80 font-semibold mr-0.5 select-none">#</span>
                    <span>Tag: ${escapeHTML(currentTag)}</span>
                    <button type="button" onclick="window.TempoKnowledge.selectTag('${escapeHTML(currentTag)}')" class="ml-2 font-bold text-white/90 hover:text-white cursor-pointer" title="Remove tag filter">✕</button>
                </span>
            `;
        }

        if (hasSearchFilter) {
            chipsHTML += `
                <span class="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-semibold bg-stone-100 text-[#202124] border border-stone-300">
                    <span>Search: "${escapeHTML(searchQuery)}"</span>
                    <button type="button" onclick="const i=document.getElementById('hub-search-input'); if(i){ i.value=''; } window.TempoKnowledge.clearSearch();" class="ml-1.5 font-bold hover:text-black">✕</button>
                </span>
            `;
        }

        chips.innerHTML = chipsHTML;
    }

    function clearSearch() {
        searchQuery = '';
        const searchInput = document.getElementById('hub-search-input');
        if (searchInput) searchInput.value = '';
        const clearBtn = document.getElementById('btn-clear-hub-search');
        if (clearBtn) clearBtn.classList.add('hidden');
        renderArticles();
        renderTags();
        renderActiveFiltersBar();
    }

    function clearAllFilters() {
        currentCategory = 'all';
        currentTag = null;
        clearSearch();
        renderCategories();
        renderTags();
        renderArticles();
        renderActiveFiltersBar();
    }

    function renderArticles() {
        const grid = document.getElementById('hub-articles-grid');
        const emptyState = document.getElementById('hub-empty-state');
        const emptyDesc = document.getElementById('hub-empty-desc');
        if (!grid) return;

        const filtered = articles.filter(a => {
            // 1. Category check
            const matchesCat = currentCategory === 'all' || a.category === currentCategory;

            // 2. Tag check
            const matchesTag = !currentTag || (Array.isArray(a.tags) && a.tags.includes(currentTag));

            // 3. Search query check (title, summary, tags, categoryLabel)
            const matchesSearch = !searchQuery ||
                (a.title && a.title.toLowerCase().includes(searchQuery)) ||
                (a.summary && a.summary.toLowerCase().includes(searchQuery)) ||
                (a.categoryLabel && a.categoryLabel.toLowerCase().includes(searchQuery)) ||
                (Array.isArray(a.tags) && a.tags.some(t => t.toLowerCase().includes(searchQuery)));

            return matchesCat && matchesTag && matchesSearch;
        });

        if (filtered.length === 0) {
            grid.innerHTML = '';
            if (emptyState) {
                emptyState.classList.remove('hidden');
                if (emptyDesc) {
                    if (searchQuery) {
                        emptyDesc.textContent = `No guides found matching "${searchQuery}". Try searching with different keywords or reset your filters.`;
                    } else if (currentTag) {
                        emptyDesc.textContent = `No guides found tagged with #${currentTag} in this category.`;
                    } else {
                        emptyDesc.textContent = `No guides currently found for this category.`;
                    }
                }
            }
            return;
        }

        if (emptyState) {
            emptyState.classList.add('hidden');
        }

        grid.innerHTML = filtered.map(a => {
            const tagsHTML = Array.isArray(a.tags) && a.tags.length > 0
                ? `<div class="flex flex-wrap gap-1.5 pt-1">
                    ${a.tags.slice(0, 3).map(t => {
                        const isTagSelected = currentTag === t;
                        const pillClass = isTagSelected
                            ? "text-[11px] font-semibold px-2 py-0.5 rounded-md bg-[#8EA391] text-white border border-[#7A907E] shadow-2xs transition cursor-pointer"
                            : "text-[11px] font-medium px-2 py-0.5 rounded-md bg-[#F8F6F4] text-[#55524E] hover:border-[#8CA5B4] hover:bg-[#F2F6F8] hover:text-[#2E4857] border border-[#EAE4DF] transition cursor-pointer";
                        const hashColor = isTagSelected ? "text-white/80" : "text-[#8CA5B4]";
                        return `
                            <span onclick="event.stopPropagation(); window.TempoKnowledge.selectTag('${escapeHTML(t)}');" 
                                  class="${pillClass}"
                                  title="Filter by #${escapeHTML(t)}">
                                <span class="${hashColor} font-semibold mr-0.5 select-none">#</span>${escapeHTML(t)}
                            </span>
                        `;
                    }).join('')}
                   </div>`
                : '';

            return `
                <div class="bg-white border border-[#EAE4DF] hover:border-[#FFD2BA] hover:shadow-md rounded-2xl p-5 sm:p-6 flex flex-col justify-between transition-all duration-200 group cursor-pointer" 
                     onclick="window.TempoKnowledge.openArticle('${a.id}')">
                    <div class="space-y-3">
                        <div class="flex items-center justify-between gap-2">
                            <span class="text-xs font-bold text-[#B83D08] bg-[#FFE9DC] px-2.5 py-0.5 rounded-full border border-[#FFD2BA]">
                                ${escapeHTML(a.categoryLabel)}
                            </span>
                            <span class="text-xs text-[#8A8682] font-medium shrink-0">⏱️ ${escapeHTML(a.readTime)}</span>
                        </div>
                        <h3 class="font-heading text-base sm:text-lg font-bold text-[#202124] group-hover:text-[#FF6B2C] leading-snug transition-colors line-clamp-2">
                            ${escapeHTML(a.title)}
                        </h3>
                        <p class="text-xs sm:text-sm text-[#6F6B68] line-clamp-3 leading-relaxed">
                            ${escapeHTML(a.summary)}
                        </p>
                        ${tagsHTML}
                    </div>
                    <div class="pt-4 mt-4 border-t border-[#F0ECE9] flex items-center justify-between text-xs font-bold text-[#FF6B2C] group-hover:text-[#E05316] transition-colors">
                        <span>Read Guide & Action Steps</span>
                        <span class="transform group-hover:translate-x-1 transition-transform">→</span>
                    </div>
                </div>
            `;
        }).join('');
    }

    function openArticle(id) {
        if (!articles || articles.length === 0) {
            loadArticles();
        }

        const article = articles.find(a => a.id === id);
        if (!article) return;

        const modal = document.getElementById('article-detail-modal');
        if (!modal) return;

        // Category & Meta
        const catEl = document.getElementById('article-modal-category');
        if (catEl) catEl.textContent = article.categoryLabel;

        const timeEl = document.getElementById('article-modal-time');
        if (timeEl) timeEl.textContent = article.readTime || '3 min read';

        // Tags
        const tagsContainer = document.getElementById('article-modal-tags');
        if (tagsContainer) {
            if (Array.isArray(article.tags) && article.tags.length > 0) {
                tagsContainer.innerHTML = article.tags.map(t => {
                    const isTagSelected = currentTag === t;
                    const pillClass = isTagSelected
                        ? "text-[10px] font-semibold px-2 py-0.5 rounded-md bg-[#8EA391] text-white border border-[#7A907E]"
                        : "text-[10px] font-medium px-2 py-0.5 rounded-md bg-[#F8F6F4] text-[#55524E] border border-[#EAE4DF]";
                    const hashClass = isTagSelected ? "text-white/80" : "text-[#8CA5B4]";
                    return `<span class="${pillClass}"><span class="${hashClass} font-semibold mr-0.5 select-none">#</span>${escapeHTML(t)}</span>`;
                }).join('');
            } else {
                tagsContainer.innerHTML = '';
            }
        }

        // Title & Summary
        const titleEl = document.getElementById('article-modal-title');
        if (titleEl) titleEl.textContent = article.title;

        const summaryEl = document.getElementById('article-modal-summary');
        if (summaryEl) {
            summaryEl.textContent = article.summary || article.context || '';
        }

        // Content Paragraphs (for learn topics)
        const parasContainer = document.getElementById('article-modal-paragraphs');
        if (parasContainer) {
            if (article.contentParagraphs && article.contentParagraphs.length > 0) {
                parasContainer.classList.remove('hidden');
                parasContainer.innerHTML = article.contentParagraphs.map(p => `
                    <p class="leading-relaxed">${escapeHTML(p)}</p>
                `).join('');
            } else {
                parasContainer.classList.add('hidden');
                parasContainer.innerHTML = '';
            }
        }

        // Case Distinctions (for situations with Case A / Case B)
        const casesSection = document.getElementById('article-modal-cases-section');
        if (casesSection) {
            if (article.caseDistinctions && article.caseDistinctions.length > 0) {
                casesSection.classList.remove('hidden');
                casesSection.innerHTML = article.caseDistinctions.map(c => `
                    <div class="p-4 rounded-2xl bg-[#FFF9F4] border border-[#FFD2BA] space-y-2">
                        <h5 class="text-xs font-bold text-[#B83D08] uppercase tracking-wider">${escapeHTML(c.caseTitle)}</h5>
                        <ul class="text-xs sm:text-sm text-[#474543] space-y-1.5">
                            ${c.items.map(it => `<li class="flex items-start"><span class="text-[#FF6B2C] mr-2 font-bold">•</span><span>${escapeHTML(it)}</span></li>`).join('')}
                        </ul>
                    </div>
                `).join('');
            } else {
                casesSection.classList.add('hidden');
                casesSection.innerHTML = '';
            }
        }

        // Key Takeaways
        const takeawaysContainer = document.getElementById('article-modal-takeaways-container');
        const takeawaysList = document.getElementById('article-modal-takeaways');
        if (takeawaysList && takeawaysContainer) {
            if (article.keyTakeaways && article.keyTakeaways.length > 0) {
                takeawaysContainer.classList.remove('hidden');
                takeawaysList.innerHTML = article.keyTakeaways.map(t => `
                    <li class="flex items-start">
                        <span class="text-[#FF6B2C] mr-2 font-bold text-sm shrink-0">•</span>
                        <span>${escapeHTML(t)}</span>
                    </li>
                `).join('');
            } else {
                takeawaysContainer.classList.add('hidden');
            }
        }

        // Action Steps
        const stepsContainer = document.getElementById('article-modal-steps-container');
        const stepsList = document.getElementById('article-modal-steps');
        if (stepsList && stepsContainer) {
            if (article.steps && article.steps.length > 0) {
                stepsContainer.classList.remove('hidden');
                stepsList.innerHTML = article.steps.map((s, idx) => {
                    const isObj = typeof s === 'object' && s !== null;
                    const heading = isObj ? s.heading : s;
                    const detail = isObj ? s.detail : null;

                    return `
                        <div class="flex items-start space-x-3 p-3.5 bg-stone-50 rounded-2xl border border-stone-200/80">
                            <span class="w-6 h-6 rounded-full bg-[#FFE9DC] text-[#B83D08] text-xs font-extrabold flex items-center justify-center shrink-0 mt-0.5">
                                ${idx + 1}
                            </span>
                            <div class="text-xs sm:text-sm text-gray-800 space-y-0.5">
                                <div class="font-bold text-[#202124]">${escapeHTML(heading)}</div>
                                ${detail ? `<p class="text-xs text-[#6F6B68] leading-relaxed">${escapeHTML(detail)}</p>` : ''}
                            </div>
                        </div>
                    `;
                }).join('');
            } else {
                stepsContainer.classList.add('hidden');
            }
        }

        // Template section (if available, e.g. extension email)
        const templateContainer = document.getElementById('article-modal-template-section');
        if (templateContainer) {
            if (article.template) {
                templateContainer.classList.remove('hidden');
                document.getElementById('article-modal-template-code').textContent = article.template;
                const copyBtn = document.getElementById('btn-copy-template');
                if (copyBtn) {
                    copyBtn.onclick = () => {
                        navigator.clipboard.writeText(article.template);
                        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                            window.TempoApp.showToast("Email template copied to clipboard!");
                        }
                    };
                }
            } else {
                templateContainer.classList.add('hidden');
            }
        }

        // Quote / Tip Callout
        const quoteContainer = document.getElementById('article-modal-quote-container');
        const quoteEl = document.getElementById('article-modal-quote');
        if (quoteContainer && quoteEl) {
            if (article.quote) {
                quoteContainer.classList.remove('hidden');
                quoteEl.innerHTML = article.tipTitle 
                    ? `<strong class="text-[#202124] not-italic block mb-0.5">💡 ${escapeHTML(article.tipTitle)}</strong>"${escapeHTML(article.quote)}"`
                    : `"${escapeHTML(article.quote)}"`;
            } else {
                quoteContainer.classList.add('hidden');
            }
        }

        // Related Tools & Modes Action Buttons
        const toolActionsContainer = document.getElementById('article-modal-tool-actions');
        if (toolActionsContainer) {
            let actionsHTML = '';

            // If article has explicit relatedTool
            if (article.relatedTool) {
                actionsHTML += `
                    <button type="button" 
                            onclick="window.TempoKnowledge.handleToolAction('${article.relatedTool.action || article.relatedTool.id}')"
                            class="px-4 py-2 rounded-full bg-[#FF6B2C] hover:bg-[#E55A1F] text-white font-bold text-xs shadow-xs transition cursor-pointer">
                        ${escapeHTML(article.relatedTool.label || 'Open Tool')} →
                    </button>
                `;
            } else if (article.id === 'art-1') {
                actionsHTML += `
                    <button type="button" 
                            onclick="window.TempoKnowledge.handleToolAction('focus_zone')"
                            class="px-4 py-2 rounded-full bg-[#FF6B2C] hover:bg-[#E55A1F] text-white font-bold text-xs shadow-xs transition cursor-pointer">
                        Start 5-Minute Focus Sprint →
                    </button>
                `;
            } else if (article.id === 'art-2') {
                actionsHTML += `
                    <button type="button" 
                            onclick="window.TempoKnowledge.handleToolAction('support_page')"
                            class="px-4 py-2 rounded-full bg-[#FF6B2C] hover:bg-[#E55A1F] text-white font-bold text-xs shadow-xs transition cursor-pointer">
                        Connect with Wellbeing Advisor →
                    </button>
                `;
            } else if (article.id === 'art-3') {
                actionsHTML += `
                    <button type="button" 
                            onclick="window.TempoKnowledge.handleToolAction('breathing')"
                            class="px-4 py-2 rounded-full bg-[#FF6B2C] hover:bg-[#E55A1F] text-white font-bold text-xs shadow-xs transition cursor-pointer">
                        Start 4-7-8 Breathing Cadence →
                    </button>
                `;
            } else if (article.id === 'art-4') {
                actionsHTML += `
                    <button type="button" 
                            onclick="window.TempoKnowledge.handleToolAction('quick_relief')"
                            class="px-4 py-2 rounded-full bg-[#FF6B2C] hover:bg-[#E55A1F] text-white font-bold text-xs shadow-xs transition cursor-pointer">
                        Try 20-20 Sensory Reset →
                    </button>
                `;
            } else if (article.id === 'art-5') {
                actionsHTML += `
                    <button type="button" 
                            onclick="window.TempoKnowledge.handleToolAction('wplan')"
                            class="px-4 py-2 rounded-full bg-[#FF6B2C] hover:bg-[#E55A1F] text-white font-bold text-xs shadow-xs transition cursor-pointer">
                        Draft in Working Plan →
                    </button>
                `;
            }

            toolActionsContainer.innerHTML = actionsHTML;
        }

        modal.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');
    }

    function handleToolAction(toolAction) {
        closeModal();
        if (toolAction === 'focus_zone') {
            if (window.TempoFocusZone && typeof window.TempoFocusZone.openQuickEntry === 'function') {
                window.TempoFocusZone.openQuickEntry();
            } else if (window.TempoApp) {
                window.TempoApp.navigateTo('plan-workspace');
            }
        } else if (toolAction === 'breathing') {
            if (window.TempoStressRelief && typeof window.TempoStressRelief.openModal === 'function') {
                window.TempoStressRelief.openModal();
            } else if (window.TempoEmergencySupport) {
                window.TempoEmergencySupport.openModal();
            }
        } else if (toolAction === 'quick_relief') {
            if (window.TempoStressRelief && typeof window.TempoStressRelief.openModal === 'function') {
                window.TempoStressRelief.openModal();
            } else if (window.TempoTools && typeof window.TempoTools.openBreak === 'function') {
                window.TempoTools.openBreak();
            }
        } else if (toolAction === 'support_page') {
            if (window.TempoApp) {
                window.TempoApp.navigateTo('support');
            }
        } else if (toolAction === 'wplan' || toolAction === 'plan-workspace') {
            if (window.TempoApp) {
                window.TempoApp.navigateTo('plan-workspace');
            }
        } else if (toolAction === 'strack') {
            if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') {
                window.TempoMode.openStrack('open');
            }
        }
    }

    // Connect with TempoLearnSolve openModal if called externally
    if (window.TempoLearnSolve) {
        const origOpen = window.TempoLearnSolve.openModal;
        window.TempoLearnSolve.openModal = function(id) {
            if (!id) {
                if (window.TempoApp) {
                    window.TempoApp.navigateTo('learn');
                }
                return;
            }
            if (typeof origOpen === 'function') {
                origOpen(id);
            }
        };
    }

    return {
        init,
        openArticle,
        selectCategory,
        selectTag,
        toggleTagsExpanded,
        isTagsExpanded: () => isTagsExpanded,
        clearSearch,
        clearAllFilters,
        closeModal,
        handleToolAction,
        getArticles: () => [...articles],
        getCurrentCategory: () => currentCategory,
        getCurrentTag: () => currentTag
    };
})();
