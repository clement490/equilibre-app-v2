'use client'

import Link from 'next/link'
import { useMemo, useState } from 'react'

type Meal={slot:string;title:string;time:number;cost:string;kcal:number;icon:string;people:number;boxed?:number}
const initial:Record<string,Meal[]>={
 'Lundi':[
  {slot:'Déjeuner',title:'Salade méditerranéenne au poulet',time:20,cost:'€€',kcal:540,icon:'🥗',people:2},
  {slot:'Dîner',title:'Saumon rôti, pommes de terre & brocolis',time:30,cost:'€€€',kcal:610,icon:'🐟',people:4,boxed:2}],
 'Mardi':[
  {slot:'Déjeuner',title:'Saumon rôti, pommes de terre & brocolis',time:30,cost:'€€€',kcal:610,icon:'🥡',people:2},
  {slot:'Dîner',title:'Poulet aux légumes & riz',time:25,cost:'€',kcal:520,icon:'🍗',people:4}],
 'Mercredi':[
  {slot:'Déjeuner',title:'Poulet aux légumes & riz',time:25,cost:'€',kcal:520,icon:'🥡',people:2},
  {slot:'Dîner',title:'Pâtes crémeuses aux courgettes',time:20,cost:'€',kcal:570,icon:'🍝',people:4,boxed:2}],
 'Jeudi':[{slot:'Déjeuner',title:'Pâtes crémeuses aux courgettes',time:20,cost:'€',kcal:570,icon:'🥡',people:2},{slot:'Dîner',title:'Bowl méditerranéen pois chiches & feta',time:25,cost:'€€',kcal:490,icon:'🥙',people:4}],
 'Vendredi':[{slot:'Déjeuner',title:'Déjeuner libre',time:0,cost:'',kcal:0,icon:'🍴',people:2},{slot:'Dîner',title:'Curry de poulet doux & riz',time:30,cost:'€€',kcal:590,icon:'🍛',people:4,boxed:2}],
 'Samedi':[{slot:'Déjeuner',title:'Tartines avocat, œufs & crudités',time:15,cost:'€€',kcal:500,icon:'🥑',people:2},{slot:'Dîner',title:'Pizza maison légumes grillés',time:35,cost:'€€',kcal:640,icon:'🍕',people:4}],
 'Dimanche':[{slot:'Déjeuner',title:'Poulet rôti, légumes & pommes de terre',time:45,cost:'€€',kcal:670,icon:'🍗',people:4},{slot:'Dîner',title:'Soupe complète lentilles & légumes',time:30,cost:'€',kcal:450,icon:'🥣',people:4}]
}

export default function Planning(){
 const [week,setWeek]=useState(initial)
 const [boxes,setBoxes]=useState({monday:2,tuesday:2,wednesday:2,thursday:0,friday:2,saturday:0,sunday:0})
 const days=Object.keys(week)
 const totalKcal=useMemo(()=>Object.values(week).flat().reduce((s,m)=>s+m.kcal,0),[week])
 function changePeople(day:string,index:number,delta:number){setWeek(w=>{const copy={...w};const list=[...copy[day]];list[index]={...list[index],people:Math.max(1,Math.min(12,list[index].people+delta))};copy[day]=list;return copy})}
 return <>
  <div className="top"><div><div className="eyebrow">Menus & organisation</div><h1>Planning</h1></div><button className="btn" onClick={()=>alert('Le générateur intelligent sera branché sur votre profil.')}>✨ Générer</button></div>
  <div className="weeknav"><button onClick={()=>{}}>‹</button><strong>7 — 13 septembre</strong><button onClick={()=>{}}>›</button></div>
  <section className="card highlight"><div><span className="eyebrow">Votre semaine</span><h2>Une semaine pensée pour vous</h2><p className="muted">Les quantités s’adaptent au nombre de personnes et aux gamelles.</p></div></section>
  {days.map(day=><section className="card day" key={day}><div className="row"><h2>{day}</h2></div>{week[day].map((m,i)=><div className="meal" key={m.slot}><div className="thumb">{m.icon}</div><div><div className="eyebrow">{m.slot}</div><strong>{m.title}</strong>{m.kcal>0&&<div className="meal-meta"><span>⏱️ {m.time} min</span><span className="cost">{m.cost}</span><span>🔥 {m.kcal} kcal / pers.</span></div>}{m.boxed&&<div className="kcal">🥡 {m.boxed} gamelles prévues le lendemain</div>}<div style={{display:'flex',alignItems:'center',gap:7,marginTop:7}}><span className="eyebrow">Personnes</span><button className="chip" onClick={()=>changePeople(day,i,-1)}>−</button><strong>{m.people}</strong><button className="chip" onClick={()=>changePeople(day,i,1)}>+</button></div></div></div>)}</section>)}
  <section className="card"><span className="eyebrow">🥡 Organisation</span><h2>Pas le temps de cuisiner demain midi ?</h2><p className="muted">Prévoir des gamelles permet à Équilibre d’augmenter les portions du dîner et de mettre à jour les courses.</p><div className="chips">{days.map((d,i)=><label className="chip" key={d}><input type="checkbox" checked={Object.values(boxes)[i]>0} onChange={e=>setBoxes(b=>({...b,[Object.keys(b)[i]]:e.target.checked?2:0}))}/> {d}</label>)}</div><div style={{display:'flex',alignItems:'center',gap:10,marginTop:10}}><strong>Nombre de gamelles</strong><button className="chip" onClick={()=>{}}>−</button><strong>2</strong><button className="chip" onClick={()=>{}}>+</button></div></section>
  <Link className="btn" href="/recipes" style={{width:'100%'}}>Ajouter une recette au planning</Link>
 </>
}
