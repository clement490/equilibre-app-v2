'use client'

import { Suspense, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { supabaseBrowser } from '@/lib/supabase-browser'

type Recipe={
  id:string
  title:string
  category:string
  meal_type:string
  vegetarian:boolean
  servings:number
  prep_min:number
  cook_min:number
  kcal:number|null
}

type RI={
  quantity:number
  unit:string
  note:string|null
  ingredients:{name:string}|null
}

const labels:Record<string,string>={
  'Petits-déjeuners':'Petits-déjeuners',
  'Plats faibles en calories':'Légers',
  'Végétariens':'Végétariens',
  'Plats':'Plats',
  'Desserts':'Desserts',
  'Encas & goûters':'Encas & goûters'
}

const art:Record<string,string>={
  'Petits-déjeuners':'☀️',
  'Plats faibles en calories':'🥗',
  'Végétariens':'🌱',
  'Plats':'🍲',
  'Desserts':'🍓',
  'Encas & goûters':'🍎'
}

function RecipesContent(){
  const params=useSearchParams()
  const [recipes,setRecipes]=useState<Recipe[]>([])
  const [cat,setCat]=useState('all')
  const [query,setQuery]=useState('')
  const [selected,setSelected]=useState<Recipe|null>(null)
  const [ingredients,setIngredients]=useState<RI[]>([])
  const [servings,setServings]=useState(1)
  const [error,setError]=useState('')

  useEffect(()=>{
    async function load(){
      const {data,error}=await supabaseBrowser()
        .from('recipes')
        .select('id,title,category,meal_type,vegetarian,servings,prep_min,cook_min,kcal')
        .order('title')

      if(error){
        setError(error.message)
        return
      }

      const rs=(data||[]) as Recipe[]
      setRecipes(rs)

      const id=params.get('recipe')
      if(id){
        const r=rs.find(x=>x.id===id)
        if(r) openRecipe(r)
      }
    }

    load()
  },[])

  async function openRecipe(r:Recipe){
    setSelected(r)
    setServings(r.servings||1)

    const {data,error}=await supabaseBrowser()
      .from('recipe_ingredients')
      .select('quantity,unit,note,ingredients(name)')
      .eq('recipe_id',r.id)

    if(error){
      setIngredients([])
      return
    }

    setIngredients((data||[]) as any)
  }

  const shown=useMemo(
    ()=>recipes.filter(r=>
      (cat==='all'||r.category===cat) &&
      r.title.toLowerCase().includes(query.toLowerCase())
    ),
    [recipes,cat,query]
  )

  const scale=(q:number)=>q*(servings/(selected?.servings||1))

  return <>
    <div className="top">
      <div>
        <div className="muted">Bibliothèque</div>
        <h1>Recettes</h1>
      </div>
      <span className="tag">{recipes.length}</span>
    </div>

    {error&&<div className="card"><strong>Erreur :</strong> {error}</div>}

    <input
      className="search"
      placeholder="Rechercher une recette…"
      value={query}
      onChange={e=>setQuery(e.target.value)}
    />

    <div className="chips">
      <button className={cat==='all'?'chip active':'chip'} onClick={()=>setCat('all')}>
        Toutes
      </button>
      {Object.entries(labels).map(([k,v])=>
        <button
          className={cat===k?'chip active':'chip'}
          key={k}
          onClick={()=>setCat(k)}
        >
          {v}
        </button>
      )}
    </div>

    <div className="recipegrid">
      {shown.map(r=>
        <button className="recipe" key={r.id} onClick={()=>openRecipe(r)}>
          <div className="art">{art[r.category]||'🍽️'}</div>
          <div className="body">
            <span className="tag">{labels[r.category]||r.category}</span>
            <h3>{r.title}</h3>
            <div className="kcal">
              {r.kcal?`${Math.round(r.kcal)} kcal / portion`:'Calories à valider'}
              {' · '}
              {r.prep_min+r.cook_min} min
            </div>
          </div>
        </button>
      )}
    </div>

    {selected&&
      <div className="overlay" onClick={()=>setSelected(null)}>
        <div className="modal" onClick={e=>e.stopPropagation()}>
          <button className="close" onClick={()=>setSelected(null)}>×</button>

          <div className="bigart">{art[selected.category]||'🍽️'}</div>
          <span className="tag">{labels[selected.category]||selected.category}</span>
          <h2>{selected.title}</h2>

          <p>
            <strong>{selected.prep_min+selected.cook_min} min</strong>
            {' · '}
            {selected.kcal?`${Math.round(selected.kcal*(servings/(selected.servings||1)))} kcal`:''}
          </p>

          <label className="servings">
            Portions
            <input
              type="number"
              min="1"
              max="20"
              value={servings}
              onChange={e=>setServings(Math.max(1,Number(e.target.value)||1))}
            />
          </label>

          <h3>Ingrédients</h3>

          {ingredients.length
            ? <ul>
                {ingredients.map((x,i)=>
                  <li key={i}>
                    {Math.round(scale(Number(x.quantity))*10)/10}
                    {' '}
                    {x.unit}
                    {' · '}
                    {x.ingredients?.name}
                    {x.note?` (${x.note})`:''}
                  </li>
                )}
              </ul>
            : <p className="muted">Aucun ingrédient renseigné.</p>
          }
        </div>
      </div>
    }
  </>
}

export default function Recipes(){
  return (
    <Suspense fallback={<div className="loading">Chargement…</div>}>
      <RecipesContent/>
    </Suspense>
  )
}
