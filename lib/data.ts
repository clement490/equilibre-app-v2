import { supabaseBrowser } from './supabase-browser'

export async function ensureAccount() {
  const sb = supabaseBrowser()
  const { data: { user } } = await sb.auth.getUser()
  if (!user) return null

  let { data: profile } = await sb.from('profiles').select('id,display_name,height_cm,target_weight_kg,avatar_url').eq('id', user.id).maybeSingle()
  if (!profile) {
    const firstName = user.user_metadata?.display_name || user.email?.split('@')[0] || 'Clément'
    await sb.from('profiles').insert({ id: user.id, display_name: firstName })
    const res = await sb.from('profiles').select('id,display_name,height_cm,target_weight_kg,avatar_url').eq('id', user.id).single()
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
  const { data: members } = await sb
    .from('household_members')
    .select('user_id,role')
    .eq('household_id', householdId)

  if (!members?.length) return []

  const ids = members.map(m => m.user_id)
  const { data: profiles } = await sb
    .from('profiles')
    .select('id,display_name')
    .in('id', ids)

  const names = new Map((profiles || []).map(p => [p.id, p.display_name]))

  return members.map(m => ({
    id: m.user_id,
    name: names.get(m.user_id) || 'Profil',
    role: m.role
  }))
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
