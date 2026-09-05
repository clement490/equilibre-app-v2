-- ÉQUILIBRE — saisonnalité des ingrédients

alter table public.ingredients
add column if not exists seasons text[] not null default '{}';

create index if not exists ingredients_seasons_idx
on public.ingredients using gin(seasons);

create index if not exists recipes_seasons_idx
on public.recipes using gin(seasons);

-- Fonction : saison française selon la date
create or replace function public.french_season(d date)
returns text
language sql
immutable
as $$
  select case
    when extract(month from d) in (12,1,2) then 'winter'
    when extract(month from d) in (3,4,5) then 'spring'
    when extract(month from d) in (6,7,8) then 'summer'
    else 'autumn'
  end;
$$;

-- Score de saisonnalité d'une recette
create or replace function public.recipe_season_score(
  recipe_seasons text[],
  target_date date
)
returns numeric
language sql
immutable
as $$
  select case
    when recipe_seasons is null or cardinality(recipe_seasons) = 0 then 0.5
    when public.french_season(target_date) = any(recipe_seasons) then 1.0
    else 0.15
  end;
$$;
