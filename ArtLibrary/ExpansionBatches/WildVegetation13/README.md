# 野外植被與岩石 13

補齊《完整建模清單》D 區「普通松、竹子、灌木、草叢」與「山石／峭壁」中仍待製作的植被與小岩石，共 5 組獨立素材：
普通松 CommonPine、竹叢 BambooClump、野灌木 WildShrub、苔石組 MossBoulderSet、碎石堆 ScreePile。

每組交付 Blender、FBX、10 張 1024 × 1024 PNG、十視圖總覽、model_info.json、views.json，以及重開與 FBX 回匯驗證紀錄。

## 製作方式

- 全部以 `BlenderSource/build_wild13.py` 程序化建模，固定亂數種子，可在 Blender 5.2 重建；沒有使用 AI 生成模型或 AI 概念圖。
- 色彩沿用山景 07 與宗門 04：玉灰岩、深綠植被、暖木樹皮。非金屬材質把鏡面反射降到 0.15，避免攝影棚面光把深綠洗成淡薄荷色。
- 1 Blender 單位 = 1 m，正面 -Y，根物件在底部中心。`01_Editable_Asset` 為可編輯分件；`90_Studio_Not_Exported` 為相機與燈光，不匯出 FBX。
- 十視圖為正前、右、後、左、四個斜角、頂視、高前視，均由同一份幾何渲染（Cycles，24 取樣＋降噪）。

## 模型規格

| 素材 | 尺寸 X × Y × Z（m） | 三角面 | 分件 | 重點 |
| --- | --- | ---: | ---: | --- |
| 普通松 CommonPine | 5.81 × 5.54 × 7.29 | 17,864 | 14 | 直立主幹、五條板根、七層枝、13 團雲片松針；最低枝葉約離地 1.5 m 以上 |
| 竹叢 BambooClump | 3.88 × 3.81 × 5.98 | 22,166 | 37 | 11 根帶節竹稈（2 根老竹）、2,762 片竹葉、3 支竹筍、土丘 |
| 野灌木 WildShrub | 1.86 × 1.68 × 1.31 | 6,124 | 11 | 9 團封閉葉團、7 支木質莖、36 朵淡玫瑰色小花 |
| 苔石組 MossBoulderSet | 3.30 × 2.16 × 1.52 | 2,656 | 7 | 1 大 6 小，平面切割岩面，平底貼地，朝上面帶苔 |
| 碎石堆 ScreePile | 2.20 × 1.80 × 0.50 | 1,738 | 77 | 76 顆獨立碎石＋碎石土丘核心 |

## 使用限制

- 植被為靜態網格，沒有風動形態鍵；需要搖曳時可參照 MountainWind07 的 WindPine 做法另存新版本。
- 竹葉是單面葉片，Unreal 需要雙面材質；松針雲片、灌木葉團與岩石為封閉網格。
- 苔蘚是材質內依法線朝上的遮罩，FBX 只帶岩石基本色；程序材質尚未烘焙成貼圖。
- 碎石堆每顆石頭都是獨立分件，可拆開散佈；底下的碎石土丘為獨立物件。
- UV／貼圖烘焙、碰撞、LOD、Unreal 匯入與場景配置均未完成。

## 重建與驗證

```sh
blender --background --python-exit-code 1 --python BlenderSource/build_wild13.py
blender --background --python-exit-code 1 --python BlenderSource/verify_wild13.py
uv run --with pillow python BlenderSource/install_wild13.py
```

建模腳本遇到該資產的 views.json 會跳過，不會覆寫既有成果；修改時請另存 v002。安裝腳本只在驗證通過後執行，會把批次成果複製到主目錄 `Models/` 與 `ArtLibrary/Turnarounds/` 並比對雜湊，並在 `ArtLibrary/History/BeforeWildVegetation13` 先備份索引。
