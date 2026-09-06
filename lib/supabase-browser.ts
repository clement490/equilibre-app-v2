import { createBrowserClient } from '@supabase/ssr'

export function supabaseBrowser() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
  const supabaseKey =
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ||
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

  if (!supabaseUrl || !supabaseKey) {
    throw new Error('Configuration Supabase manquante')
  }

  return createBrowserClient(supabaseUrl, supabaseKey)
}
