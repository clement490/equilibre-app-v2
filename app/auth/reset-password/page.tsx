'use client'

import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { Suspense } from 'react'
import { supabaseBrowser } from '@/lib/supabase-browser'

function ResetPasswordContent() {
  const params = useSearchParams()
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    async function prepare() {
      const code = params.get('code')

      if (code) {
        const { error } = await supabaseBrowser().auth.exchangeCodeForSession(code)
        if (error) {
          setError('Le lien de récupération est invalide ou expiré.')
          setLoading(false)
          return
        }
      }

      const { data } = await supabaseBrowser().auth.getSession()

      if (!data.session) {
        setError('Impossible de valider le lien de récupération.')
      }

      setLoading(false)
    }

    prepare()
  }, [params])

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

  if (loading) {
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

export default function ResetPassword() {
  return (
    <Suspense fallback={<main className="authpage">Chargement…</main>}>
      <ResetPasswordContent />
    </Suspense>
  )
}
