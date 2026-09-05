insert into public.recipes(title,category,meal_type,vegetarian,servings,prep_min,cook_min,kcal,seasons,dietary_tags,provenance,license)
values
('Porridge pomme & cannelle','Petits-déjeuners','breakfast',true,1,5,5,380,'{automne,hiver}','{simple}','Équilibre starter seed','original'),
('Pancakes banane & skyr','Petits-déjeuners','breakfast',true,1,8,8,410,'{toutes}','{protéiné}','Équilibre starter seed','original'),
('Saumon, riz & brocoli','Plats faibles en calories','dinner',false,6,10,25,620,'{toutes}','{famille}','Équilibre starter seed','original'),
('Chili végétarien','Végétariens','dinner',true,6,10,30,540,'{automne,hiver,printemps}','{famille}','Équilibre starter seed','original'),
('Curry de légumes','Végétariens','dinner',true,6,10,25,510,'{automne,hiver,printemps}','{famille}','Équilibre starter seed','original'),
('Poulet rôti pommes de terre','Plats','dinner',false,6,15,35,590,'{automne,hiver,printemps}','{famille}','Équilibre starter seed','original'),
('Mousse chocolat légère','Desserts','dessert',true,1,10,0,190,'{toutes}','{simple}','Équilibre starter seed','original'),
('Compote pomme-poire','Desserts','dessert',true,1,5,15,120,'{automne,hiver}','{simple}','Équilibre starter seed','original'),
('Energy balls avoine-cacahuète','Encas & goûters','snack',true,1,10,0,160,'{toutes}','{goûter}','Équilibre starter seed','original')
on conflict do nothing;
