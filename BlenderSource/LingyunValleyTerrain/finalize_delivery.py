"""Package the terrain study and its independently generated references."""
import json,shutil,hashlib,html,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
REF=ROOT/'ArtReferences/LingyunValleyTerrain_v001'
MODEL=ROOT/'Models/LingyunValleyTerrain/v002'
VIEWS=ROOT/'ArtLibrary/Turnarounds/LingyunValleyTerrain_v002'
BATCH=ROOT/'ArtLibrary/ExpansionBatches/LingyunValleyTerrain14'
BATCH.mkdir(parents=True,exist_ok=True)
prompts=json.loads((REF/'prompts.json').read_text(encoding='utf-8'))
labels=['正前方／南','右側／東','後方／北','左側／西','右前／東南','右後／東北','左後／西北','左前／西南','正上方／北朝上','高前視角']
names=[]
for record in prompts['images']:
    name=record['name'];names.append(name)
    src=Path(record['generated_source']);dest=REF/(name+'.png')
    if src.resolve()!=dest.resolve():shutil.copy2(src,dest)
    record['sha256']=hashlib.sha256(dest.read_bytes()).hexdigest()
(REF/'prompts.json').write_text(json.dumps(prompts,ensure_ascii=False,indent=2),encoding='utf-8')
assert len(names)==10
for source,dest in [(MODEL,BATCH/'Models'),(VIEWS,BATCH/'Turnarounds'),(REF,BATCH/'References')]:
    shutil.copytree(source,dest,dirs_exist_ok=True)
    for p in source.glob('*'):
        if p.is_file():assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256((dest/p.name).read_bytes()).digest()
cards=[]
for name,label in zip(names,labels):
    cards.append(f'<section><h2>{label}</h2><div class="pair"><figure><a href="References/{name}.png"><img loading="lazy" src="References/{name}.png" alt="{label}概念圖"></a><figcaption>AI 概念參考：造型與材質方向</figcaption></figure><figure><a href="Turnarounds/{name}.png"><img loading="lazy" src="Turnarounds/{name}.png" alt="{label}模型渲染"></a><figcaption>Blender 實際模型：固定幾何與配置</figcaption></figure></div></section>')
    
page='''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>凌雲山谷｜地形與十角度參考</title><style>*{box-sizing:border-box}body{margin:0;background:#edf0e9;color:#203d33;font:16px/1.7 system-ui}main{max-width:1400px;margin:auto;padding:28px}h1{font-size:32px}a{color:#236c59}nav{display:flex;gap:20px;flex-wrap:wrap}section{background:#fff;border-radius:14px;padding:20px;margin:24px 0}.pair{display:grid;grid-template-columns:1fr 1fr;gap:18px}figure{margin:0}img{display:block;width:100%;aspect-ratio:1;object-fit:contain;background:#dce1df}figcaption{padding:8px}p{max-width:950px}@media(max-width:700px){.pair{grid-template-columns:1fr}}</style></head><body><main><h1>凌雲山谷 · 地形研究 14</h1><p>10 張獨立概念參考 ＋ 同一個 Blender 模型的 10 張實際渲染。保留原有小鎮、山門與重建營地的位置，加入連續草地、土坡、岩山、碎石與植被。</p><p><strong>概念圖是美術目標，幾何會有差異；精確建模請以右側模型渲染與 .blend 為準。</strong>目前為外觀初模，尚未套入 UE，也未完成碰撞、導航、UV 烘焙或 LOD。</p><nav><a href="Models/LingyunValleyTerrain_v002.blend">開啟 Blender 原檔</a><a href="Models/LingyunValleyTerrain_v002.fbx">地形 FBX</a><a href="Models/validation.json">檢查報告</a><a href="References/prompts.json">生圖提示詞</a><a href="README.md">使用說明</a></nav>'''+''.join(cards)+'</main></body></html>'
(BATCH/'index.html').write_text(page,encoding='utf-8')
readme='''# 凌雲山谷地形研究 14

這一版先展示地形外觀與可編輯初模，沒有覆蓋 Unreal TownLayout_10。

- 開啟 `index.html` 對照 10 張 AI 概念圖與 10 張同模型渲染。
- `Models/LingyunValleyTerrain_v002.blend`：完整預覽場景，包含原有建築配置、可編輯地形、山峰、草木、燈光與相機。1 單位 = 1 公尺，北方 +Y，前方 -Y；為了對齊既有 UE 場景，保留世界座標，未重新置中。
- `Models/LingyunValleyTerrain_v002.fbx`：只匯出新增地形、山峰及環境點綴，不重複匯出原有建築。程序材質尚未烘焙，FBX 不會呈現所有 Blender 材質效果。
- Collection `00_ExistingSettlement_UE10` 是既有建築；`10_ContinuousTerrain` 是連續地面；`20_KarstPeaks` 是岩山；`30_GroundCoverAndFoothills` 是碎石與草木。
- 正前、右、後、左、四個斜角、正上、高前各一張；Blender 預覽皆 1024×1024。
- 概念圖使用內建 ImageGen 各自生成，保留原始解析度。它們並非精密多視圖，建築／山形細節可能漂移。提示詞與來源記於 `References/prompts.json`。
- 已驗證重新開檔、FBX 回匯物件數與尺寸、封閉地形邊、十張圖片與十個不同相機位置。地形有 4 個不影響渲染的孤立頂點，詳見 validation.json。
- 模型仍是初模：山體層紋、邊界與路肩需進一步雕修；未驗證角色通行、碰撞、導航、UE 材質或效能，不代表遊戲內地形問題全部修復。

## 重現

腳本位於專案 `BlenderSource/LingyunValleyTerrain/`。`import_context.py` 讀取由 UE 只讀匯出的 Settlement10.fbx；`build_terrain.py` 建立 v001；`refine_terrain_v002.py` 改良為 v002；`render_and_export_v002.py` 產生十角度與 FBX；`validate_v002.py` 回匯檢查。已有版本的建模腳本會拒絕覆寫。v001 是試作，請使用 v002。
'''
(BATCH/'README.md').write_text(readme,encoding='utf-8')
(MODEL/'README.md').write_text(readme,encoding='utf-8')
catalog_path=ROOT/'ArtLibrary/asset_catalog.json';catalog=json.loads(catalog_path.read_text(encoding='utf-8'))
if not any(e['id']=='LingyunValleyTerrain' for e in catalog['entries']):
    catalog['entries'].append({'id':'LingyunValleyTerrain','name':'凌雲山谷連續地形研究','category':'配置場景／地形','source_version':'v002','source_path':'Models/LingyunValleyTerrain/v002','blend':'../Models/LingyunValleyTerrain/v002/LingyunValleyTerrain_v002.blend','fbx':'../Models/LingyunValleyTerrain/v002/LingyunValleyTerrain_v002.fbx','preview':'Turnarounds/LingyunValleyTerrain_v002/05_front_right.png','views':['Turnarounds/LingyunValleyTerrain_v002/'+n+'.png' for n in names],'gallery':'ExpansionBatches/LingyunValleyTerrain14/index.html','status':'地形外觀初模；尚未整合 UE','unreal_import_verified':False,'uv_baked':False,'collision_ready':False,'lod_ready':False})
    catalog['assembled_scenes']+=1;catalog['consistent_turnaround_images']+=10;catalog['concept_reference_images']+=10
    catalog_path.write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
index=ROOT/'ArtLibrary/index.html';content=index.read_text(encoding='utf-8')
if 'LingyunValleyTerrain14/index.html' not in content:
    content=content.replace('</nav>',' · <a href="ExpansionBatches/LingyunValleyTerrain14/index.html">地形研究 14 · 十角度對照</a></nav><section><h2>凌雲山谷地形初模</h2><p>新增 10 張概念圖與 10 張實際模型預覽，未套入 UE。</p><a href="ExpansionBatches/LingyunValleyTerrain14/index.html">開啟對照圖庫與 Blender 原檔</a><img class="hero" src="Turnarounds/LingyunValleyTerrain_v002/05_front_right.png" alt="地形模型"></section>',1)
    index.write_text(content,encoding='utf-8')
handoff=ROOT/'HANDOFF.md';old=handoff.read_text(encoding='utf-8')
if not old.startswith('2026-10-23 地形研究'):
    handoff.write_text('2026-10-23 地形研究：新增 LingyunValleyTerrain v002 可編輯 Blender 初模與 FBX、10 張實際渲染、10 張內建 ImageGen 概念參考。入口 ArtLibrary/ExpansionBatches/LingyunValleyTerrain14/index.html。UE TownLayout_10 未改動；原版地形問題尚未在遊戲內修復。回匯與十視圖檢查見 Models/LingyunValleyTerrain/v002/validation.json。v001 為保留的試作。\n\n'+old,encoding='utf-8')
print(json.dumps({'gallery':str(BATCH/'index.html'),'references':len(names),'renders':len(list(VIEWS.glob('*.png'))),'batch_copies_hash_verified':True},ensure_ascii=True))
