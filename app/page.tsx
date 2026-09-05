'use client'
import Link from 'next/link'
import { useEffect, useState } from 'react'
import { ensureAccount, mondayOf, addDays } from '@/lib/data'
import { supabaseBrowser } from '@/lib/supabase-browser'

type Recipe={id:string;title:string;kcal_per_serving:number|null;category:string;vegetarian:boolean}
export default function Home(){
 const [name,setName]=useState('Clément'); const [weight,setWeight]=useState<number|null>(null); const [goal,setGoal]=useState<number|null>(null); const [menu,setMenu]=useState<any[]>([]); const [loading,setLoading]=useState(true)
 useEffect(()=>{(async()=>{const a=await ensureAccount(); if(!a){setLoading(false);return} const sb=supabaseBrowser(); setName(a.profile?.first_name||'Clément'); setGoal(a.profile?.target_weight_kg??null); const w=await sb.from('weight_entries').select('weight_kg').eq('user_id',a.user.id).order('measured_on',{ascending:false}).limit(1).maybeSingle(); setWeight(w.data?.weight_kg??null)
 const today=new Date().toISOString().slice(0,10), week=mondayOf(); const {data:mw}=await sb.from('menu_weeks').select('id').eq('household_id',a.householdId).eq('week_start',week).maybeSingle(); if(mw){const {data:items}=await sb.from('menu_items').select('menu_date,meal_type,servings,is_free_meal,recipes(id,title,kcal_per_serving)').eq('menu_week_id',mw.id).eq('menu_date',today); setMenu(items||[])} setLoading(false)})()},[])
 const labels:{[k:string]:string}={petit_dejeuner:'Petit-déjeuner',dejeuner:'Déjeuner',diner:'Dîner',encas:'Encas'}
 if(loading)return <div className="loading">Chargement…</div>
 return <><div className="top"><div className="brand">Équilibre</div><Link className="pill" href="/tracking">👤 {name}</Link></div><section className="hero"><div className="muted">Aujourd’hui · {new Date().toLocaleDateString('fr-FR',{weekday:'long',day:'numeric',month:'long'})}</div><h1>Bonjour {name} 👋</h1><div className="muted">On garde le cap, simplement.</div></section>
 <section className="card"><div className="row"><h2>🍽️ Menu du jour</h2><Link href="/planning">Voir</Link></div>{menu.length?menu.map((m:any)=><div className="meal" key={m.meal_type}><div className="thumb">{m.meal_type==='petit_dejeuner'?'☀️':m.meal_type==='dejeuner'?'🍱':'🌙'}</div><div><div className="muted">{labels[m.meal_type]}</div><strong>{m.is_free_meal?'Repas libre':m.recipes?.title}</strong><div className="kcal">{m.recipes?.kcal_per_serving?`${Math.round(m.recipes.kcal_per_serving)} kcal / portion`:''}</div></div></div>):<div className="empty"><strong>Ton menu n’est pas encore généré.</strong><p className="muted">Va dans Planning pour créer ta semaine automatiquement.</p><Link className="btn" href="/planning">Créer mon planning</Link></div>}</section>
 <section className="card"><div className="row"><div><div className="muted">Poids actuel</div><div className="total">{weight?`${weight.toFixed(1).replace('.',',')} kg`:'—'}</div></div><div><div className="muted">Objectif</div><strong>{goal?`${goal} kg`:'À définir'}</strong></div></div><Link className="btn secondary full" href="/tracking">Voir mon suivi</Link></section></>
}
