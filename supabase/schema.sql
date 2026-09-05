create extension if not exists pgcrypto;

create table if not exists public.profiles (
 id uuid primary key references auth.users(id) on delete cascade,
 display_name text not null,
 height_cm numeric(5,1), target_weight_kg numeric(5,1), avatar_url text,
 created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create table if not exists public.households (
 id uuid primary key default gen_random_uuid(), name text not null, created_by uuid references auth.users(id), created_at timestamptz not null default now()
);
create table if not exists public.household_members (
 household_id uuid references public.households(id) on delete cascade,
 user_id uuid references auth.users(id) on delete cascade,
 role text not null default 'member' check(role in ('owner','member')),
 primary key(household_id,user_id)
);
create table if not exists public.recipes (
 id uuid primary key default gen_random_uuid(),
 title text not null,
 category text not null,
 meal_type text not null check(meal_type in ('breakfast','lunch','dinner','snack','dessert','brunch')),
 vegetarian boolean not null default false,
 servings numeric(5,2) not null default 1,
 prep_min int not null default 0,
 cook_min int not null default 0,
 kcal numeric(7,1), protein_g numeric(7,1), carbs_g numeric(7,1), fat_g numeric(7,1),
 seasons text[] not null default '{}',
 dietary_tags text[] not null default '{}',
 photo_url text, illustration_url text,
 source_url text, license text, provenance text,
 created_at timestamptz not null default now()
);
create table if not exists public.ingredients (
 id uuid primary key default gen_random_uuid(), name text not null unique, canonical_unit text
);
create table if not exists public.recipe_ingredients (
 recipe_id uuid references public.recipes(id) on delete cascade,
 ingredient_id uuid references public.ingredients(id) on delete cascade,
 quantity numeric(10,3) not null,
 unit text not null,
 note text,
 primary key(recipe_id,ingredient_id)
);
create table if not exists public.menu_weeks (
 id uuid primary key default gen_random_uuid(), household_id uuid references public.households(id) on delete cascade,
 week_start date not null, generated_at timestamptz not null default now(), unique(household_id,week_start)
);
create table if not exists public.menu_items (
 id uuid primary key default gen_random_uuid(), week_id uuid references public.menu_weeks(id) on delete cascade,
 menu_date date not null, slot text not null check(slot in ('breakfast','lunch','dinner','snack','dessert')),
 recipe_id uuid references public.recipes(id), servings numeric(5,2) not null default 1,
 is_free_meal boolean not null default false, source text not null default 'generated',
 unique(week_id,menu_date,slot)
);
create table if not exists public.weight_entries (
 id uuid primary key default gen_random_uuid(), user_id uuid references auth.users(id) on delete cascade,
 measured_on date not null, weight_kg numeric(5,2) not null check(weight_kg > 0), created_at timestamptz not null default now(), unique(user_id,measured_at)
);
create table if not exists public.sport_sessions (
 id uuid primary key default gen_random_uuid(), user_id uuid references auth.users(id) on delete cascade,
 session_date date not null, distance_km numeric(7,2), duration_seconds int, avg_heart_rate int, source text, notes text
);
create table if not exists public.recipe_feedback (
 user_id uuid references auth.users(id) on delete cascade,
 recipe_id uuid references public.recipes(id) on delete cascade,
 rating smallint check(rating between 1 and 5), reason text,
 created_at timestamptz not null default now(), primary key(user_id,recipe_id)
);

create or replace function public.is_household_member(hid uuid)
returns boolean language sql security definer set search_path=public as $$
 select exists(select 1 from household_members where household_id=hid and user_id=auth.uid()); $$;

alter table public.profiles enable row level security;
alter table public.households enable row level security;
alter table public.household_members enable row level security;
alter table public.recipes enable row level security;
alter table public.ingredients enable row level security;
alter table public.recipe_ingredients enable row level security;
alter table public.menu_weeks enable row level security;
alter table public.menu_items enable row level security;
alter table public.weight_entries enable row level security;
alter table public.sport_sessions enable row level security;
alter table public.recipe_feedback enable row level security;

create policy "profile own" on profiles for all using(id=auth.uid()) with check(id=auth.uid());
create policy "household members read" on households for select using(is_household_member(id));
create policy "household owner create" on households for insert with check(created_by=auth.uid());
create policy "member rows" on household_members for select using(user_id=auth.uid() or is_household_member(household_id));
create policy "recipes public read" on recipes for select using(true);
create policy "ingredients public read" on ingredients for select using(true);
create policy "recipe ingredients public read" on recipe_ingredients for select using(true);
create policy "weeks household" on menu_weeks for all using(is_household_member(household_id)) with check(is_household_member(household_id));
create policy "items household" on menu_items for all using(exists(select 1 from menu_weeks w where w.id=week_id and is_household_member(w.household_id))) with check(exists(select 1 from menu_weeks w where w.id=week_id and is_household_member(w.household_id)));
create policy "weights own" on weight_entries for all using(user_id=auth.uid()) with check(user_id=auth.uid());
create policy "sport own" on sport_sessions for all using(user_id=auth.uid()) with check(user_id=auth.uid());
create policy "feedback own" on recipe_feedback for all using(user_id=auth.uid()) with check(user_id=auth.uid());
