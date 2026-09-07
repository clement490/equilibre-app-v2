import { createClient } from './supabase-browser'

export type RecipeCard = {
  id: string
  title: string
  description: string | null
  total_minutes: number | null
  kcal_per_serving: number | null
  protein_per_serving: number | null
  carbs_per_serving: number | null
  fat_per_serving: number | null
  cost_tier: string | null
  vegetarian: boolean
  vegan: boolean
  image_url: string | null
}

export async function loadRecipeCards(limit = 500) {
  const supabase = createClient()
  const { data: recipes, error } = await supabase
    .from('recipes')
    .select('id,title,description,total_minutes,kcal_per_serving,protein_per_serving,carbs_per_serving,fat_per_serving,cost_tier,vegetarian,vegan')
    .order('created_at', { ascending: true })
    .limit(limit)

  if (error) throw error
  if (!recipes?.length) return []

  const ids = recipes.map(r => r.id)
  const { data: images } = await supabase
    .from('recipe_images')
    .select('recipe_id,public_url')
    .in('recipe_id', ids)
    .eq('is_primary', true)

  const imageByRecipe = new Map((images ?? []).map(i => [i.recipe_id, i.public_url]))
  return recipes.map(r => ({ ...r, image_url: imageByRecipe.get(r.id) ?? null })) as RecipeCard[]
}
