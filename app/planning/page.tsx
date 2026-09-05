'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { ensureAccount, mondayOf, addDays, formatRange } from '@/lib/data'
import { supabaseBrowser } from '@/lib/supabase-browser'

type Recipe = {
  id: string
  title: string
  kcal: number | null
  vegetarian: boolean
  category: string
  meal_type: string
  prep_min: number
  cook_min: number
}

type Item = {
  id: string
  menu_date: string
  slot: string
  servings: number
  is_free_meal: boolean
  recipe_id: string | null
  recipes: Recipe | null
}

const days = ['Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi','Dimanche']

export default function Planning() {
  const [start, setStart] = useState(mondayOf())
  const [household, setHousehold] = useState<string | null>(null)
  const [items, setItems] = useState<Item[]>([])
  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  async function load() {
    setLoading(true)
    setError('')

    const account = await ensureAccount()

    if (!account?.householdId) {
      setError('Compte ou foyer introuvable.')
      setLoading(false)
      return
    }

    setHousehold(account.householdId)

    const sb = supabaseBrowser()

    const { data: week, error: weekError } = await sb
      .from('menu_weeks')
      .select('id')
      .eq('household_id', account.householdId)
      .eq('week_start', start)
      .maybeSingle()

    if (weekError) {
      setError(weekError.message)
      setLoading(false)
      return
    }

    if (week) {
      const { data, error: itemsError } = await sb
        .from('menu_items')
        .select(`
          id,
          menu_date,
          slot,
          servings,
          is_free_meal,
          recipe_id,
          recipes (
            id,
            title,
            kcal,
            vegetarian,
            category,
            meal_type,
            prep_min,
            cook_min
          )
        `)
        .eq('week_id', week.id)
        .order('menu_date')

      if (itemsError) {
        setError(itemsError.message)
      } else {
        setItems((data || []) as any)
      }
    } else {
      setItems([])
    }

    const { data: r, error: recipesError } = await sb
      .from('recipes')
      .select('id,title,kcal,vegetarian,category,meal_type,prep_min,cook_min')
      .order('title')

    if (recipesError) {
      setError(recipesError.message)
    } else {
      setRecipes((r || []) as Recipe[])
    }

    setLoading(false)
  }

  useEffect(() => {
    load()
  }, [start])

  async function generate() {
    if (!household || !recipes.length) {
      setError('Aucune recette disponible.')
      return
    }

    setLoading(true)
    setError('')

    const sb = supabaseBrowser()

    const { data: week, error: weekError } = await sb
      .from('menu_weeks')
      .upsert(
        {
          household_id: household,
          week_start: start
        },
        {
          onConflict: 'household_id,week_start'
        }
      )
      .select('id')
      .single()

    if (weekError || !week) {
      setError(weekError?.message || 'Impossible de créer la semaine.')
      setLoading(false)
      return
    }

    const breakfasts = recipes.filter(r => r.meal_type === 'breakfast')
    const lunches = recipes.filter(r => r.meal_type === 'lunch' || r.meal_type === 'dinner')
    const dinners = recipes.filter(r => r.meal_type === 'dinner')

    if (!breakfasts.length || !dinners.length) {
      setError('Il manque des recettes de petit-déjeuner ou de dîner.')
      setLoading(false)
      return
    }

    await sb
      .from('menu_items')
      .delete()
      .eq('week_id', week.id)

    const rows: any[] = []

    for (let i = 0; i < 7; i++) {
      const date = addDays(start, i)

      const breakfast = breakfasts[i % breakfasts.length]

      rows.push({
        week_id: week.id,
        menu_date: date,
        slot: 'breakfast',
        recipe_id: breakfast.id,
        servings: 1,
        is_free_meal: false
      })

      const free = i === 4

      if (free) {
        rows.push({
          week_id: week.id,
          menu_date: date,
          slot: 'dinner',
          recipe_id: null,
          servings: 6,
          is_free_meal: true
        })
      } else {
        const dinner = dinners[(i + 2) % dinners.length]

        rows.push({
          week_id: week.id,
          menu_date: date,
          slot: 'dinner',
          recipe_id: dinner.id,
          servings: 6,
          is_free_meal: false
        })
      }

      const lunch = lunches[(i + 1) % lunches.length]

      rows.push({
        week_id: week.id,
        menu_date: date,
        slot: 'lunch',
        recipe_id: lunch.id,
        servings: 2,
        is_free_meal: false
      })
    }

    const { error: insertError } = await sb
      .from('menu_items')
      .insert(rows)

    if (insertError) {
      setError(insertError.message)
      setLoading(false)
      return
    }

    await load()
  }

  const shown: Record<string, Item[]> = {}

  for (const item of items) {
    if (!shown[item.menu_date]) shown[item.menu_date] = []
    shown[item.menu_date].push(item)
  }

  if (loading) {
    return <div className="loading">Chargement…</div>
  }

  return (
    <>
      <div className="top">
        <div>
          <div className="muted">Menus & courses</div>
          <h1>Planning</h1>
        </div>

        <button className="btn" onClick={generate}>
          Générer la semaine
        </button>
      </div>

      {error && (
        <div className="card" style={{ marginBottom: 20 }}>
          <strong>Erreur :</strong> {error}
        </div>
      )}

      <div className="weeknav">
        <button onClick={() => setStart(addDays(start, -7))}>‹</button>
        <strong>{formatRange(start)}</strong>
        <button onClick={() => setStart(addDays(start, 7))}>›</button>
      </div>

      {days.map((day, i) => {
        const date = addDays(start, i)
        const list = shown[date] || []

        const breakfast = list.find(x => x.slot === 'breakfast')
        const lunch = list.find(x => x.slot === 'lunch')
        const dinner = list.find(x => x.slot === 'dinner')

        return (
          <section className="card day" key={date}>
            <div className="row">
              <h2>{day}</h2>
              {dinner?.is_free_meal && <span className="tag">Repas libre</span>}
            </div>

            <Meal
              item={breakfast}
              icon="☀️"
              label="Petit-déjeuner"
            />

            <Meal
              item={lunch}
              icon="🍱"
              label="Déjeuner"
            />

            <Meal
              item={dinner}
              icon="🌙"
              label="Dîner"
            />
          </section>
        )
      })}
    </>
  )
}

function Meal({
  item,
  icon,
  label
}: {
  item?: Item
  icon: string
  label: string
}) {
  const content = (
    <div className="meal">
      <div className="thumb">{icon}</div>

      <div>
        <div className="muted">{label}</div>

        <strong>
          {item?.is_free_meal
            ? 'Repas libre'
            : item?.recipes?.title || 'À planifier'}
        </strong>

        {item?.recipes && (
          <div className="kcal">
            {item.recipes.kcal
              ? `${Math.round(item.recipes.kcal)} kcal / portion`
              : ''}
            {' · '}
            {item.recipes.prep_min + item.recipes.cook_min} min
            {item.recipes.vegetarian ? ' · végétarien' : ''}
          </div>
        )}
      </div>
    </div>
  )

  if (item?.recipe_id && !item.is_free_meal) {
    return (
      <Link
        className="meal-link"
        href={`/recipes?recipe=${item.recipe_id}`}
      >
        {content}
      </Link>
    )
  }

  return content
}
