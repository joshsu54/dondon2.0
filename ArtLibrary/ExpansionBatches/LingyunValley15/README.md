# 凌雲山谷地形 15

依使用者提供的 13 張 AI 概念圖（`References/*.webp`，來源與視角對應見 `references.json`），在 **TownLayout_09 的實際座標**上建出可替換 UE 灰色平地的山谷地形，並新做南側營地。開啟 `index.html` 逐視角對照概念圖與模型；概念圖之間會漂移，以模型渲染為準。

C: 那份 Codex 專案的批次 14 是同主題的另一份成果；這份在 D: 從頭建立，未參考或複製其檔案。

## 內容

| 項目 | 說明 |
| --- | --- |
| `Models/LingyunValley/v001` | 完整場景 .blend（含唯讀小鎮參考）、地形 FBX、植被散佈 JSON、model_info |
| 地形 | 95.6 × 169.7 m 圓角島；7.3 萬頂點連續草地，泥土小徑與路肩以 `dirt` 屬性控制 |
| 北坡 | 自然坡地升到山門平台（6.1 m），步道與石階嵌入坡中 |
| 崖壁 | 一圈柱狀石灰岩崖（深 11 m）＋ 154 塊沿邊岩石 |
| 岩峰 | 五座分層喀斯特岩柱群：東北 48 m（最高）、西北 40 m、東中 31 m、西中 28 m、西南 19 m |
| 南側營地 | 宿舍、藥圃、六角亭、128 塊石板路、8 座石燈 |
| 植被 | 383 株（松、竹叢、灌木、苔石、碎石），沿用 WildVegetation13；岩階頂另有小松 |
| 營地獨立素材 | 宿舍 CampDormitory（7.96 × 11.7 × 5.77 m）、藥圃 CampHerbGarden（7.48 × 8.9 × 1.46 m）、六角亭 CampHexPavilion（6.2 × 5.4 × 4.96 m），各自 .blend／FBX／十視圖 |

## 座標與 UE 對位

- Blender 1 單位 = 1 m，北方 +Y；UE 座標 = (x, −y, z) × 100。場景**未重新置中**，直接對齊 TownLayout_09。
- 小鎮由 `Unreal/Tools/export_town_context15.py` 從 UE 唯讀匯出（3,928 Actor），只作對位參考，不在 FBX 內。
- 地形在每個小鎮地面類表面（鋪面、台階、平台、地基）下方 3 cm，周圍 9 m 以土肩過渡到自然地形。UE 的兩塊地台 `TownLayout_v004_Terrain_Display_Island`、`TownLayout_v004_North_Terrace_Ground` 在本場景隱藏，由地形取代；放進 UE 時需要移除或隱藏這兩塊。
- FBX 只含新幾何（地形、崖壁、岩石、岩峰、營地、步道，773 個網格、30.6 萬三角面）。植被不重複匯出，改用 `vegetation_scatter_ue.json`（UE 座標、yaw、縮放，對應 `/Game/Art/WildVegetation08/Meshes/`）。
- 新營地與 UE 現有的 WildVegetation08 子關卡有重疊（例如 (−900, 5600) 的松樹落在營地附近），放進 UE 時應以這份散佈取代該子關卡。

## 驗證（`validation.json`）

- 重新開檔；地形頂點有限值、`dirt` 屬性存在。
- 小鎮貼合：在 2,636 個地面類表面取樣點中，地形高出可見頂面 2 cm 以上的點為 **0**（最大 1.7 cm）。夾在兩層鋪面之間或位於結構下方的點不可見，另列數字。
- 三棟營地建物根部與地形高度差為 0；五座岩峰與小鎮、山門平台都留有間隙。
- 383 株植被沒有落在禁區；散佈 JSON 數量相符。
- 場景 FBX 回匯 773 個網格、尺寸誤差 0；三棟營地 FBX 回匯尺寸誤差小於 0.002 mm。
- 場景與三棟營地各 10 張 1024 px、互不相同的圖。

**未驗證：** UE 匯入、地形碰撞與導航、PIE 通行、UV／貼圖烘焙（程序材質，FBX 只帶基本色）、LOD。

## 修正紀錄

- 第一次建置時，附加進來的小鎮參考還沒更新世界座標就被拿去建射線資料，導致山門平台、石階、休憩亭等物件被當成在原點，北坡蓋過山門平台最多 3.6 m。已在附加後強制更新場景。
- 石階一帶因網格內插會從下一級台階穿出（最多 0.5 m）；約束改取周圍 0.3 m 內最低表面後降為 0。
- 測試原先把「夾在兩層鋪面之間」也算成穿出，改為只計可見穿出，兩種數字都保留。

## 已知差距

- 岩峰比概念圖規整：概念圖的崖面更破碎、岩階上的樹更多，可再雕修。
- 宿舍側面格窗的窗框是實心板，看起來像打孔木板，可再修。
- 沿邊岩石比概念圖小，崖頂邊緣不如概念圖有份量。

## 重建

```sh
blender --background --python-exit-code 1 --python BlenderSource/import_context15.py -- <per-mesh FBX 資料夾>
blender --background --python-exit-code 1 --python BlenderSource/build_lingyun15.py -- camp
blender --background --python-exit-code 1 --python BlenderSource/build_lingyun15.py -- scene
blender --background --python-exit-code 1 --python BlenderSource/verify_lingyun15.py
uv run --no-project --with pillow python BlenderSource/install_lingyun15.py
```

建置腳本遇到已存在的 views.json 會跳過，不會覆寫；修改時請另存 v002。每個網格各自的 FBX 由 UE 工具重新產生，不放在交付資料夾。
