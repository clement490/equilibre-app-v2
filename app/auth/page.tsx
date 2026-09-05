'use client'
import { Suspense, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { supabaseBrowser } from '@/lib/supabase-browser'

function AuthContent() {
  const params = useSearchParams()
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [error, setError] = useState('')
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setError('')
    const { error } = await supabaseBrowser().auth.signInWithOtp({
      email,
      options: { emailRedirectTo: `${window.location.origin}/auth/callback?next=${encodeURIComponent(params.get('next') || '/')}` }
    })
    if (error) setError(error.message); else setSent(true)
  }
  const queryError = params.get('error')
  return <main className="authpage"><div className="authlogo">Équilibre</div><h1>Ton équilibre, simplement.</h1><p className="muted">Menus, recettes, courses, poids et sport réunis au même endroit.</p><div className="card authcard">{queryError && <p className="error">Le lien de connexion a expiré ou est invalide. Demande un nouveau lien.</p>}
    {sent ? <><div className="bigemoji">✉️</div><h2>Regarde ta boîte mail</h2><p className="muted">Un lien de connexion vient d'être envoyé à <strong>{email}</strong>.</p></> : <form className="form" onSubmit={submit}><label>Adresse e-mail<input type="email" required placeholder="ton@email.fr" value={email} onChange={e=>setEmail(e.target.value)} /></label><button className="btn">Recevoir mon lien</button>{error && <p className="error">{error}</p>}</form>}
  </div><p className="muted small">Aucun mot de passe à retenir.</p></main>
}


export default function Auth() { return <Suspense fallback={<main className="authpage"><div className="authlogo">Équilibre</div><p className="muted">Chargement…</p></main>}><AuthContent /></Suspense> }
