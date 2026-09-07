'use client'

import Link from 'next/link'

const meals=[
 {slot:'Déjeuner',title:'Salade méditerranéenne au poulet',time:20,cost:'€€',kcal:540,icon:'🥗'},
 {slot:'Dîner',title:'Saumon rôti, pommes de terre & brocolis',time:30,cost:'€€€',kcal:610,icon:'🐟'}
]

export default function Home(){
 return <>
  <header className="top"><div className="brand">Équilibre</div><Link className="profile-pill" href="/settings">CB</Link></header>
  <section className="hero"><div className="eyebrow">Aujourd’hui · lundi 7 septembre</div><h1>Bonjour Clément 👋</h1><p>Une alimentation adaptée à votre vraie vie.</p></section>
  <section className="card highlight"><div><span className="eyebrow">Cette semaine</span><h2>Votre planning est prêt</h2><p className="muted">Des repas pensés selon vos habitudes, votre temps et votre foyer.</p></div><Link className="btn" href="/planning">Voir le planning</Link></section>
  <section className="section-head"><h2>Aujourd’hui</h2><Link href="/planning">Semaine →</Link></section>
  <div className="stack">{meals.map(m=><Meal key={m.slot} meal={m}/>)}</div>
  <section className="section-head"><h2>À découvrir</h2><Link href="/recipes">Toutes les recettes →</Link></section>
  <div className="quick-grid"><Link href="/recipes" className="quick"><span>🍝</span><strong>J’ai envie de pâtes</strong><small>Parcourir les recettes</small></Link><Link href="/recipes" className="quick"><span>🥗</span><strong>Rapide & léger</strong><small>20–30 minutes</small></Link></div>
 </>
}
function Meal({meal}:{meal:any}){return <Link href="/planning" className="meal-card"><div className="meal-icon">{meal.icon}</div><div className="meal-info"><span className="eyebrow">{meal.slot}</span><strong>{meal.title}</strong><div className="meal-meta"><span>⏱️ {meal.time} min</span><span className="cost">{meal.cost}</span><span>🔥 {meal.kcal} kcal / pers.</span></div></div></Link>}
