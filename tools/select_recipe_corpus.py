import json,re,unicodedata
from pathlib import Path

def norm(s):
 s=unicodedata.normalize('NFKD',s or '').encode('ascii','ignore').decode().lower().replace('advertisement',' ')
 return re.sub(r'\s+',' ',s).strip()
alcohol=re.compile(r'(?<![a-z])(beer|ale|lager|stout|porter|wine|red wine|white wine|champagne|prosecco|sherry|marsala|vermouth|brandy|cognac|rum|vodka|whisky|whiskey|bourbon|tequila|kirsch|liqueur|amaretto|baileys|cointreau|grand marnier|sake|mirin)(?![a-z])')
bad_title=re.compile(r'\b(cocktail|martini|margarita|juice|lemonade|punch|sangria|mocktail|beverage|drink|tea|coffee|syrup|frosting|icing|glaze|marinade|dressing|dip|condiment|sauce|gravy|jam|jelly|candy|caramel|fudge|truffle|cookie dough|pet food)\b')
sweet_title=re.compile(r'\b(cake|cupcake|brownie|cookie|cookies|donut|doughnut|pie|tart|pudding|cheesecake|ice cream|sorbet|dessert|cobbler|crisp|parfait|cannoli|macaron|meringue|fudge|biscotti|bread)\b')
breakfast=re.compile(r'\b(pancake|waffle|oatmeal|porridge|granola|french toast|breakfast|brunch|overnight oats|baked oats)\b')
hard_ing=re.compile(r'\b(foie gras|truffle|truffles|caviar|uni\b|roe\b|octopus ink|squid ink|saffron|gochujang|gochugaru|kombu|bonito flakes|dashi|nori|wasabi|tamarind paste|galangal|asafoetida|ajwain|sumac|chipotle in adobo|mole paste|cassava flour|jicama|collard greens|venison|elk|bison|rabbit|quail|pheasant|sweetbread|brain|tongue|tripe)\b')
protein=re.compile(r'\b(chicken|turkey|beef|pork|lamb|veal|salmon|tuna|cod|haddock|sardine|mackerel|shrimp|prawn|fish|seafood|egg|eggs|tofu|tempeh|chickpea|chickpeas|lentil|lentils|bean|beans|yogurt|yoghurt|skyr|cottage cheese|cheese|mozzarella|feta|parmesan|ham|bacon)\b')
produce=re.compile(r'\b(apple|apples|pear|pears|banana|berries|berry|strawberr|blueberr|raspberr|orange|lemon|lime|tomato|tomatoes|spinach|broccoli|cauliflower|carrot|carrots|zucchini|courgette|pepper|peppers|onion|garlic|mushroom|mushrooms|eggplant|aubergine|cabbage|kale|lettuce|salad|avocado|peas|green bean|beans|corn|sweet potato|potato|potatoes|pumpkin|squash|cucumber|celery|fruit|vegetable)\b')
starch=re.compile(r'\b(rice|pasta|noodle|noodles|bread|quinoa|couscous|bulgur|barley|oat|oats|flour|tortilla|wrap|potato|potatoes|sweet potato)\b')
rows=[]; seen=set(); stats={'raw':0,'incomplete':0,'alcohol':0,'nonmeal':0,'hard':0,'complex':0,'historical':0,'sweet':0,'processed':0,'balance':0,'photo':0,'selected':0,'duplicate':0}
for fn in ['recipes_raw_nosource_ar.json','recipes_raw_nosource_epi.json','recipes_raw_nosource_fn.json']:
 source=fn.split('_')[3].split('.')[0]
 data=json.loads((Path('raw')/fn).read_text())
 for rid,r in data.items():
  stats['raw']+=1; title=(r.get('title') or '').strip(); ings=[x.strip().replace('ADVERTISEMENT','').strip() for x in (r.get('ingredients') or []) if x and x.strip().replace('ADVERTISEMENT','').strip()]; ins=(r.get('instructions') or '').strip()
  if not title or not ings or not ins: stats['incomplete']+=1; continue
  text=norm(title+' '+' '.join(ings)); t=norm(title)
  if alcohol.search(text): stats['alcohol']+=1; continue
  if bad_title.search(t): stats['nonmeal']+=1; continue
  if hard_ing.search(text): stats['hard']+=1; continue
  if len(ings)>10 or len(ins)>3000: stats['complex']+=1; continue
  if re.search(r'\b(aspic|sweetbread|calves? brain|cervelle|mutton feet|pieds? de mouton|eel\b|anguille|alose|crepine)\b',text): stats['historical']+=1; continue
  if sweet_title.search(t) and not breakfast.search(t): stats['sweet']+=1; continue
  if re.search(r'\b(canned soup|condensed soup|cake mix|cookie mix|cool whip|velveeta|cheez whiz|spam\b|hot dog|bologna|packet|package dry)\b',text): stats['processed']+=1; continue
  score=sum([bool(protein.search(text)),bool(produce.search(text)),bool(starch.search(text) or re.search(r'\b(lentil|lentils|chickpea|chickpeas|bean|beans|pea|peas)\b',text))])
  if score<3: stats['balance']+=1; continue
  if not (r.get('picture_link') or '').strip(): continue
  key=norm(title)+'|'+norm(' '.join(ings))
  if key in seen: stats['duplicate']+=1; continue
  seen.add(key); stats['photo']+=1
  rows.append({'source_name':source,'source_recipe_id':rid,'title':title,'ingredients':ings,'instructions':ins,'picture_link':r.get('picture_link'),'selected':True,'enrichment_status':'pending_translation'}); stats['selected']+=1
Path('build').mkdir(exist_ok=True)
Path('build/equilibre_selected_v2.ndjson').write_text('\n'.join(json.dumps(r,ensure_ascii=False,separators=(',',':')) for r in rows)+'\n',encoding='utf-8')
for i in range(0,len(rows),500): Path('build').joinpath(f'chunk_{i//500:02d}.json').write_text(json.dumps(rows[i:i+500],ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print(json.dumps(stats)); print('ROWS',len(rows)); assert len(rows)==8043, f'Expected 8043 selected recipes, got {len(rows)}'
