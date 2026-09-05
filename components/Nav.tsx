'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
const items=[['/','⌂','Accueil'],['/recipes','🍴','Recettes'],['/planning','▦','Planning'],['/tracking','◔','Suivi'],['/settings','⚙️','Profil']]
export default function Nav(){const path=usePathname();return <nav className="nav"><div className="navinner">{items.map(([href,icon,label])=><Link className={path===href?'active':''} href={href} key={href}><span>{icon}</span>{label}</Link>)}</div></nav>}
