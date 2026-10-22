# 小鎮畫風修整 12｜2026-10-18

以 Claude 分支 `claude/zealous-dirac-g9r8gd` 的 `70d3fa4` 為來源，配合使用者「根據過去的畫風做修改」的要求，延用宗門核心建設 04 的青綠瓦、暖木、淺石、淡玉配色與柔光棚拍。沒有直接覆寫 Claude 原檔；來源及概念圖在 SourceSnapshot，並有逐檔 SHA-256。

## 內容與範圍

- 小鎮場景實際使用的 18 項 Claude 素材各自另存 v002，皆附可編輯 .blend、FBX、10 張 1024×1024 PNG、views.json 和 model_info.json，共 180 張獨立素材圖。
- TownLayout v004 另有 10 張場景視圖及 4 張預覽，場景圖片不替代單件十視圖。
- 本批涵蓋客棧、水井、公告板、牌樓、竹圍籬／轉角／院門、竹簍、陶甕、柴堆、木箱、食材箱、穀袋、石欄杆、荷花池、出生石台及兩款路口。Claude 的其他廚房道具及未使用的道路模組尚未納入這次修整。
- 11 件保留原幾何，修改材質及棚拍設定。牌樓另修幾何：中央柱距 2.6 → 4.4 m，基座間淨寬約 1.8 → 3.6 m，中央屋頂與橫梁同步延伸，側間平移但柱徑維持。

另兩件路口修整了相交的路緣石：改成封閉的 L 形整體轉角，避免重疊表面，並把路緣高度調成 0.32 m，與直道路段一致。

荷花池另外分開五片共面的荷葉，避免重疊產生黑色閃面。

公告紙張增加分層、竹簍內草束分開、木箱橫框內縮 2 mm，移除三項來源素材的共面黑斑。

## 小鎮配置修正

- 庭院與荷花池向東移 3 m，避開東側路段；校準四個轉角，清除接頭重複柱與重複石欄柱。
- 院門雙扇向內開 90°，並增加從主街至院門的鋪面、緩坡與路緣開口。
- 補上客棧門前與水井前方的鋪面。北端 T 字路口封閉的一側不再標成出口。
- 場景預覽重新取景，頂視圖呈現整座小鎮。

## 畫風依據

`BlenderSource/style12.py` 的材質值與柔光配置取自既有 `SectCore04/BlenderSource/build_sect_core04.py`；使用 AgX、低飽和青綠瓦、暖木、淺石、淡玉及舊銅色。這是實際 Blender 材質和光線調整，並非圖片濾鏡。原有十張概念參考圖保留並打包至各 .blend；修改後十視圖重新從實際模型渲染。

## 重建與驗證

從專案根目錄執行，Blender 5.3.0 Beta 已驗證；執行前先備份已審閱版本。生成腳本會更新本批的 v002 / v004 工作成果，獨立材質素材若已有 views.json 則跳過；需要重做時應改新版本或另用隔離輸出目錄。

```sh
blender --background --threads 8 --python-exit-code 1 --python ArtLibrary/ExpansionBatches/TownRefinement12/BlenderSource/refine_town12.py -- paifang style-assets layout
blender --background --threads 8 --python-exit-code 1 --python ArtLibrary/ExpansionBatches/TownRefinement12/BlenderSource/verify_town12.py
python3 ArtLibrary/ExpansionBatches/TownRefinement12/BlenderSource/install_town12.py
python3 Tools/Handoff/verify_project.py
```

安裝腳本需要 Pillow；建模／驗證腳本只需 Blender 的 Python 環境。SourceSnapshot 是從 Git LFS 還原的實際原檔，重建不需登入 GitHub。各主交付檔與批次副本應有相同雜湊。

## 限制

這是美術原型。通行檢查只檢查牌樓中央、院門與新增步行鋪面的指定區域，不是全鎮角色碰撞／導航驗收。UV 烘焙、遊戲碰撞、LOD、Unreal 匯入與完整室內仍待製作。FBX 不包含棚拍燈光、相機或概念圖，也不等同已移植程序材質。
