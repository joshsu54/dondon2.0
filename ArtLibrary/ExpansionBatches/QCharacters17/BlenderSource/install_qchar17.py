"""Install verified QCharacters17: copy to master Models/ and ArtLibrary/Turnarounds (hash-checked), labelled design sheets,
ten-view sheets, batch gallery and catalog entries. Run after verify_qchar17.py:
  uv run --no-project --with pillow python install_qchar17.py
"""
from pathlib import Path
import json,shutil,hashlib,html,re
from PIL import Image,ImageDraw,ImageFont
BATCH=Path(__file__).resolve().parents[1];ROOT=BATCH.parents[2];LIB=ROOT/'ArtLibrary'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def font(n):
    for f in ['C:/Windows/Fonts/msjh.ttc','/System/Library/Fonts/STHeiti Medium.ttc']:
        try:return ImageFont.truetype(f,n)
        except OSError:pass
    return ImageFont.load_default()
import os
VER=os.environ.get('QCHAR_VERSION','v001');SUF='' if VER=='v001' else '_'+VER
RIGGED=VER>='v005'
IN_UNREAL={'QPlayerMale','QPlayerFemale'} if VER>='v006' else set()   # TownLayout_13 player pawns (Unreal/qplayer13_runtime.json)   # v005 = v004 geometry + skeleton and Idle/Walk actions (rig_qchar17.py)
rep=read(BATCH/f'validation{SUF}.json');assert len(rep['assets'])==12
for r in rep['assets']:
    aid=r['asset'];m=BATCH/'Models'/aid/VER;t=BATCH/'ArtLibrary/Turnarounds'/f'{aid}_{VER}'
    assert sha(m/f'{aid}_{VER}.blend')==r['blend_sha256'] and sha(m/f'{aid}_{VER}.fbx')==r['fbx_sha256'],aid
    dm=ROOT/'Models'/aid/VER;dt=LIB/'Turnarounds'/f'{aid}_{VER}'
    if dm.exists() and sha(dm/f'{aid}_{VER}.blend')!=r['blend_sha256']:raise SystemExit(f'{dm} holds a different {aid}; not overwriting')
    shutil.copytree(m,dm,dirs_exist_ok=True);shutil.copytree(t,dt,dirs_exist_ok=True)
    for f in m.rglob("*"):assert f.is_dir() or sha(f)==sha(dm/f.relative_to(m))   # v005 adds an anim/ folder
    for f in t.rglob("*"):assert f.is_dir() or sha(f)==sha(dt/f.relative_to(t))
    vs=read(t/'views.json')['views'];sh=Image.new('RGB',(1500,660),(237,240,233));d=ImageDraw.Draw(sh);d.text((16,8),f'{r["name_zh"]} | {aid} {VER}',font=font(24),fill='#243d34')
    for i,v in enumerate(vs):
        im=Image.open(t/v['file']).convert('RGB');im.thumbnail((290,290));sh.paste(im,((i%5)*300+5,48+(i//5)*305))
    sh.save(BATCH/f'{aid}{SUF}_10views.jpg',quality=91)
    if RIGGED:   # animation strip: eight walk frames from the side, four idle frames from the front
        af=read(t/'views.json')['animation_frames'];fs=[BATCH/f for k in ('walk_side','idle_front') for f in af[k]['files']]
        st=Image.new('RGB',(6*250,2*250+40),(237,240,233));d=ImageDraw.Draw(st);d.text((16,8),f'{r["name_zh"]} | 走路（側面 8 格）· 待機（正面 4 格）',font=font(22),fill='#243d34')
        for i,f in enumerate(fs):
            im=Image.open(f).convert('RGB');im.thumbnail((246,246));st.paste(im,((i%6)*250+2,40+(i//6)*250))
        st.save(BATCH/f'{aid}{SUF}_anim.jpg',quality=91)
# Labelled design sheets: names under each character at the x positions recorded by the lineup render.
DS='DesignSheets' if VER=='v001' else f'DesignSheets_{VER}'
lj=read(BATCH/DS/'lineup.json');F=font(30)
for name,labels in lj['label_x_fraction'].items():
    im=Image.open(BATCH/DS/(name+'.png')).convert('RGB');W,H=im.size;out=Image.new('RGB',(W,H+70),(237,240,233));out.paste(im,(0,0));d=ImageDraw.Draw(out)
    for aid,zh,fx in labels:
        x=fx*W;tw=d.textlength(zh,font=F);d.text((x-tw/2,H+16),zh,font=F,fill='#243d34')   # back view: positions already mirrored by the camera projection
    out.save(BATCH/DS/(name+'_labelled.jpg'),quality=92)
ids=[r['asset'] for r in rep['assets']];names={r['asset']:r['name_zh'] for r in rep['assets']}
cards=''.join(f'<section><h2>{html.escape(names[a])} <small>{a}</small></h2><p>身高 {r["height_m"]:.2f} m · {r["mesh_objects"]} 分件 · <a href="Models/{a}/{VER}/{a}_{VER}.blend">Blender</a> · <a href="Models/{a}/{VER}/{a}_{VER}.fbx">FBX</a> · <a href="Models/{a}/{VER}/model_info.json">模型資料</a></p><img class="sheet" src="{a}{SUF}_10views.jpg" alt="{html.escape(names[a])}十視圖">'+(f'<img class="sheet" src="{a}{SUF}_anim.jpg" alt="{html.escape(names[a])}動作格">' if RIGGED else '')+f'</section>' for a,r in ((r['asset'],r) for r in rep['assets']))
style='<style>body{margin:0;background:#edf0e9;color:#243d34;font:16px/1.65 system-ui,"Microsoft JhengHei",sans-serif}main{max-width:1280px;margin:auto;padding:30px 16px}section{background:#fff;padding:20px;border-radius:14px;margin:22px 0}small{color:#6b7f75;font-weight:400}a{color:#366c59}img{width:100%;border-radius:8px}</style>'
page=(f'<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Q 版人物 17</title>{style}<main>'
      '<h1>Q 版人物 17</h1><p>'+('約 2 頭身、身高 1.25 m' if VER=='v001' else '約 2.5 頭身、身高約 1.3–1.5 m、動漫大眼')+f'的 Q 版人物 12 位（目前 {VER}）：玩家男女、三位弟子、宗門長老與六位村民。全部由同一套程序化零件（身體、臉、髮型、服裝、道具）組成，畫風與比例一致；A 字站姿，'+(('已綁 17 骨骼骨架，含待機與走路循環動作（原地）；玩家男女已匯入 Unreal 的 TownLayout_13 當玩家角色，其餘尚未匯入。' if IN_UNREAL else '已綁 17 骨骼骨架，含待機與走路循環動作（原地），尚未匯入 Unreal。') if RIGGED else '尚未綁骨架。')+'設定圖與十視圖都是同一份 Blender 幾何的渲染，沒有使用 AI 生圖。</p>'
      '<p><a href="README.md">說明</a> · <a href="'+("validation.json" if VER=="v001" else f"validation_{VER}.json")+'">驗證結果</a> · <a href="../../index.html">回主圖庫</a></p>'
      f'<section><h2>設定圖（{VER}）</h2><img src="{DS}/lineup_front_labelled.jpg" alt="正面設定圖"><img src="{DS}/lineup_three_quarter_labelled.jpg" alt="斜角設定圖"><img src="{DS}/lineup_back_labelled.jpg" alt="背面設定圖"></section>'+(f'<section><h2>舊版 v001（保留）</h2><p>約 2 頭身、全黑小眼、短袍的第一版；使用者要求改為 v002。</p><img src="DesignSheets/lineup_front_labelled.jpg" alt="v001 設定圖"></section>' if VER!='v001' else '')+cards+'</main></html>')
(BATCH/'index.html').write_text(page,encoding='utf-8')
hist=LIB/'History/BeforeQCharacters17';hist.mkdir(parents=True,exist_ok=True)
for rel in ['asset_catalog.json','index.html']:
    if not (hist/rel).exists():shutil.copy2(LIB/rel,hist/rel)
cat=read(LIB/'asset_catalog.json');new=[]
for a in ids:
    vs=read(LIB/'Turnarounds'/f'{a}_{VER}/views.json')['views']
    new.append({'id':a,'name':names[a],'category':'Q 版人物','source_version':VER,'source_path':f'Models/{a}/{VER}','blend':f'../Models/{a}/{VER}/{a}_{VER}.blend','fbx':f'../Models/{a}/{VER}/{a}_{VER}.fbx',
                'preview':f'Turnarounds/{a}_{VER}/05_front_right.png','views':[f'Turnarounds/{a}_{VER}/'+v['file'] for v in vs],'status':('程序化角色；已綁骨架、含待機與走路動作，已在 UE TownLayout_13 當玩家角色' if a in IN_UNREAL else '程序化角色；已綁骨架、含待機與走路動作，未進引擎') if RIGGED else '程序化外觀原型；未綁骨架、未進引擎','unreal_import_verified':a in IN_UNREAL,'rigged':RIGGED})
cat['entries']=[e for e in cat['entries'] if e['id'] not in set(ids)]+new
cat['model_asset_sets']=sum(bool(e.get('views')) for e in cat['entries']);cat['consistent_turnaround_images']=sum(len(e.get('views',[])) for e in cat['entries']);cat['updated']='2026-10-24'
link='ExpansionBatches/QCharacters17/index.html'
if link not in cat.setdefault('supplemental_batches',[]):cat['supplemental_batches'].append(link)
(LIB/'asset_catalog.json').write_text(json.dumps(cat,ensure_ascii=False,indent=2),encoding='utf-8')
p=LIB/'index.html';s=p.read_text(encoding='utf-8')
s=re.sub(r'\d+ 組素材各有 10 張參考圖，共 \d+ 張',f'{cat["model_asset_sets"]} 組素材各有 10 張參考圖，共 {cat["consistent_turnaround_images"]} 張',s)
s=s.replace('QCharacters17/DesignSheets/lineup_front_labelled.jpg',f'QCharacters17/{DS}/lineup_front_labelled.jpg')
if link not in s:s=s.replace('</nav>',f' · <a href="{link}">Q 版人物 17</a></nav><section><h2>Q 版人物 17</h2><p>12 位 2 頭身人物：玩家、弟子、長老與村民。</p><a href="{link}">開啟人物圖庫</a><img class="hero" src="{link.rsplit("/",1)[0]}/{DS}/lineup_front_labelled.jpg" alt="Q 版人物設定圖"></section>',1)
p.write_text(s,encoding='utf-8')
(BATCH/f'inventory{SUF}.json').write_text(json.dumps({'batch':'QCharacters17','version':VER,'date':'2026-10-24','new_asset_sets':12,'new_views':120,'design_sheets':3,
    'assets':[{'asset':r['asset'],'name_zh':r['name_zh'],'height_m':r['height_m'],'blend_sha256':r['blend_sha256'],'fbx_sha256':r['fbx_sha256']} for r in rep['assets']]},ensure_ascii=False,indent=2),encoding='utf-8')
print('INSTALLED 12; catalog',cat['model_asset_sets'],cat['consistent_turnaround_images'])
