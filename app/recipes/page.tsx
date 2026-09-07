'use client'

import { useMemo, useState } from 'react'
import Link from 'next/link'

type Recipe={title:string;category:string;time:number;cost:string;kcal:number;icon:string;vegetarian?:boolean}
const recipes:Recipe[]=[
 {title:'Poulet aux légumes & riz',category:'Poulet',time:25,cost:'€',kcal:520,icon:'🍗'},
 {title:'Saumon rôti, pommes de terre & brocolis',category:'Poissons',time:30,cost:'€€€',kcal:610,icon:'🐟'},
 {title:'Pâtes crémeuses aux courgettes',category:'Pâtes',time:20,cost:'€',kcal:570,icon:'🍝',vegetarian:true},
 {title:'Bowl méditerranéen pois chiches & feta',category:'Végétarien',time:25,cost:'€€',kcal:490,icon:'🥙',vegetarian:true},
 {title:'Curry de poulet doux & riz',category:'Poulet',time:30,cost:'€€',kcal:590,icon:'🍛'},
 {title:'Salade méditerranéenne au poulet',category:'Salades & bowls',time:20,cost:'€€',kcal:540,icon:'🥗'},
 {title:'Tartines avocat, œufs & crudités',category:'Rapide',time:15,cost:'€€',kcal:500,icon:'🥑',vegetarian:true},
 {title:'Soupe complète lentilles & légumes',category:'Soupes',time:30,cost:'€',kcal:450,icon:'🥣',vegetarian:true},
 {title:'Risotto crémeux aux champignons',category:'Riz',time:35,cost:'€€',kcal:560,icon:'🍚',vegetarian:true},
 {title:'Chili sin carne',category:'Végétarien',time:35,cost:'€',kcal:510,icon:'🌶️',vegetarian:true},
 {title:'Gratin de courgettes & pommes de terre',category:'Famille',time:40,cost:'€€',kcal:530,icon:'🥔',vegetarian:true},
 {title:'Poulet citron, semoule & courgettes',category:'Rapide',time:25,cost:'€€',kcal:550,icon:'🍋'}
]
const categories=['Toutes','Rapide','Poulet','Poissons','Pâtes','Riz','Végétarien','Salades & bowls','Soupes','Famille']
export default function Recipes(){
 const [cat,setCat]=useState('Toutes');const [q,setQ]=useState('');const [selected,setSelected]=useState<Recipe|null>(null)
 const shown=useMemo(()=>recipes.filter(r=>(cat==='Toutes'||r.category===cat)&&r.title.toLowerCase().includes(q.toLowerCase())),[cat,q])
 return <>
  <div className="top"><div><div className="eyebrow">Bibliothèque</div><h1>Recettes</h1></div><span className="tag">{recipes.length}</span></div>
  <input className="search" placeholder="Rechercher une recette…" value={q} onChange={e=>setQ(e.target.value)}/>
  <div className="chips">{categories.map(c=><button className={cat===c?'chip active':'chip'} key={c} onClick={()=>setCat(c)}>{c}</button>)}</div>
  <p className="muted small">Toutes les recettes restent accessibles. Les filtres servent à trouver rapidement ce qui vous convient.</p>
  <div className="recipegrid">{shown.map(r=><button className="recipe" key={r.title} onClick={()=>setSelected(r)}><div className="art">{r.icon}</div><div className="body"><span className="tag">{r.category}</span><h3>{r.title}</h3><div className="meal-meta"><span>⏱️ {r.time} min</span><span className="cost">{r.cost}</span><span>🔥 {r.kcal} kcal / pers.</span></div></div></button>)}</div>
  {selected&&<div className="overlay" onClick={()=>setSelected(null)}><div className="modal" onClick={e=>e.stopPropagation()}><button className="close" onClick={()=>setSelected(null)}>×</button><div className="bigart">{selected.icon}</div><span className="tag">{selected.category}</span><h2>{selected.title}</h2><p className="meal-meta"><span>⏱️ {selected.time} min</span><span className="cost">{selected.cost}</span><span>🔥 {selected.kcal} kcal / personne</span></p><button className="btn" onClick={()=>alert('Dans la version connectée, cette recette sera placée dans le créneau choisi du planning.')}>Ajouter au planning</button><h3>À propos</h3><p className="muted">Recette structurée pour Équilibre : portions, nutrition, temps, coût indicatif et compatibilité alimentaire pourront être enrichis dans l’encyclopédie complète.</p></div></div>}
  <div className="card" style={{marginTop:18}}><strong>🍽️ Une envie précise ?</strong><p className="muted">Ajoutez une recette directement à votre planning, puis choisissez le repas concerné.</p><Link className="btn secondary" href="/planning">Ouvrir le planning</Link></div>
 </>
}
