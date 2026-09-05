'use client'

import { useEffect, useState } from 'react'
import { supabaseBrowser } from '@/lib/supabase-browser'

export default function ResetPassword() {
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [ready, setReady] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    const supabase = supabaseBrowser()

    const { data: listener } = supabase.auth.onAuthStateChange(
      (event, session) => {
        if (
          (event === 'PASSWORD_RECOVERY' || event === 'SIGNED_IN') &&
          session
        ) {
          setReady(true)
          setError('')
        }
      }
    )

    supabase.auth.getSession().then(({ data }) => {
      if (data.session) {
        setReady(true)
      } else {
        setTimeout(() => {
          supabase.auth.getSession().then(({ data: retry }) => {
            if (retry.session) setReady(true)
            else {
              setError('Le lien de récupération est invalide ou expiré.')
              setReady(true)
            }
          })
        }, 1000)
      }
    })

    return () => listener.subscription.unsubscribe()
  }, [])

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setError('')

    if (password.length < 6) {
      setError('Le mot de passe doit contenir au moins 6 caractères.')
      return
    }

    if (password !== confirm) {
      setError('Les deux mots de passe ne correspondent pas.')
      return
    }

    const { error } = await supabaseBrowser().auth.updateUser({
      password,
    })

    if (error) {
      setError(error.message)
      return
    }

    setSaved(true)

    setTimeout(() => {
      window.location.href = '/'
    }, 1000)
  }

  if (!ready) {
    return (
      <main className="authpage">
        <div className="authlogo">Équilibre</div>
        <p className="muted">Validation du lien…</p>
      </main>
    )
  }

  return (
    <main className="authpage">
      <div className="authlogo">Équilibre</div>

      <h1>Ton équilibre, simplement.</h1>

      <div className="card authcard">
        <h2>Nouveau mot de passe</h2>

        {saved ? (
          <p>✅ Mot de passe enregistré. Redirection…</p>
        ) : (
          <form className="form" onSubmit={submit}>
            <label>
              Nouveau mot de passe
              <input
                type="password"
                required
                minLength={6}
                autoComplete="new-password"
                value={password}
                onChange={e => setPassword(e.target.value)}
              />
            </label>

            <label>
              Confirmer le mot de passe
              <input
                type="password"
                required
                minLength={6}
                autoComplete="new-password"
                value={confirm}
                onChange={e => setConfirm(e.target.value)}
              />
            </label>

            <button className="btn">
              Enregistrer mon mot de passe
            </button>

            {error && <p className="error">{error}</p>}
          </form>
        )}
      </div>
    </main>
  )
}
