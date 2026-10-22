# 食肆客棧（TownInn）：10 張建模前概念參考圖

建模前先產生。依提示詞寫成設計規格，在暫存場景排出草模，以接近 Codex image_gen 概念圖的柔光棚拍風格（淺灰無縫背景、暖色主光、接地陰影、透視鏡頭）渲染十個角度。雲端環境沒有 AI 生圖模型，所以這些不是 AI 繪圖；提示詞保留在 `prompts.json`，之後可改用生圖工具重新產生。

- 設計：Two-storey 12 x 9 m inn: red lacquered columns, open lattice front, dining hall with five tables, counter and wine shelf, straight stair, three upstairs guest rooms with beds, front balcony, blank signboard, two red lanterns, tiled gable roof and a rear kitchen annex with stove, woks and chimney.
- 尺寸：Approx. 13.8 x 13 x 9.6 m; floor-to-floor 3.4 m; stair 17 risers of 0.2 m.
- 正面＝Blender -Y；主造型依據為 05 右前斜角。風格參考：`ArtReferences/HerbalStall/concept.png`、`ArtReferences/Blacksmith_10Views/`。

## 圖片索引

1. [正面](01_front.png)
2. [右側](02_right.png)
3. [背面](03_rear.png)
4. [左側](04_left.png)
5. [右前斜角](05_front_right.png)
6. [右後斜角](06_rear_right.png)
7. [左後斜角](07_rear_left.png)
8. [左前斜角](08_front_left.png)
9. [垂直俯視](09_top.png)
10. [正面高角度](10_high_front.png)

模型：`Models/TownInn/v001/`；同模型十視圖：`ArtLibrary/Turnarounds/TownInn_v001/`。這十張圖已作為參考圖片物件放進 .blend 的 `80_Concept_References` 集合（不渲染、不匯出）。
