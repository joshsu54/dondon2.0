"""Build a portable library of current source models, renders and reference art.
No source asset is modified. Requires all five ten-view sets to be complete.
"""
import json
import shutil
import hashlib
import html
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LIB=ROOT/'ArtLibrary'
ASSETS=[
 ('WelcomingPine','迎客松','Models/WelcomingPine/v002','環境', '01_front_right.png'),
 ('SpawnPlaza','出生廣場模組組合','Models/SpawnTown/v001','地景／建築', '01_overview.png'),
 ('StarterHouse','新手民宅','Models/StarterHouse/v004','建築', '01_front_right.png'),
 ('Blacksmith','鐵匠鋪與工作道具','Models/Blacksmith/v001','建築／道具', '01_smithy_overview.png'),
 ('MaterialShop','雜貨／材料鋪','Models/MaterialShop/v001','建築／道具', '01_material_shop_overview.png'),
]
SCENES=[('TownLayout','出生小鎮配置（民宅＋鐵匠鋪）','Models/TownLayout/v002','場景組合','01_town_with_smithy.png')]
LIB.mkdir(exist_ok=True)
entries=[]
for asset_id,name,source,category,preview in ASSETS+SCENES:
    folder=ROOT/source; target=LIB/'Current'/asset_id
    target.mkdir(parents=True,exist_ok=True)
    for path in sorted(folder.iterdir()):
        if path.suffix.lower() in ('.blend','.fbx','.png','.json'):
            shutil.copy2(path,target/path.name)
    blends=list(target.glob('*.blend')); fbxs=list(target.glob('*.fbx'))
    assert len(blends)==1 and len(fbxs)==1
    turn=LIB/'Turnarounds'/f'{asset_id}_{folder.name}'
    views=[]
    if asset_id!='TownLayout':
        manifest=json.loads((turn/'views.json').read_text())
        views=[str((turn/name).relative_to(LIB)) for name in manifest['views']]
        assert len(views)==10 and all((LIB/p).exists() for p in views)
    entries.append({'id':asset_id,'name':name,'category':category,'source_version':folder.name,
        'source_path':source,'blend':str(blends[0].relative_to(LIB)),'fbx':str(fbxs[0].relative_to(LIB)),
        'preview':str((target/preview).relative_to(LIB)),'views':views,
        'status':'外觀原型；待遊戲資產整理','unreal_import_verified':False,
        'uv_baked':False,'collision_ready':False,'lod_ready':False})

reference_files=0
for source in sorted((ROOT/'ArtReferences').iterdir()):
    if not source.is_dir(): continue
    legacy=source.name in ('LogCabin_10Views','Blacksmith_10Views')
    target=LIB/'References'/('Legacy_AlternateStyle' if legacy else 'Current_Xianxia')/source.name
    target.mkdir(parents=True,exist_ok=True)
    for p in source.iterdir():
        if p.is_file() and p.suffix.lower() in ('.png','.jpg','.jpeg','.md','.txt','.json'):
            shutil.copy2(p,target/p.name)
            if p.suffix.lower() in ('.png','.jpg','.jpeg'): reference_files+=1

data={'target_engine':'Unreal Engine','workflow':'Art preparation first; game-system implementation paused',
      'model_asset_sets':len(ASSETS),'assembled_scenes':len(SCENES),'consistent_turnaround_images':sum(len(e['views']) for e in entries),
      'concept_reference_images':reference_files,'entries':entries,
      'note':'Concept references are not models. Town scene does not yet include the new materials shop.'}
(LIB/'asset_catalog.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

cards=[]
for e in entries:
    gallery=''.join(f'<a href="{html.escape(p)}"><img loading="lazy" src="{html.escape(p)}" alt="{html.escape(Path(p).stem)}"><span>{html.escape(Path(p).stem)}</span></a>' for p in e['views'])
    cards.append(f'''<section><div class="header"><h2>{html.escape(e['name'])}</h2><span>{html.escape(e['source_version'])} · 外觀原型</span></div>
    <a href="{e['preview']}"><img class="hero" src="{e['preview']}" alt="{html.escape(e['name'])}"></a>
    <p><a class="button" href="{e['blend']}">Blender 原檔</a> <a class="button" href="{e['fbx']}">FBX</a></p>
    <div class="views">{gallery}</div></section>''')
page='''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>修仙素材庫｜Unreal 美術準備</title><style>
*{box-sizing:border-box}body{margin:0;background:#142522;color:#e7e7dc;font:16px/1.65 -apple-system,BlinkMacSystemFont,"PingFang TC",sans-serif}
main{max-width:1200px;margin:auto;padding:40px 24px}h1{font-size:36px;margin:0}h2{margin:0;font-size:24px}p{color:#bccdc5}
.intro{border-bottom:1px solid #3a5148;padding-bottom:28px}.tag{color:#d0b784;letter-spacing:2px}section{margin:34px 0;padding:24px;background:#20352e;border:1px solid #3a5148;border-radius:14px}
.header{display:flex;justify-content:space-between;gap:20px;align-items:center;margin-bottom:18px}.header span{color:#cfbd94;font-size:14px}
.hero{width:100%;max-height:520px;object-fit:contain;background:#364840;border-radius:7px}a{color:#e2c891}.button{display:inline-block;padding:8px 18px;border:1px solid #8a815d;border-radius:6px;text-decoration:none}
.views{display:grid;grid-template-columns:repeat(5,1fr);gap:12px}.views a{font-size:12px;overflow:hidden;text-decoration:none}.views img{width:100%;display:block;border-radius:5px}.views span{display:block;padding:6px 0}
@media(max-width:700px){.views{grid-template-columns:repeat(2,1fr)}.header{display:block}main{padding:22px 12px}section{padding:14px}h1{font-size:27px}}
</style><main><div class="intro"><div class="tag">青瓦 · 木構 · 山間修仙</div><h1>修仙美術素材庫</h1>
<p>5 組模型原型 · 50 張同模型固定視角圖 · 1 組小鎮配置。所有連結使用本機檔案，無需連線。</p>
<p>目前是美術準備階段；尚未完成 UE 匯入、UV 烘焙、碰撞或 LOD。小鎮配置尚未加入新材料鋪。</p>
<a href="README.md">使用說明</a>　<a href="完整建模清單.md">完整建模清單</a>　<a href="Unreal交接規格.md">Unreal 交接規格</a>
</div>'''+''.join(cards)+'''<p>概念參考圖存於 References。Legacy_AlternateStyle 為早期其他風格參考，不代表目前採用的造型。</p></main></html>'''
(LIB/'index.html').write_text(page,encoding='utf-8')

manifest=[]
for p in sorted(LIB.rglob('*')):
    if p.is_file() and p.name not in ('checksums.json','library_validation.json'):
        manifest.append({'file':str(p.relative_to(LIB)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(LIB/'checksums.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
validation={'model_pairs':len(entries),'turnaround_images':sum(len(e['views']) for e in entries),
            'all_catalog_files_exist':all((LIB/e[k]).exists() for e in entries for k in ('blend','fbx','preview')),
            'concept_reference_images':reference_files,'unreal_import_verified':False}
assert validation['all_catalog_files_exist'] and validation['turnaround_images']==50
(LIB/'library_validation.json').write_text(json.dumps(validation,indent=2),encoding='utf-8')
delivery=ROOT/'Deliverables'; delivery.mkdir(exist_ok=True)
n=1
while (delivery/f'UnrealArtPrep_v{n:03d}.zip').exists(): n+=1
archive=delivery/f'UnrealArtPrep_v{n:03d}.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as z:
    for p in sorted(LIB.rglob('*')):
        if p.is_file(): z.write(p,Path('ArtLibrary')/p.relative_to(LIB))
with zipfile.ZipFile(archive) as z: assert z.testzip() is None
print(json.dumps({'library':str(LIB),'archive':str(archive),'archive_bytes':archive.stat().st_size,**validation},ensure_ascii=False))
