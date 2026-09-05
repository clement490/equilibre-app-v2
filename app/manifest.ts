import type { MetadataRoute } from 'next'
export default function manifest(): MetadataRoute.Manifest {
  return { name:'Équilibre', short_name:'Équilibre', description:'Menus, recettes, courses, suivi du poids et sport.', start_url:'/', display:'standalone', background_color:'#f6f7f3', theme_color:'#68785f', lang:'fr' }
}
