'use client'

import { useState } from 'react'

const defaults=[['Petit-déjeuner',4],['Collation',0],['Déjeuner',2],['Goûter',2],['Dîner',4]]
export default function Settings(){
 const [people,setPeople]=useState(defaults);const [saved,setSaved]=useState(false);const [members,setMembers]=useState(['Clément','Adulte 2','Enfant 1','Enfant 2'])
 const change=(i:number,d:number)=>setPeople(p=>p.map((x,n)=>n===i?[x[0],Math.max(0,Math.min(12,Number(x[1])+d))]:x))
 return <>
  <div className="top"><div><div className="eyebrow">Votre foyer</div><h1>Profil</h1></div></div>
  <section className="card"><h2>👨‍👩‍👧‍👦 Membres de la famille</h2>{members.map((m,i)=><div className="history" key={m}><strong>{m}</strong><span className="muted small"> {i===0?'· Vous':i===1?'· Adulte':'· Enfant'}</span></div>)}<button className="btn secondary" style={{marginTop:12}} onClick={()=>setMembers(m=>[...m,`Membre ${m.length+1}`])}>+ Ajouter un membre</button></section>
  <section className="card"><h2>👥 Portions habituelles</h2><p className="muted">Une personne = une portion. Ces nombres servent de réglages par défaut et restent modifiables dans le planning.</p>{people.map((p,i)=><div className="row history" key={p[0]}><strong>{p[0]}</strong><div style={{display:'flex',alignItems:'center',gap:8}}><button className="chip" onClick={()=>change(i,-1)}>−</button><strong>{p[1]}</strong><button className="chip" onClick={()=>change(i,1)}>+</button></div></div>)}</section>
  <section className="card"><h2>🥡 Gamelles</h2><p className="muted">Choisissez le nombre de gamelles et les jours concernés directement dans le planning. Elles reprennent le dîner précédent.</p><div className="card" style={{margin:0,background:'var(--soft)',border:0}}><strong>2 gamelles</strong><p className="muted small">À régler chaque semaine selon vos besoins.</p></div></section>
  <section className="card"><h2>🎯 Vos objectifs</h2><div className="form"><label>Objectif<select defaultValue="reequilibrage"><option value="reequilibrage">Rééquilibrage alimentaire</option><option>Perte de poids</option><option>Maintien</option><option>Retour au sport</option><option>Objectif sportif</option></select></label><label>Temps de cuisine habituel<input defaultValue="30–45 min"/></label></div></section>
  <button className="btn" style={{width:'100%'}} onClick={()=>setSaved(true)}>{saved?'✓ Enregistré':'Enregistrer mes préférences'}</button>
 </>
}
