"""Read-only source inventory; writes only this versioned planning folder's reports."""
import json
from pathlib import Path
from collections import Counter

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
CAT = json.loads((ROOT / 'ArtLibrary/asset_catalog.json').read_text(encoding='utf-8'))
GROUPS = [
    ('BODY', '角色基底', '男修基底|女修基底', True),
    ('HAIR', '可替換髮型', '束髮髻|雙低髻|高馬尾|短髮|半束長髮|雙辮|道冠束髮|長老髮鬚組', True),
    ('CLOTH', '服裝套件', '男新手服|女新手服|男雜役服|女雜役服|男劍修服|女劍修服|男丹修服|女丹修服|男器修服|女器修服|長老袍|商販服|鐵匠圍裙服|採藥師服', True),
    ('ACC', '角色配件', '採集背簍|斗笠|髮簪|面具|護腕手套組|儲物袋', True),
    ('CREATURE', '獵物與敵人', '山兔|山豬|野狼|靈鹿|草木妖|石傀儡|劍靈首領|古樹首領', True),
    ('GEAR', '武器法器', '進階法劍|刀|長槍|法杖|弓|箭筒與箭組|盾|劍鞘|法戒|護身佩', False),
    ('ITEM', '修煉與掉落物', '靈石|丹瓶|丹藥|煉氣訣書冊|功法玉簡|符籙|種子袋|獸肉|獸皮|獸骨|妖丹|貢獻令牌', False),
    ('RESOURCE', '採集與種植', '靈蓮幼苗|靈蓮成長株|靈蓮成熟株|靈參幼苗|靈參成長株|靈參成熟株|採收後殘株|可採靈礦脈|採空礦脈|可採枯木', False),
    ('HOME', '洞府拼裝模組', '洞府入口|室內地板|室內直牆|室內轉角|洞頂|可開合洞府門', False),
    ('ASSESS', '選拔測資質', '測靈晶石|測靈台基座|資質榜框|選宗登記台', False),
    ('SECT', '宗門識別與特色', '劍宗徽記旗|丹宗徽記旗|器宗徽記旗|劍修試劍台|丹修育藥池|器修鍛造爐', False),
    ('REALM', '秘境拼裝與機緣', '秘境入口框|秘境石門|秘境地板|秘境直牆|秘境轉角|遺跡石柱|遺跡階梯|斷橋模組|機緣祭壇|普通寶箱|首領寶箱|地刺陷阱|倒塌柱|發光菌簇|晶簇|巨樹根|傳承石碑|遺寶座', False),
]
FIRST = {'BODY01','BODY02','HAIR01','HAIR02','CLOTH01','CLOTH02','CREATURE01','CREATURE02','ITEM01','ITEM02','ITEM04','ASSESS01','HOME01','HOME02','HOME03','HOME06'}
REUSE_IDS = '''StarterHouse Blacksmith MaterialShop HerbalStall DryingRack MortarPestle HerbPlanter AlchemyFurnace MeditationCushion StoneLantern TownWaymarker TownBench SmithAnvil SmithWorkbench QuenchBarrel WeaponDisplayRack SmithHammer BasicSword01 SmithTongs MedicineJar01 MaterialSack01 GoodsShelf SalesCounter JadeOre01 IronIngot01 SectGate SectGrandHall DiscipleResidence TrainingGround SpiritHerbGarden CultivationPlatform AlchemyHall ScriptureLibrary SectStorehouse MedicineCabinet ScrollShelf ReadingDesk StorageChest DiscipleBed SectWallStraight SectWallCorner CourtyardGate TimberStairFlight TrainingDummy SpiritHerbSeedling SpiritHerbYoung SpiritHerbMature MountainStoneStairs MountainTurnLanding CliffBoardwalk TimberSpanBridge MountainStonePath SpiritSpringPool BambooBasket BambooFence FenceGate NoticeBoard SpawnAltar TownPaifang TownRoadCrossroad TownRoadTJunction CommonPine BambooClump WildShrub MossBoulderSet ScreePile'''.split()
FIRST_REUSE = set('StarterHouse StorageChest DiscipleBed SpiritHerbGarden SpiritHerbSeedling SpiritHerbYoung SpiritHerbMature MeditationCushion BasicSword01 MaterialShop NoticeBoard AlchemyFurnace SmithWorkbench SpawnAltar'.split())
SCENES = ['新手聚落','低級狩獵採集區','選拔廣場','私人洞府與靈田','劍宗公共區','丹宗公共區','器宗公共區','竹林秘境','古代遺跡秘境','靈礦洞秘境']
ICON_GROUPS = {'五行靈根':5,'天賦':12,'境界':8,'功法技能':12,'物品':40,'宗門徽記':3}
PANELS = ['創角','角色資質','背包裝備','修煉','商店','宗門選拔','洞府靈田','煉丹煉器','任務貢獻','秘境入口與倒數']
FX = ['打坐聚氣','突破','採集提示','採礦碎屑','普通命中','劍氣','受擊','丹爐火煙','煉器火花','測靈五行變色','秘境傳送','機緣發光']
HUMAN_ANIMS = '待機 走路 跑步 左轉 右轉 起跳 空中 落地 拾取 採藥 挖礦 伐木 播種 澆灌 打坐入座 打坐循環 打坐起身 普攻 施法 受擊 倒地 打鐵 煉丹 睡眠'.split()
CREATURE_ANIMS = '待機 行走 奔跑 警戒 攻擊 受擊 死亡 特殊動作'.split()

def check_file(rel):
    p = (ROOT / 'ArtLibrary' / rel).resolve()
    if not p.is_file():
        return {'path': str(p.relative_to(ROOT)), 'exists':False, 'lfs_pointer':False}
    with p.open('rb') as f:
        ptr = f.read(80).startswith(b'version https://git-lfs.github.com/spec/v1')
    return {'path': str(p.relative_to(ROOT)), 'exists':True, 'lfs_pointer':ptr}

new = []
for prefix, label, names, ortho in GROUPS:
    for i, name in enumerate(names.split('|'),1):
        key = f'{prefix}{i:02d}'
        new.append({'id':key,'name':name,'category':label,'first_batch':key in FIRST,
                    'concept_sheets':1,'extra_orthographic_sheets':int(ortho),'model_sets':1,
                    'model_render_views':10,'status':'planned_not_modeled'})
byid = {e['id']:e for e in CAT['entries']}
assert len(REUSE_IDS) == len(set(REUSE_IDS))
assert FIRST <= {r['id'] for r in new}
assert FIRST_REUSE <= set(REUSE_IDS)
reuse = []
for key in REUSE_IDS:
    e = byid[key]
    reuse.append({'id':key,'name':e['name'],'first_batch':key in FIRST_REUSE,
                  'blend':check_file(e['blend']),'fbx':check_file(e['fbx']),
                  'views_existing':len(e.get('views',[])),
                  'status':'reuse_candidate_requires_scale_material_interaction_review'})
extra = []
for name in ('CampDormitory','CampHerbGarden','CampHexPavilion'):
    extra.append({'id':name, 'blend':check_file(f'../Models/{name}/v001/{name}_v001.blend'),
                 'fbx':check_file(f'../Models/{name}/v001/{name}_v001.fbx'),
                 'status':'extra_existing_candidate_not_in_main_catalog',
                 'source':'ArtLibrary/ExpansionBatches/LingyunValley15/inventory.json'})
assert all(x[k]['exists'] and not x[k]['lfs_pointer'] for x in reuse+extra for k in ('blend','fbx'))
new_count = len(new)
concepts = sum(r['concept_sheets'] + r['extra_orthographic_sheets'] for r in new) + 2 + len(SCENES)
summary = {'new_model_sets':new_count,'selected_reuse_sets':len(reuse),
           'planned_model_sets':new_count+len(reuse),'first_batch_new':len(FIRST),
           'first_batch_reuse':len(FIRST_REUSE),'concept_sheets':concepts,
           'new_model_render_views':10*new_count,'icons':sum(ICON_GROUPS.values()),
           'interface_design_sheets':len(PANELS),'effect_design_sheets':len(FX),
           'image_deliverables_total':concepts+10*new_count+sum(ICON_GROUPS.values())+len(PANELS)+len(FX),
           'concept_sheets_created':2,'new_models_created':0,
           'first_batch_concept_sheets':sum(r['concept_sheets']+r['extra_orthographic_sheets'] for r in new if r['first_batch'])+2+4,
           'human_animation_clips':len(HUMAN_ANIMS),'creature_animation_clips':len(CREATURE_ANIMS)*8}
data = {'date':'2026-10-24','scope':'首期規劃假設：1 新手區、3 宗門、3 秘境主題；不是完整正式服內容量',
        'summary':summary,'new_assets':new,'reuse_assets':reuse,'extra_existing_assets':extra,
        'scene_boards':SCENES,'icon_groups':ICON_GROUPS,'interface_panels':PANELS,
        'effects':FX,'human_animations':HUMAN_ANIMS,'creature_animation_template':CREATURE_ANIMS}
(OUT/'asset_plan.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# Q 版修仙首期美術逐項清單','',
       '本表由 `build_plan.py` 產生，來源為本版規劃與現有素材索引。數量是製作預算，不代表已完成。', '',
       '## 新增模型與設計圖','',
       '| ID | 資產 | 分類 | 第一批 | 概念圖 | 補充正交設定圖 | 模型十視圖 |',
       '| --- | --- | --- | --- | ---: | ---: | ---: |']
for r in new:
    lines.append(f"| {r['id']} | {r['name']} | {r['category']} | {'是' if r['first_batch'] else '後續'} | 1 | {r['extra_orthographic_sheets']} | 10 |")
lines += ['', '## 選用既有模型','', '下列為沿用候選，已檢查 blend／FBX 檔案存在且不是 LFS 指標；未逐件重驗引擎可用性。現有十視圖不計入新增圖片工作量。','',
          '| ID | 資產 | 第一批 | 現有十視圖數 |', '| --- | --- | --- | ---: |']
for r in reuse:
    lines.append(f"| {r['id']} | {r['name']} | {'是' if r['first_batch'] else '後續'} | {r['views_existing']} |")
lines += ['', '## 主索引外另有的素材','',
          'LingyunValley15 的 CampDormitory、CampHerbGarden、CampHexPavilion 另有 3 組獨立模型與批次記載的 30 張十視圖。可替代同用途建築，但不與本表已選用的相同用途資產重複加算。LingyunValley 場景的 10 張預覽另列，不當成 10 個新模型。', '',
          '## 圖片與動作明細','',
          '- 場景設計圖：'+'、'.join(SCENES),
          '- UI 圖示：'+'、'.join(f'{k} {v}' for k,v in ICON_GROUPS.items()),
          '- 介面設計稿：'+'、'.join(PANELS),
          '- 特效設計稿：'+'、'.join(FX),
          '- 人形共用動作：'+'、'.join(HUMAN_ANIMS),
          '- 每種生物預留動作：'+'、'.join(CREATURE_ANIMS), '',
          '動畫、骨架、材質貼圖、特效實作、地圖配置與遊戲功能工作量獨立於模型件數。服裝、髮型等套件可在同檔案中有多個分件；若之後拆成獨立交付資產，需各補十視圖並更新統計。']
(OUT/'逐項美術清單.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
audit={'catalog_entries':len(CAT['entries']),'catalog_assets_with_views':sum(bool(e.get('views')) for e in CAT['entries']),
       'catalog_view_paths':sum(len(e.get('views',[])) for e in CAT['entries']),
       'selected_reuse_files_exist_and_not_lfs':True,'extra_three_model_files_exist_and_not_lfs':True,
       'unique_new_ids':len({r['id'] for r in new})==len(new),
       'summary':summary,'note':'File inventory and plan arithmetic only; no new 3D models, UE or Blender acceptance claimed.'}
(OUT/'planning_validation.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(audit,ensure_ascii=False,indent=2))
