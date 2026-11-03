import sys

sys.stdout.reconfigure(encoding='utf-8')

file_path = 'i18n.js'

with open(file_path, 'rb') as f:
    raw = f.read()

initial_crlf = raw.count(b'\r\n')
initial_lone_lf = raw.count(b'\n') - initial_crlf
print(f"i18n.js initial CRLF: {initial_crlf}, lone LF: {initial_lone_lf}")

text = raw.decode('utf-8')

# Ensure DEFAULT_LANG and SUPPORTED_LANGS reflect Vietnamese sole UI language
text = text.replace(
    "const SUPPORTED_LANGS = ['vi', 'en'];",
    "const SUPPORTED_LANGS = ['vi'];"
)

# Ensure initLanguage and setLanguage always force 'vi'
init_lang_target = """    function initLanguage() {
        try {
            const saved = localStorage.getItem('tempo_language');
            if (saved && SUPPORTED_LANGS.includes(saved)) {
                currentLang = saved;
            } else {
                // Vietnamese-first: first visit defaults to 'vi'
                currentLang = DEFAULT_LANG;
            }
        } catch (e) {
            currentLang = DEFAULT_LANG;
        }
    }"""

init_lang_replacement = """    function initLanguage() {
        // Vietnamese is the sole UI language across Tempo
        currentLang = 'vi';
        try {
            localStorage.setItem('tempo_language', 'vi');
            localStorage.setItem('tempo_auth_lang', 'vi');
        } catch (e) {}
    }"""

text = text.replace(init_lang_target, init_lang_replacement)

# Update setLanguage to always enforce 'vi' and ignore switching
set_lang_target = """    function setLanguage(lang) {
        if (!SUPPORTED_LANGS.includes(lang)) return;
        currentLang = lang;
        try {
            localStorage.setItem('tempo_language', lang);
            localStorage.setItem('tempo_auth_lang', lang);
        } catch (e) {}"""

set_lang_replacement = """    function setLanguage(lang) {
        // Vietnamese is the sole UI language
        currentLang = 'vi';
        try {
            localStorage.setItem('tempo_language', 'vi');
            localStorage.setItem('tempo_auth_lang', 'vi');
        } catch (e) {}"""

text = text.replace(set_lang_target, set_lang_replacement)

# Update updateNavbarSwitcher to hide the language switcher completely
navbar_switcher_target = """    function updateNavbarSwitcher() {
        const btnLabel = document.getElementById('nav-current-lang-label');
        if (btnLabel) {
            btnLabel.textContent = currentLang.toUpperCase();
        }

        const flagImg = document.getElementById('nav-current-lang-flag');
        if (flagImg) {
            if (currentLang === 'vi') {
                flagImg.src = 'assets/flag-vn.png';
                flagImg.alt = 'Tiếng Việt';
            } else {
                flagImg.src = 'assets/flag-us.png';
                flagImg.alt = 'English';
            }
        }

        const checkVi = document.getElementById('lang-check-vi');
        const checkEn = document.getElementById('lang-check-en');
        if (checkVi && checkEn) {
            if (currentLang === 'vi') {
                checkVi.classList.remove('hidden');
                checkEn.classList.add('hidden');
            } else {
                checkVi.classList.add('hidden');
                checkEn.classList.remove('hidden');
            }
        }
    }"""

navbar_switcher_replacement = """    function updateNavbarSwitcher() {
        // Requirement 9: Do not introduce a language switcher or English/Vietnamese toggle. Vietnamese is the sole UI language.
        const wrapper = document.getElementById('nav-language-wrapper');
        if (wrapper) {
            wrapper.style.display = 'none';
            wrapper.classList.add('hidden');
        }
        const dropdown = document.getElementById('nav-language-dropdown');
        if (dropdown) {
            dropdown.style.display = 'none';
            dropdown.classList.add('hidden');
        }
    }"""

text = text.replace(navbar_switcher_target, navbar_switcher_replacement)

# Update updateStaticHtml to cover all static elements in Vietnamese
static_html_target = """    function updateStaticHtml() {
        // Nav tabs
        const navTabToday = document.getElementById('nav-tab-today');
        if (navTabToday) navTabToday.textContent = t('nav.home');
        const navTabPosts = document.getElementById('nav-tab-community');
        if (navTabPosts) navTabPosts.textContent = t('nav.tempoPosts');
        const navTabVolunteer = document.getElementById('nav-tab-volunteer');
        if (navTabVolunteer) navTabVolunteer.textContent = t('nav.peerVolunteer');
        const navTabAdmin = document.getElementById('nav-tab-admin');
        if (navTabAdmin) navTabAdmin.textContent = t('nav.advisorDesk');

        // Global search placeholder
        const searchInput = document.getElementById('global-search-input');
        if (searchInput) searchInput.placeholder = t('common.searchPlaceholder');

        // Auth buttons in header & avatar dropdown items
        const btnSignIn = document.getElementById('btn-header-signin');
        if (btnSignIn) btnSignIn.textContent = t('common.signIn');
        const btnRegister = document.getElementById('btn-header-register');
        if (btnRegister) btnRegister.textContent = t('common.register');
        const labelMessages = document.getElementById('label-menu-messages');
        if (labelMessages) labelMessages.textContent = t('common.directMessages');
        const labelSaved = document.getElementById('label-menu-saved');
        if (labelSaved) labelSaved.textContent = t('common.saved');
        const labelLibrary = document.getElementById('label-menu-library');
        if (labelLibrary) labelLibrary.textContent = t('common.myLibrary');
        const labelAccount = document.getElementById('label-menu-account');
        if (labelAccount) labelAccount.textContent = t('common.account');
        const labelMyData = document.getElementById('label-menu-my-data');
        if (labelMyData) labelMyData.textContent = t('common.myData');
        const labelSettings = document.getElementById('label-menu-settings');
        if (labelSettings) labelSettings.textContent = t('common.settings');
        const labelSignOut = document.getElementById('label-menu-signout');
        if (labelSignOut) {
            labelSignOut.textContent = t('common.signOut');
        } else {
            const btnSignOut = document.getElementById('btn-header-signout');
            if (btnSignOut) btnSignOut.textContent = t('common.signOut');
        }

        // Footer
        const footerSos = document.querySelector('footer button[onclick*="openSOS"]');
        if (footerSos) footerSos.textContent = t('sos.title');
    }"""

static_html_replacement = """    function updateStaticHtml() {
        // Nav central links
        const navAbout = document.getElementById('nav-link-what-is-tempo');
        if (navAbout) navAbout.textContent = 'Giới thiệu';
        const navCheck = document.getElementById('nav-link-check');
        if (navCheck) navCheck.textContent = 'Tự kiểm tra';
        const navPlan = document.getElementById('nav-link-plan');
        if (navPlan) navPlan.textContent = 'Kế hoạch';
        const navCommunity = document.getElementById('nav-link-community');
        if (navCommunity) navCommunity.textContent = 'Cộng đồng';

        // Nav tabs
        const navTabToday = document.getElementById('nav-tab-today');
        if (navTabToday) navTabToday.textContent = 'Trang chủ';
        const navTabPosts = document.getElementById('nav-tab-community');
        if (navTabPosts) navTabPosts.textContent = 'Cộng đồng';
        const navTabVolunteer = document.getElementById('nav-tab-volunteer');
        if (navTabVolunteer) navTabVolunteer.textContent = 'Hỗ trợ tình nguyện';
        const navTabAdmin = document.getElementById('nav-tab-admin');
        if (navTabAdmin) navTabAdmin.textContent = 'Bàn Cố vấn';

        // Global search placeholder & button
        const searchInput = document.getElementById('global-search-input');
        if (searchInput) searchInput.placeholder = 'Tìm kiếm trên Tempo...';
        const searchBtn = document.getElementById('btn-header-search-toggle');
        if (searchBtn) searchBtn.title = 'Tìm kiếm trên Tempo';

        // Auth buttons in header & avatar dropdown items
        const btnSignIn = document.getElementById('btn-header-signin');
        if (btnSignIn) btnSignIn.textContent = 'Đăng nhập';
        const btnRegister = document.getElementById('btn-header-register');
        if (btnRegister) btnRegister.textContent = 'Đăng ký';
        const labelMessages = document.getElementById('label-menu-messages');
        if (labelMessages) labelMessages.textContent = 'Tin nhắn trực tiếp';
        const labelSaved = document.getElementById('label-menu-saved');
        if (labelSaved) labelSaved.textContent = 'Đã lưu';
        const labelLibrary = document.getElementById('label-menu-library');
        if (labelLibrary) labelLibrary.textContent = 'Thư viện của tôi';
        const labelAccount = document.getElementById('label-menu-account');
        if (labelAccount) labelAccount.textContent = 'Tài khoản';
        const labelMyData = document.getElementById('label-menu-my-data');
        if (labelMyData) labelMyData.textContent = 'Dữ liệu của tôi';
        const labelSettings = document.getElementById('label-menu-settings');
        if (labelSettings) labelSettings.textContent = 'Cài đặt';
        const labelSignOut = document.getElementById('label-menu-signout');
        if (labelSignOut) {
            labelSignOut.textContent = 'Đăng xuất';
        } else {
            const btnSignOut = document.getElementById('btn-header-signout');
            if (btnSignOut) btnSignOut.textContent = 'Đăng xuất';
        }

        // SOS button & footer
        const btnNavSos = document.getElementById('btn-nav-sos');
        if (btnNavSos) btnNavSos.title = 'Hỗ trợ khẩn cấp (Đường dây nóng 24/7 & Điểm tựa tĩnh tâm)';
        const footerSos = document.querySelector('footer button[onclick*="openSOS"]');
        if (footerSos) footerSos.textContent = 'SOS · Hỗ trợ khẩn cấp';

        // Hide language switcher per Requirement 9
        const langWrapper = document.getElementById('nav-language-wrapper');
        if (langWrapper) {
            langWrapper.style.display = 'none';
            langWrapper.classList.add('hidden');
        }
    }"""

text = text.replace(static_html_target, static_html_replacement)

# Ensure line endings stay CRLF
text_lf = text.replace('\r\n', '\n')
new_crlf = text_lf.replace('\n', '\r\n')

with open(file_path, 'wb') as f:
    f.write(new_crlf.encode('utf-8'))

with open(file_path, 'rb') as f:
    final_bytes = f.read()

final_crlf = final_bytes.count(b'\r\n')
final_lone_lf = final_bytes.count(b'\n') - final_crlf
print(f"i18n.js updated. Final CRLF: {final_crlf}, lone LF: {final_lone_lf}")
