import { createClient } from '@supabase/supabase-js'

// Server-side klient s service role key — nikdy neposílat do browseru
export const supabaseAdmin = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
)
