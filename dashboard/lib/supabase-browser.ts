import { createClient } from '@supabase/supabase-js'

// Browser klient s anon key — pouze SELECT operace (RLS)
export const supabaseBrowser = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
)
