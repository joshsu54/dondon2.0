"""Install verified LingyunValley15 results: copy to master Models/ and ArtLibrary/Turnarounds (hash-checked),
build ten-view sheets, the concept-vs-model comparison gallery and catalog entries. Run after verify_lingyun15.py:
  uv run --no-project --with pillow python install_lingyun15.py
The valley is an assembled scene (scene_views, not counted as an independent asset); the three camp buildings are.
"""
from pathlib import Path
import json,shutil,hashlib,html
from PIL import Image,ImageDraw,ImageFont
BATCH=Path(__file__).resolve().parents[1];ROOT=BATCH.parents[2];LIB=ROOT/'ArtLibrary'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def font(n):
    for f in ['C:/Windows/Fonts/msjh.ttc','/System/Library/Fonts/STHeiti Medium.ttc']:
        try:return ImageFont.truetype(f,n)
        except OSError:pass
    return ImageFont.load_default()
F=font(24);report=read(BATCH/'validation.json');res={a['asset']:a for a in report['assets']}
NAMES={'LingyunValley':'凌雲山谷地形','CampDormitory':'營地宿舍','CampHerbGarden':'營地藥圃','CampHexPavilion':'營地六角亭'}
for aid,r in res.items():
    m=BATCH/'Models'/aid/'v001';t=BATCH/'ArtLibrary/Turnarounds'/f'{aid}_v001'
    assert sha(m/f'{aid}_v001.blend')==r['blend_sha256'] and sha(m/f'{aid}_v001.fbx')==r['fbx_sha256'],aid
    dm=ROOT/'Models'/aid/'v001';dt=LIB/'Turnarounds'/f'{aid}_v001'
    if dm.exists() and sha(dm/f'{aid}_v001.blend')!=r['blend_sha256']:raise SystemExit(f'{dm} holds a different {aid}; not overwriting')
    shutil.copytree(m,dm,dirs_exist_ok=True);shutil.copytree(t,dt,dirs_exist_ok=True)
    for f in list(m.iterdir())+list(t.iterdir()):assert sha(f)==sha((dm if f.parent==m else dt)/f.name),f
    views=read(t/'views.json')['views'];sheet=Image.new('RGB',(1500,660),(237,240,233));d=ImageDraw.Draw(sheet)
    d.text((16,8),f'{NAMES[aid]} | {aid} v001',font=F,fill='#243d34')
    for i,v in enumerate(views):
        im=Image.open(t/v['file']).convert('RGB');im.thumbnail((290,290));sheet.paste(im,((i%5)*300+5,48+(i//5)*305))
    sheet.save(BATCH/f'{aid}_10views.jpg',quality=91)
# Concept vs model comparison (art direction vs authoritative geometry), one row per view.
refs=read(BATCH/'References/references.json')['images'];byview={}
for r in refs:byview.setdefault(r['view'],[]).append(r['file'])
LABEL={'01_front':'正前方／南','02_right':'右側／東','03_rear':'後方／北','04_left':'左側／西','05_front_right':'東南斜角','06_rear_right':'東北斜角',
       '07_rear_left':'西北斜角','08_front_left':'西南斜角','09_top':'正上方','10_high_front':'高角度正前'}
rows=[]
for v,label in LABEL.items():
    concepts=''.join(f'<figure><img loading="lazy" src="References/{html.escape(f)}" alt="概念 {v}"><figcaption>AI 概念參考：{html.escape(f)}</figcaption></figure>' for f in byview.get(v,[]))
    rows.append(f'<section><h2>{label} <small>{v}</small></h2><div class="pair"><div class="col">{concepts}</div><div class="col"><figure><img loading="lazy" src="ArtLibrary/Turnarounds/LingyunValley_v001/{v}.png" alt="模型 {v}"><figcaption>Blender 實際模型：固定幾何與配置</figcaption></figure></div></div></section>')
info=read(BATCH/'Models/LingyunValley/v001/model_info.json');fit=res['LingyunValley']['terrain_fit']
camps=''.join(f'<section><h2>{NAMES[a]} <small>{a}</small></h2><p><a href="Models/{a}/v001/{a}_v001.blend">Blender</a> · <a href="Models/{a}/v001/{a}_v001.fbx">FBX</a> · <a href="Models/{a}/v001/model_info.json">模型資料</a></p><img class="sheet" src="{a}_10views.jpg" alt="{NAMES[a]}十視圖"></section>' for a in ('CampDormitory','CampHerbGarden','CampHexPavilion'))
style='<style>body{margin:0;background:#edf0e9;color:#243d34;font:16px/1.65 system-ui,"Microsoft JhengHei",sans-serif}main{max-width:1280px;margin:auto;padding:30px 16px}section{background:#fff;padding:20px;border-radius:14px;margin:22px 0}small{color:#6b7f75;font-weight:400}a{color:#366c59}.pair{display:grid;grid-template-columns:1fr 1fr;gap:14px}@media(max-width:760px){.pair{grid-template-columns:1fr}}.col{display:grid;gap:10px}figure{margin:0}figure img,.sheet{width:100%;border-radius:8px;background:#ccc}figcaption{font-size:14px;color:#56685f}</style>'
page=(f'<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>凌雲山谷地形 15</title>{style}<main>'
      f'<h1>凌雲山谷地形 15</h1><p>依 13 張 AI 概念圖，在 TownLayout_09 的實際座標上建出連續草地、往北山門的坡地、柱狀崖壁、五座分層喀斯特岩峰與南側營地。左欄是概念參考（各視角之間會漂移），右欄是同一份 Blender 幾何的正交渲染，以右欄為準。</p>'
      f'<p>{info["dimensions_m"][0]:.0f} × {info["dimensions_m"][1]:.0f} m · 地形 {info["terrain_vertices"]:,} 頂點 · 匯出 {info["export_triangles"]:,} 三角面 · 植被 {info["vegetation_instances"]} 株 · 小鎮貼合取樣 {fit["surface_samples"]} 點、可見穿出 {fit["visible_pokes_above_top_surface_gt_2cm"]} 點</p>'
      f'<p><a href="Models/LingyunValley/v001/LingyunValley_v001.blend">Blender 場景</a> · <a href="Models/LingyunValley/v001/LingyunValley_v001.fbx">地形 FBX</a> · <a href="Models/LingyunValley/v001/vegetation_scatter_ue.json">植被散佈 JSON（UE 座標）</a> · <a href="README.md">說明</a> · <a href="validation.json">驗證結果</a> · <a href="../../index.html">回主圖庫</a></p>'
      +''.join(rows)+'<h2>南側營地獨立素材</h2>'+camps+'</main></html>')
(BATCH/'index.html').write_text(page,encoding='utf-8')
hist=LIB/'History/BeforeLingyunValley15';hist.mkdir(parents=True,exist_ok=True)
for rel in ['asset_catalog.json','index.html','完整建模清單.md']:
    if not (hist/rel).exists():shutil.copy2(LIB/rel,hist/rel)
catalog=read(LIB/'asset_catalog.json');new=[]
for a in ('CampDormitory','CampHerbGarden','CampHexPavilion'):
    vs=read(LIB/'Turnarounds'/f'{a}_v001/views.json')['views'];inf=read(ROOT/'Models'/a/'v001/model_info.json')
    new.append({'id':a,'name':NAMES[a],'category':'宗門營地','source_version':'v001','source_path':f'Models/{a}/v001','blend':f'../Models/{a}/v001/{a}_v001.blend','fbx':f'../Models/{a}/v001/{a}_v001.fbx',
                'preview':f'Turnarounds/{a}_v001/05_front_right.png','views':[f'Turnarounds/{a}_v001/'+v['file'] for v in vs],'status':'程序化外觀原型；待引擎驗證','unreal_import_verified':False,'uv_baked':False,'collision_ready':False,'lod_ready':False})
sv=read(LIB/'Turnarounds/LingyunValley_v001/views.json')['views']
new.append({'id':'LingyunValley','name':NAMES['LingyunValley'],'category':'配置場景','source_version':'v001','source_path':'Models/LingyunValley/v001','blend':'../Models/LingyunValley/v001/LingyunValley_v001.blend',
            'fbx':'../Models/LingyunValley/v001/LingyunValley_v001.fbx','preview':'Turnarounds/LingyunValley_v001/05_front_right.png','views':[],'scene_views':[f'Turnarounds/LingyunValley_v001/'+v['file'] for v in sv],
            'status':'對齊 TownLayout_09 的地形外觀原型；UE 匯入、碰撞與導航未驗證','unreal_import_verified':False})
ids={e['id'] for e in new};catalog['entries']=[e for e in catalog['entries'] if e['id'] not in ids]+new
old=(catalog['model_asset_sets'],catalog['consistent_turnaround_images'])
catalog['model_asset_sets']=sum(bool(e.get('views')) for e in catalog['entries']);catalog['consistent_turnaround_images']=sum(len(e.get('views',[])) for e in catalog['entries'])
catalog['assembled_scenes']=catalog.get('assembled_scenes',3)+(0 if 'LingyunValley' in {e['id'] for e in catalog['entries'] if e.get('scene_views') and e['id']!='LingyunValley'} else 1)
catalog['updated']='2026-10-23';link='ExpansionBatches/LingyunValley15/index.html'
if link not in catalog.setdefault('supplemental_batches',[]):catalog['supplemental_batches'].append(link)
write(LIB/'asset_catalog.json',catalog)
p=LIB/'index.html';s=p.read_text(encoding='utf-8')
s=s.replace(f'{old[0]} 組素材各有 10 張參考圖，共 {old[1]} 張',f'{catalog["model_asset_sets"]} 組素材各有 10 張參考圖，共 {catalog["consistent_turnaround_images"]} 張')
if link not in s:
    s=s.replace('</nav>',f' · <a href="{link}">凌雲山谷 15</a></nav><section><h2>凌雲山谷地形 15</h2><p>依 AI 概念圖建出的連續山谷地形與南側營地；概念圖與模型逐視角對照。</p><a href="{link}">開啟對照圖庫</a><img class="hero" src="Turnarounds/LingyunValley_v001/10_high_front.png" alt="凌雲山谷高角度正前"></section>',1)
p.write_text(s,encoding='utf-8')
write(BATCH/'inventory.json',{'batch':'LingyunValley15','date':'2026-10-23','scene':'LingyunValley v001 (10 scene views)','new_asset_sets':3,'new_views':30,
      'assets':[{'asset':a,'name_zh':NAMES[a],'blend_sha256':res[a]['blend_sha256'],'fbx_sha256':res[a]['fbx_sha256']} for a in res]})
print('INSTALLED; catalog',old,'->',(catalog['model_asset_sets'],catalog['consistent_turnaround_images']),'scenes',catalog['assembled_scenes'])
