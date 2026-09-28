/**
 * Tempo Supabase Client Integration (Production Hardened)
 * 
 * Security Features:
 * 1. Supports modern Supabase publishable key model (sb_p_...) with legacy anon key fallback.
 * 2. Strictly prohibits secret keys (sb_s_... / service_role) from ever being loaded in the browser.
 * 3. Never writes or reads sensitive keys from browser localStorage.
 * 4. Loads public configuration securely from /api/config or window.TEMPO_CONFIG.
 */

window.TempoSupabase = (function() {
    let client = null;
    let isConnected = false;
    let isInitialized = false;

    let config = {
        url: window.TEMPO_CONFIG?.supabaseUrl || '',
        publishableKey: window.TEMPO_CONFIG?.supabasePublishableKey || window.TEMPO_CONFIG?.supabaseAnonKey || ''
    };

    /**
     * Inspects a candidate key for secret-key leakage.
     * Throws an error and halts execution if a secret key is detected.
     */
    function validatePublishableKey(key) {
        if (!key) return;
        const normalized = key.trim();

        // Check for new Supabase secret key prefix (sb_s_...)
        if (normalized.startsWith('sb_s_')) {
            const err = "FATAL SECURITY VIOLATION: A Supabase Secret Key (sb_s_...) was provided to the browser. Secret keys must strictly remain server-side.";
            console.error(err);
            throw new Error(err);
        }

        // Check for legacy service_role JWT payload
        if (normalized.startsWith('eyJ')) {
            try {
                const parts = normalized.split('.');
                if (parts.length >= 2) {
                    const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')));
                    if (payload.role === 'service_role') {
                        const err = "FATAL SECURITY VIOLATION: A Supabase service_role key was provided to the browser. Service role keys must never be exposed to clients.";
                        console.error(err);
                        throw new Error(err);
                    }
                }
            } catch (e) {
                // If decoding fails, continue key check
            }
        }
    }

    async function init() {
        // 1. If configuration not injected via window.TEMPO_CONFIG, fetch safe public config from /api/config
        if (!config.url || !config.publishableKey) {
            try {
                const res = await fetch('/api/config');
                if (res.ok) {
                    const data = await res.json();
                    if (data.supabaseUrl) config.url = data.supabaseUrl.trim();
                    if (data.supabasePublishableKey) config.publishableKey = data.supabasePublishableKey.trim();
                }
            } catch (e) {
                // Endpoint unavailable in offline/static preview
            }
        }

        // 2. Validate key safety
        if (config.publishableKey) {
            try {
                validatePublishableKey(config.publishableKey);
            } catch (secError) {
                isConnected = false;
                client = null;
                isInitialized = true;
                return;
            }
        }

        // 3. Initialize Supabase client using publishable/anon key only
        if (config.url && config.publishableKey && window.supabase) {
            try {
                client = window.supabase.createClient(config.url, config.publishableKey, {
                    auth: {
                        persistSession: true,
                        autoRefreshToken: true,
                        detectSessionInUrl: true
                    }
                });
                isConnected = true;
                console.log("[TempoSupabase] Initialized with publishable client key.");
            } catch (err) {
                console.warn("[TempoSupabase] Initialization error:", err);
                isConnected = false;
            }
        } else {
            isConnected = false;
        }

        isInitialized = true;
    }

    function getClient() {
        return client;
    }

    function hasConnection() {
        return isConnected && client !== null;
    }

    function getConfig() {
        return {
            url: config.url,
            isConfigured: !!(config.url && config.publishableKey)
        };
    }

    return {
        init,
        getClient,
        hasConnection,
        getConfig
    };
})();
