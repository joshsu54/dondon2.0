# 序章動態分鏡〈凌雲重開〉v002（含暫代聲音）

依 `Story/序章劇情動畫_凌雲重開.md` 第三節分鏡表製作的 Blender 動態分鏡（animatic），用來檢查節奏、鏡頭長度，以及小鎮與山頂宗門之間的距離。**這不是正式動畫**：角色、特效、山路與門扇都是暫代品。

## 檔案

| 檔案 | 內容 |
| --- | --- |
| `PrologueAnimatic_v002.blend` | 兩個場景：`Animatic3D`（3D 場景、攝影機、timeline markers）與 `AnimaticEdit`（剪輯：畫格＋鏡號字卡＋字幕＋時間碼） |
| `PrologueAnimatic_v002_preview_960x540.mp4` | 預覽影片，960×540、24 fps、H.264，AAC 立體聲 48 kHz，2:45（3960 格） |
| `animatic_info.json` | 鏡號、格數範圍、攝影機、對白、連結來源與世界座標配置 |
| `audio/` | 暫代聲音：`Amb_`／`SFX_`／`Music_temp_stem.wav`（全長 2:45 的環境音、音效、配樂分軌）與 `VO_<鏡號>_<n>.wav`（每句旁白、對白一個檔案） |
| `audio/audio_timing.json` | 每句台詞的開始時間、語音長度、字幕區間，以及是否超出鏡頭 |
| `README.md` | 本文件 |

- 生成腳本：`BlenderSource/Story/build_prologue_animatic.py`（Blender 背景模式；每次建立新的 `vNNN`，不覆寫舊版本）。
- 中間畫格：**沿用** `work/PrologueAnimatic/v001_frames/`（JPEG，3960 張）。v002 的 3D 場景和 v001 完全相同（腳本固定亂數種子，只改了剪輯與聲音），所以沒有重新算圖，建置時加了 `--frames work/PrologueAnimatic/v001_frames`。這個資料夾目前被 v001 和 v002 共用，刪除前請確認兩版影片都已經不需要重新合成。

### 重新產生

```bash
Tools/bin/blender -b --factory-startup --python BlenderSource/Story/build_prologue_animatic.py -- --frames work/PrologueAnimatic/v001_frames
Tools/bin/blender -b Models/PrologueAnimatic/vNNN/PrologueAnimatic_vNNN.blend --python BlenderSource/Story/build_prologue_animatic.py -- --render-frames
Tools/bin/blender -b Models/PrologueAnimatic/vNNN/PrologueAnimatic_vNNN.blend --python BlenderSource/Story/build_prologue_animatic.py -- --render-edit
```

不加 `--frames` 就會算到自己的 `work/PrologueAnimatic/vNNN_frames`。加 `--no-audio` 可以跳過聲音。`--render-frames` 可加上 `--range 0-1319`，用多個行程平行算圖；已經存在的畫格會跳過。

## 畫面上的燒錄資訊

- 左上：鏡號、短描述、設計長度（例如 `2-5 天暗，光柱落在出生石台，衝擊波（11s）`）。
- 下方：旁白、對白、音效提示的字幕。時間位置是預估值，用來檢查節奏，不代表配音長度。
- 右上：版本標籤。
- 最下列（Blender stamp）：`Marker`（鏡號）、`Timecode`（時:分:秒:格，第 0 格等於 0:00）、`Frame`。
- 時間碼和設計文件一致：第一場 0:00、第二場 0:30、第三場 1:05、第四場 1:40、第五場 2:15，結束於 2:45。

## 暫代聲音（v002 新增）

全部都是**暫代品**，只用來對節奏，不能當作正式音效或配音。

- **旁白、對白**：macOS 內建台灣中文語音。旁白用 Meijia，掌門用 Grandpa（台灣），鐵匠用 Eddy（台灣）。每句台詞從字幕開始時間播放；如果唸得比字幕久，字幕會延長到唸完（不會蓋到下一句）。主角的「……」和 5-4 的操作提示不出聲。5-2 掌門「輕聲」那句用較慢語速、較小音量。
- **音效與環境音**：用 numpy 合成。風聲（第一場、4-1、4-2、5-4）；鳥叫和遠處打鐵聲（第二場）；2-2 三下鐵鎚叮聲，對齊火星出現的時間，接著淬火的嗤聲；2-3 市集嘈雜聲；2-5 低頻轟鳴、靈光呼嘯聲、落地的轟聲，8.0 秒起全部**靜音到鏡頭結束**（照設計文件寫的「突然靜音」）；3-1 心跳；3-2 落地和滑腳；3-4 拔劍；4-1 腳步；4-2 牌匾吱呀聲；4-3 推門五下、踹門的砰聲；5-2 陣紋每亮一圈響一聲鈴；5-3 拉遠時的呼嘯聲；5-4 提示音。
- **配樂**：從 5-1 開始的和弦鋪底，5-2、5-3 逐層疊加，5-3 加上鼓點，5-4 的 0.8 秒標題出現時重擊，畫面在 4.8–5.7 秒淡出時配樂一起淡出。
- 所有聲音在 `AnimaticEdit` 裡是獨立的 sound strip（第 7–11 軌），可以直接調音量或換掉。

### 台詞長度檢查

電腦語音的 18 句台詞全部唸得完，沒有一句超出字幕或鏡頭。不過電腦語音比真人快，例如「後來……」只唸 0.6 秒，省略號幾乎不停頓。所以下表另外用 1.6 倍估算真人語速，列出可能太趕的地方。這只是粗估，正式配音後應該用實際錄音重新檢查。

| 鏡號 | 說話者 | 字幕區間（秒） | 語音長度 | 唸完時間／鏡頭長度 | 照 1.6 倍時長估算的唸完時間 |
| --- | --- | --- | --- | --- | --- |
| 1-1 | 旁白 | 2.0–7.5 | 2.3 s | 4.3 / 8 s | 5.7 s  |
| 1-2 | 旁白 | 1.0–9.0 | 4.8 s | 5.8 / 10 s | 8.7 s  |
| 1-3 | 旁白 | 1.5–5.0 | 0.6 s | 2.1 / 12 s | 2.4 s  |
| 1-3 | 旁白 | 6.0–10.0 | 1.0 s | 7.0 / 12 s | 7.6 s  |
| 2-4 | 鐵匠 | 2.0–7.5 | 2.6 s | 4.6 / 8 s | 6.2 s  |
| 3-2 | 掌門 | 3.3–5.8 | 2.2 s | 5.5 / 6 s | 6.9 s **超出鏡頭** |
| 3-3 | 掌門 | 0.4–2.6 | 1.5 s | 1.9 / 8 s | 2.8 s 超出字幕 |
| 3-3 | 掌門 | 2.8–5.2 | 1.5 s | 4.3 / 8 s | 5.3 s 超出字幕 |
| 3-3 | 掌門 | 5.4–7.8 | 1.6 s | 7.0 / 8 s | 8.0 s 超出字幕 |
| 3-4 | 鐵匠 | 0.4–3.6 | 3.0 s | 3.4 / 7 s | 5.3 s 超出字幕 |
| 3-4 | 掌門 | 4.4–6.8 | 1.2 s | 5.6 / 7 s | 6.3 s  |
| 3-5 | 掌門 | 0.8–7.2 | 4.2 s | 5.0 / 8 s | 7.5 s 超出字幕 |
| 4-1 | 掌門 | 0.4–7.6 | 3.5 s | 3.9 / 8 s | 6.0 s  |
| 4-4 | 掌門 | 0.4–3.8 | 1.5 s | 1.9 / 12 s | 2.8 s  |
| 4-4 | 掌門 | 4.0–7.4 | 1.3 s | 5.3 / 12 s | 6.1 s  |
| 4-4 | 掌門 | 7.6–11.8 | 3.1 s | 10.7 / 12 s | 12.6 s **超出鏡頭** |
| 4-5 | 掌門 | 2.4–4.8 | 1.5 s | 3.9 / 5 s | 4.8 s  |
| 5-2 | 掌門 | 1.5–6.0 | 1.1 s | 2.6 / 8 s | 3.3 s  |

## 製作方式與慣例

- 1 單位等於 1 公尺，24 fps，第 0–3959 格。每個鏡號在 `Animatic3D` 有一個同名 timeline marker，並綁定攝影機 `CAM_<鏡號>`。蒙太奇或正反打需要切機位時，使用 `CAM_<鏡號>a/b/c`，marker 名稱仍然是同一個鏡號。
- 既有模型都用 **library link** 連進來（相對路徑、唯讀），以 collection instance 擺放，**沒有修改任何既有模型檔**。連結時略過來源檔的 `Not_Exported`／`Studio` 等集合，也略過 TownLayout v002 裡空的預設 `Scene`（內含一個多餘的 Cube）。
- 角色是灰色人形方塊（身高 1.8 m、原點在腳底）。加上小色塊方便辨識：主角是藍色腰帶；老掌門顏色較深，有白鬍子和髮髻；鐵匠體型較寬，有棕色圍裙。頭部前方的小方塊表示臉的朝向。
- 角色和道具動作用線性關鍵格；攝影機用平滑曲線。

## 世界配置（暫定，供距離與高度檢查）

設計文件說小鎮與山頂之間的距離和高度差「還沒有規劃」。本版採用以下配置：

| 項目 | 位置 |
| --- | --- |
| TownLayout v002 | 原點；出生石台中心 (0, −3.3, 0.49)，北側出口 (0, 11.7, 1.32) |
| 山路暫代 | 小鎮北口以平路接到 y = 26，再用 156 階直線階梯升到 y = 104、z = 48（水平 78 m、升高 46.7 m、坡度約 31°、寬 3.6 m） |
| SectSummitPlateau | (0, 160, 0)，平台頂面 48 m |
| SectLayout v003 | (0, 150.5, 48)；山門在 y ≈ 135.5，修煉台座位在 (10, 162.6, 48.8) |
| CloudpiercerPeak | (0, 262, 0)，放大 2.4 倍（高約 163 m），立在平台北側作為孤峰主體 |
| MountainRidge | 三組，放大 2.6–3.4 倍，作為西、東、北側遠景 |
| LayeredCliff | 西側 (−30, 52) 放大 1.3 倍；東側 (26, 80) 放大 1.6 倍，夾住山路 |

從出生石台走到宗門山門，水平距離約 139 m，高度差約 48 m。如果正式要讓人感覺「高可摘星」，這個高度差偏小，可以拿這版當作比較基準。

## 各鏡頭素材與暫代品

「連結素材」都是 `Models/` 或 `ArtLibrary/ExpansionBatches/MountainWind07/Models/` 裡的原始檔案。「暫代」表示本檔案裡新做的方塊、平面或發光物件，物件名稱以 `PH_`、`CHR_`、`FX_` 開頭。

| 鏡號 | 連結素材 | 暫代品／缺口 |
| --- | --- | --- |
| 1-1 | CloudpiercerPeak、MountainRidge、SectSummitPlateau | 雲海是半透明平面卡片（`PH_Cloud_*`）；黑場淡入在 `AnimaticEdit` 裡做 |
| 1-2 | LayeredCliff（西）、WindPine（崖頂，使用原檔的 96 格風動循環）、LayeredCliff（東） | — |
| 1-3 | SectSummitPlateau、SectLayout v003、WindGrass（160 叢，散布在宗門內外）、WindPine、CloudpiercerPeak；下降到山腳時接到 TownLayout v002 | 山路階梯 `PH_Mountain_Stair_156_Steps` |
| 2-1 | TownLayout v002（內含 SpawnTown 出生廣場、WelcomingPine 迎客松、StoneLantern 石燈） | 石燈沒有另外做點亮效果 |
| 2-2 | TownLayout v002 的鐵匠鋪（鐵砧、淬火桶、爐灶） | 鐵匠 `CHR_Smith`；手上的鎚子是方塊（原本的 SmithHammer 留在工作台上沒有動）；火星是發光小球；白煙是半透明圓錐 |
| 2-3 | HerbalStall、DryingRack ×2、SalesCounter、MaterialShop | TownLayout v002 沒有市集地塊，這幾件**暫時擺在廣場西側**，位置待正式配置 |
| 2-4 | TownLayout v002（TownBench、TownWaymarker） | 主角 `CHR_Hero`；指路碑上的「凌雲宗 ↑」刻字還沒有做 |
| 2-5 | TownLayout v002、山景 | 天色變暗用世界背景與太陽強度關鍵格；靈光是發光球；光柱是發光圓柱；衝擊波是發光圓環；落地閃光是點光源。迎客松和石燈火焰不會被衝擊波吹動 |
| 3-1 | SpawnTown 出生石台（在 TownLayout 內） | 主角；掌心光紋是發光小圓片 |
| 3-2 | SpawnTown 木構牌樓（在 TownLayout 內） | 老掌門 `CHR_Elder`，從牌樓屋脊跳下、滑一下再站穩 |
| 3-3 | SpawnTown | 兩名角色；用三個機位 a/b/c 做正反打 |
| 3-4 | 鐵匠鋪（TownLayout 內）、BasicSword01 | 鐵匠探頭；掌門從背後抽劍 |
| 3-5 | BasicSword01 | 遞劍時劍柄朝上直立，特寫主角握住劍柄；劍上的缺口還沒有做 |
| 4-1 | LayeredCliff ×2、WindPine、CloudpiercerPeak | **山路長階為暫代方塊階梯**；用遠景、側面、背影三個機位做蒙太奇。從 4-1 起，主角背著另一份 BasicSword01 |
| 4-2 | SectLayout v003（SectGate、圍牆）、WindGrass | **歪斜牌匾** `PH_Crooked_Plaque` 掛在 SectGate 的空白名牌前，會輕微搖晃 |
| 4-3 | SectGate | **門扇** `PH_Gate_Door_L/R`（SectGate 沒有可開合的門，門軸是空物件）；掌門推門卡住後踹開 |
| 4-4 | SectLayout v003：SpiritHerbGarden、TrainingGround（含 TrainingDummy）、SectGrandHall、AlchemyHall（含 AlchemyFurnace） | 宗門模型仍是乾淨版本，只用 WindGrass 表示雜草；沒有荒廢材質、落葉、破牆 |
| 4-5 | SectLayout v003 | 兩名角色 |
| 5-1 | CultivationPlatform（SectLayout v003 內那一座）、MeditationCushion（另外連結，放在座台上） | 主角走上台後坐下 |
| 5-2 | CultivationPlatform、SpiritHerbSeedling ×6（另外連結，放大 2.2 倍、從低垂轉成抬起） | 陣紋是三個依序亮起的發光圓環；靈氣粒子是 36 顆發光小球；幼苗鏡頭用 `CAM_5-2b` |
| 5-3 | SectLayout v003、SectSummitPlateau、CloudpiercerPeak、MountainRidge | **秘境裂縫**是貼在孤峰北面的紅色發光長方塊，加上紅色點光源 |
| 5-4 | CloudpiercerPeak、雲海卡片；最後切回 5-1 機位 | **標題字卡**是 `AnimaticEdit` 的文字條（「修先溝八」「序章〈凌雲重開〉」）；淡出用黑色色塊；「按住〔打坐鍵〕開始修煉」也是文字條 |

## 已知限制

- 聲音全是暫代品，見上一節。
- 角色沒有骨架，只有方塊旋轉；繞圈、踹門、爬階梯都是示意動作。
- 劍的交接用兩份 BasicSword01：掌門手上那份在 3-5 結束時隱藏，主角背上那份從 4-1 開始出現。
- 山路是直線階梯，靠近平台邊緣處可能和平台的崖壁有少量穿插。正式山路模組（長階或坡路）完成後應該替換。
- 小鎮四周只有一塊大地面平面，沒有地形。
- 光線是 EEVEE 的單一太陽光加天空色，沒有做雲影和霧。
- 只在 Blender 5.3.0 Beta 驗證；還沒有匯入 Unreal Sequencer。
