'use client'

import { useEffect, useMemo, useState } from 'react'
import { createClient } from '@/lib/supabase-browser'

const supabase = createClient()

type Recipe = { id: string; title: string }

type Result = { file: string; recipe: string; ok: boolean; error?: string }

export default function RecipeImagesImport() {
  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [files, setFiles] = useState<FileList | null>(null)
  const [results, setResults] = useState<Result[]>([])
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    supabase.from('recipes').select('id,title').order('created_at').limit(5000)
      .then(({ data }) => setRecipes((data ?? []) as Recipe[]))
  }, [])

  const byId = useMemo(() => new Map(recipes.map(r => [r.id, r])), [recipes])

  async function importFiles() {
    if (!files?.length) return
    setBusy(true)
    setResults([])
    const output: Result[] = []
    for (const file of Array.from(files)) {
      const base = file.name.replace(/\.[^.]+$/, '')
      const recipe = byId.get(base)
      if (!recipe) {
        output.push({ file: file.name, recipe: base, ok: false, error: 'Nom de fichier attendu : <recipe_id>.webp' })
        continue
      }
      const form = new FormData()
      form.append('recipe_id', recipe.id)
      form.append('file', file)
      const { data: { session } } = await supabase.auth.getSession()
      if (!session?.access_token) {
        output.push({ file: file.name, recipe: recipe.title, ok: false, error: 'Session utilisateur requise' })
        continue
      }
      const res = await fetch(`${process.env.NEXT_PUBLIC_SUPABASE_URL}/functions/v1/recipe-image-upload-v2`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${session.access_token}` },
        body: form,
      })
      const body = await res.json().catch(() => ({}))
      output.push(res.ok ? { file: file.name, recipe: recipe.title, ok: true } : { file: file.name, recipe: recipe.title, ok: false, error: body.error ?? 'Upload échoué' })
    }
    setResults(output)
    setBusy(false)
  }

  return <main className="card" style={{ marginTop: 24 }}>
    <div className="eyebrow">Médias</div>
    <h1>Importer les visuels recettes</h1>
    <p className="muted">Dépose un lot de fichiers <strong>&lt;recipe_id&gt;.webp</strong>. Chaque image est envoyée dans Supabase Storage et associée automatiquement à sa recette.</p>
    <input type="file" accept="image/webp,image/jpeg,image/png" multiple onChange={e => setFiles(e.target.files)} />
    <button className="btn" disabled={busy || !files?.length} onClick={importFiles}>{busy ? 'Import en cours…' : 'Importer le lot'}</button>
    {!!results.length && <div style={{ marginTop: 16 }}>{results.map((r, i) => <div key={i}>{r.ok ? '✓' : '✕'} {r.recipe} — {r.file}{r.error ? ` — ${r.error}` : ''}</div>)}</div>}
  </main>
}
