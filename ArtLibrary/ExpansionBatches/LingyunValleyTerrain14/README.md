# 凌雲山谷地形研究 14

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
