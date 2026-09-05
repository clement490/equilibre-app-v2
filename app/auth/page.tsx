'use client'

import { useState } from 'react'
import { supabaseBrowser } from '@/lib/supabase-browser'

export default function Auth() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [mode, setMode] = useState<'login' | 'signup'>('login')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)

    const supabase = supabaseBrowser()

    if (mode === 'login') {
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      })

      if (error) {
        setError('E-mail ou mot de passe incorrect.')
        setLoading(false)
        return
      }

      window.location.href = '/'
      return
    }

    const { error } = await supabase.auth.signUp({
      email,
      password,
    })

    if (error) {
      setError(error.message)
      setLoading(false)
      return
    }

    window.location.href = '/'
  }

  return (
    <main className="authpage">
      <div className="authlogo">Équilibre</div>

      <h1>Ton équilibre, simplement.</h1>

      <p className="muted">
        Menus, recettes, courses, poids et sport réunis au même endroit.
      </p>

      <div className="card authcard">
        <h2>{mode === 'login' ? 'Connexion' : 'Créer mon compte'}</h2>

        <form className="form" onSubmit={submit}>
          <label>
            Adresse e-mail
            <input
              type="email"
              required
              autoComplete="email"
              placeholder="ton@email.fr"
              value={email}
              onChange={e => setEmail(e.target.value)}
            />
          </label>

          <label>
            Mot de passe
            <input
              type="password"
              required
              minLength={6}
              autoComplete={
                mode === 'login' ? 'current-password' : 'new-password'
              }
              placeholder="••••••••"
              value={password}
              onChange={e => setPassword(e.target.value)}
            />
          </label>

          <button className="btn" disabled={loading}>
            {loading
              ? 'Chargement…'
              : mode === 'login'
                ? 'Se connecter'
                : 'Créer mon compte'}
          </button>

          {error && <p className="error">{error}</p>}
        </form>

        <button
          type="button"
          className="pill"
          onClick={() => {
            setMode(mode === 'login' ? 'signup' : 'login')
            setError('')
          }}
        >
          {mode === 'login'
            ? 'Créer un nouveau compte'
            : 'J’ai déjà un compte'}
        </button>
      </div>

      <p className="muted small">
        Connexion sécurisée avec ton adresse e-mail et ton mot de passe.
      </p>
    </main>
  )
}
