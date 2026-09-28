/**
 * Public Environment Configuration Endpoint (Vercel Serverless)
 * Safely exposes ONLY publishable/public Supabase client configuration.
 * Strictly NEVER exposes SUPABASE_SECRET_KEY, service_role, or any backend secrets.
 */
export default function handler(req, res) {
    if (req.method !== 'GET') {
        return res.status(405).json({ error: 'Method Not Allowed' });
    }

    // Modern Supabase Publishable Key with legacy fallback
    const supabaseUrl = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL || '';
    const supabasePublishableKey = process.env.SUPABASE_PUBLISHABLE_KEY || 
                                  process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY || 
                                  process.env.SUPABASE_ANON_KEY || 
                                  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

    // Cache at edge for 5 minutes
    res.setHeader('Cache-Control', 'public, max-age=60, s-maxage=300');
    res.setHeader('Content-Type', 'application/json');

    return res.status(200).json({
        supabaseUrl,
        supabasePublishableKey
    });
}
