/**
 * Tempo Knowledge Hub ("Learn & Solve")
 * Practical, action-oriented guides filterable by acute stress states.
 */

window.TempoKnowledge = (function() {
    let articles = [];
    let currentCategory = 'all';
    let searchQuery = '';

    function init() {
        articles = window.TEMPO_DATA.articles || [];
        bindEvents();
        renderArticles();
    }

    function bindEvents() {
        // Category Pills
        document.querySelectorAll('.hub-filter-pill').forEach(pill => {
            pill.addEventListener('click', (e) => {
                document.querySelectorAll('.hub-filter-pill').forEach(p => {
                    p.className = "hub-filter-pill px-3.5 py-1.5 rounded-full text-xs font-medium bg-stone-100 text-stone-600 hover:bg-stone-200 cursor-pointer transition";
                });
                e.currentTarget.className = "hub-filter-pill px-3.5 py-1.5 rounded-full text-xs font-semibold bg-[#FF6B2C] text-white cursor-pointer transition";
                currentCategory = e.currentTarget.dataset.category;
                renderArticles();
            });
        });

        // Search Input
        const searchInput = document.getElementById('hub-search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                searchQuery = e.target.value.toLowerCase();
                renderArticles();
            });
        }

        // Close Modal
        const closeBtn = document.getElementById('btn-close-article-modal');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                document.getElementById('article-detail-modal').classList.add('hidden');
            });
        }
    }

    function renderArticles() {
        const grid = document.getElementById('hub-articles-grid');
        if (!grid) return;

        const filtered = articles.filter(a => {
            const matchesCat = currentCategory === 'all' || a.category === currentCategory;
            const matchesSearch = !searchQuery || 
                a.title.toLowerCase().includes(searchQuery) || 
                a.summary.toLowerCase().includes(searchQuery);
            return matchesCat && matchesSearch;
        });

        if (filtered.length === 0) {
            grid.innerHTML = `
                <div class="col-span-full py-12 text-center text-gray-500">
                    <p class="text-sm">No guides found matching "${searchQuery}".</p>
                    <button onclick="document.getElementById('hub-search-input').value=''; window.TempoKnowledge.init();" class="mt-2 text-xs text-[#FF6B2C] underline font-medium">Clear search filter</button>
                </div>
            `;
            return;
        }

        grid.innerHTML = filtered.map(a => `
            <div class="tempo-card p-6 flex flex-col justify-between hover:shadow-md cursor-pointer transition" onclick="window.TempoKnowledge.openArticle('${a.id}')">
                <div class="space-y-3">
                    <div class="flex items-center justify-between">
                        <span class="text-xs font-semibold text-[#B83D08] bg-[#FFE9DC] px-2.5 py-0.5 rounded-full border border-[#FFD2BA]">
                            ${a.categoryLabel}
                        </span>
                        <span class="text-xs text-gray-400 font-medium">${a.readTime}</span>
                    </div>
                    <h3 class="text-base font-bold text-[#202124] hover:text-[#FF6B2C] leading-snug">
                        ${a.title}
                    </h3>
                    <p class="text-xs text-[#6F6B68] line-clamp-3 leading-relaxed">
                        ${a.summary}
                    </p>
                </div>
                <div class="pt-4 mt-4 border-t border-gray-100 flex items-center justify-between text-xs font-semibold text-[#FF6B2C]">
                    <span>Read Guide & Action Steps</span>
                    <span>→</span>
                </div>
            </div>
        `).join('');
    }

    function openArticle(id) {
        const article = articles.find(a => a.id === id);
        if (!article) return;

        const modal = document.getElementById('article-detail-modal');
        if (!modal) return;

        document.getElementById('article-modal-category').textContent = article.categoryLabel;
        document.getElementById('article-modal-time').textContent = article.readTime;
        document.getElementById('article-modal-title').textContent = article.title;
        document.getElementById('article-modal-summary').textContent = article.summary;

        // Key Takeaways
        const takeawaysList = document.getElementById('article-modal-takeaways');
        takeawaysList.innerHTML = article.keyTakeaways.map(t => `<li class="flex items-start"><span class="text-[#FF6B2C] mr-2 font-bold">•</span><span>${t}</span></li>`).join('');

        // Action Steps
        const stepsList = document.getElementById('article-modal-steps');
        stepsList.innerHTML = article.steps.map((s, idx) => `
            <div class="flex items-start space-x-3 p-3 bg-stone-50 rounded-xl border border-stone-200">
                <span class="w-6 h-6 rounded-full bg-[#FF6B2C] text-white text-xs font-bold flex items-center justify-center shrink-0">${idx + 1}</span>
                <span class="text-xs text-gray-800 font-medium pt-0.5">${s}</span>
            </div>
        `).join('');

        // Template section (if available, e.g. extension email)
        const templateContainer = document.getElementById('article-modal-template-section');
        if (article.template) {
            templateContainer.classList.remove('hidden');
            document.getElementById('article-modal-template-code').textContent = article.template;
            document.getElementById('btn-copy-template').onclick = () => {
                navigator.clipboard.writeText(article.template);
                window.TempoApp.showToast("Email template copied to clipboard!");
            };
        } else {
            templateContainer.classList.add('hidden');
        }

        // Quote
        document.getElementById('article-modal-quote').textContent = `"${article.quote}"`;

        modal.classList.remove('hidden');
    }

    return {
        init,
        openArticle
    };
})();
