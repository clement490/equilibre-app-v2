import { supabaseBrowser } from './supabase-browser'

export async function ensureAccount() {
  const sb = supabaseBrowser()
  const { data: { user } } = await sb.auth.getUser()
  if (!user) return null

  let { data: profile } = await sb.from('profiles').select('id,first_name,display_name,height_cm,target_weight_kg,preferences').eq('id', user.id).maybeSingle()
  if (!profile) {
    const firstName = user.user_metadata?.first_name || (user.email?.split('@')[0] || 'Clément')
    await sb.from('profiles').insert({ id: user.id, first_name: firstName, display_name: firstName })
    const res = await sb.from('profiles').select('id,first_name,display_name,height_cm,target_weight_kg,preferences').eq('id', user.id).single()
    profile = res.data
  }

  let { data: membership } = await sb.from('household_members').select('household_id').eq('user_id', user.id).limit(1).maybeSingle()
  if (!membership) {
    const { data: household } = await sb.from('households').insert({ name: 'Équilibre', created_by: user.id }).select('id').single()
    if (household) {
      await sb.from('household_members').insert({ household_id: household.id, user_id: user.id })
      membership = { household_id: household.id }
    }
  }
  return { user, profile, householdId: membership?.household_id ?? null }
}

export async function householdMembers(householdId: string) {
  const sb = supabaseBrowser()
  const { data } = await sb.rpc('get_household_members', { p_household_id: householdId })
  return (data || []).map((m: any) => ({ id: m.user_id, name: m.first_name || m.display_name || 'Profil' }))
}

export function mondayOf(date = new Date()) {
  const d = new Date(date)
  const day = d.getDay()
  const diff = day === 0 ? -6 : 1 - day
  d.setDate(d.getDate() + diff)
  return d.toISOString().slice(0, 10)
}
export function addDays(iso: string, days: number) {
  const d = new Date(iso + 'T12:00:00')
  d.setDate(d.getDate() + days)
  return d.toISOString().slice(0, 10)
}
export function formatRange(start: string) {
  const end = addDays(start, 6)
  const a = new Date(start + 'T12:00:00').toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })
  const b = new Date(end + 'T12:00:00').toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })
  return `${a} → ${b}`
}
