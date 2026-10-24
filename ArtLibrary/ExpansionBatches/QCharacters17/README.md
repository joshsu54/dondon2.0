# Q 版人物 17

## v006（目前版本）：可匯入 Unreal 的 FBX

外觀、骨架、權重、動作都與 v005 相同，只改 FBX 匯出，因為 v005 的 FBX 匯入 Unreal 後骨架小了 100 倍（v005 的 Blender 檔本身沒問題）：

- **單位：** v005 的 FBX 用公尺，並在 Armature 節點帶 ×100 縮放。Unreal 把 Armature 當成骨架物件略過，縮放也跟著丟掉，網格大小正確，骨架卻只剩 1/100，畫面上角色縮成約 1.5 cm。改用 `FBX_SCALE_ALL` 也不行：它寫出公尺加 UnitScaleFactor 100，Unreal 只換算了網格。v006 在匯出前把骨頭、頂點、Solidify 厚度、骨盆位移曲線都乘 100，以公分寫出 FBX（UnitScaleFactor 1、所有節點縮放 1）。這只在記憶體裡做，`.blend` 仍是 1 單位 = 1 公尺。
- **名稱：** 分件 `Head`、`Neck` 與骨頭 head、neck 同名（Unreal 不分大小寫），Unreal 會把骨頭改成 head2、neck1。v006 把這兩個分件改名為 `Head_Mesh`、`Neck_Mesh`。

產生：`QRIG_VERSION=v006` 執行 `rig_qchar17.py`、`verify_rig17.py`，再以 `QCHAR_VERSION=v006` 執行 `install_qchar17.py`。12 位通過驗證（`validation_v006.json`）：v005 的全部檢查，加上分件名稱不得與骨頭同名。玩家男女已匯入 Unreal 的 `TownLayout_13`，見 `Unreal/qplayer13_runtime.json`。

## v005：骨架與待機／走路動作（FBX 不適合 Unreal，請用 v006）

外觀與 v004 完全相同（直接讀 `Models/<ID>/v004/` 的幾何），加上骨架、蒙皮與兩段原地循環動作。由 `BlenderSource/rig_qchar17.py` 產生，`verify_rig17.py` 驗證。

- **骨架：** 17 根骨頭，命名比照 Unreal：root › pelvis › spine › neck › head；spine › upperarm › lowerarm › hand；pelvis › thigh › calf › foot（_l 為角色左側 +X）。骨架物件取名 `Armature`，匯入 Unreal 時不會多出一根根骨。
- **蒙皮：** 頭、臉、頭髮、手、手持道具、鞋為剛性綁定；袖子在手肘混合上下臂，腿在膝蓋與腳踝混合，袍子在腰部混合 spine／pelvis，臀部以下跟著兩腿擺動（下襬 80%）。背劍、藥簍、披肩跟 spine，腰帶與葫蘆跟 pelvis。
- **動作（24 fps、原地、無 root motion）：**
  - `Idle` 49 格（2 秒）：呼吸前後、頭部輕擺、空手的手臂微張。
  - `Walk` 25 格（1 秒兩步）：大腿前後 22°、擺腿時屈膝、腳掌放平、手臂反向擺動 26°（拿道具的手 9°）、骨盆扭轉並下沉，讓著地的腳貼地。
- **預覽：** 每位的動作格（側面走路 8 格、正面待機 4 格）在 `Models/<ID>/v005/anim/`，圖庫頁有合成圖 `<ID>_v005_anim.jpg`。設定圖 `DesignSheets_v005/` 是 12 位都停在走路第 7 格（最大步幅）。十視圖為 A 字靜止姿勢。
- **驗證（`validation_v005.json`，12 位通過）：** 17 根骨頭；每個分件都綁到骨架，所有頂點權重和為 1；兩段動作首尾一致可循環；靜止姿勢尺寸與 v004 相同；兩段動作取樣時，手與袖、鞋與腿、頭與頸的距離都沒有拉開；走路時著地腳最高 3.8 mm、鞋底最多陷入 7.5 mm、單腳前後移動約 0.30 m；FBX 回匯保留骨架、分件數、尺寸與兩段動作；十張 1024 視圖與 12 張動作格存在。
- **未做：** Unreal 匯入、重定向與遊戲內播放；頭髮與袍子沒有物理擺動（只是蒙皮）；手臂與袍子、頭髮與肩膀是否在某些格穿插，沒有逐格量測；UV 烘焙、LOD、與門和家具的比例檢查。

重建：

```sh
blender --background --python-exit-code 1 --python BlenderSource/rig_qchar17.py
blender --background --python-exit-code 1 --python BlenderSource/rig_qchar17.py -- lineup
blender --background --python-exit-code 1 --python BlenderSource/verify_rig17.py
QCHAR_VERSION=v005 uv run --no-project --with pillow python BlenderSource/install_qchar17.py
```

## v004：黑髮、嘴巴、女性側髮

使用者在 v003 眼睛定案後指定三項，其餘與 v003 相同：

- **黑髮調黑：** 黑髮顏色降到 (.014,.011,.014)，粗糙度 .42、鏡面 .05，高光集中成細亮帶，其餘保持深黑（v003 在攝影棚燈下偏灰）。棕、白、灰髮不變。
- **嘴巴放大：** 張口笑約放大 25%（寬 86 mm、深 38 mm），小張口也同比例放大；改成和眼睛一樣投影到臉部曲面的薄圖層（`mouth_decal`），避免較大的平板在嘴角陷進臉裡。
- **女性側髮弧度：** 玩家（女）、丹修弟子、客棧老闆娘、藥師的側髮（`lock_curve=True`）：前片先往外鼓過臉頰、再往下巴內收成括號形，後片尾端往外翹。其餘人物維持 v003 直側髮。文件沒有記載角色性別，劍修弟子先當男性處理，未加弧度。

模組 `BlenderSource/qchar17_v004.py`；以 `QCHAR_VERSION=v004` 建置與驗證；設定圖 `DesignSheets_v004/`，驗證 `validation_v004.json`（12 位通過）。v001–v003 保留。

## v003：眼睛重做

使用者回饋 v002「眼睛怪怪的」。原因：眼白、虹膜、高光都是鼓起的立體小丘，看起來像塑膠鈕扣；眼白整圈包住虹膜像在瞪人；上睫毛是浮在上方的立體拱；瞳孔像黑豆。

v003 把眼睛改成貼合臉部曲面的平面圖層（每個頂點都投影到皮膚上，層距 1.2 mm）：眼白 → 虹膜（上緣藏進睫毛下）→ 上方深色帶 → 下方亮部 → 瞳孔 → 同側大小高光 → 上睫毛（內細外粗、眼尾上翹的實心線）與下睫毛。眼睛材質霧面並略帶自發光，看起來像畫上去的。瀏海蓋到額頭的人物不再畫眉毛（v002 的眉毛夾在髮尖間像橫槓），只保留給長老、店主、婆婆。其他造型與 v002 相同。

模組 `BlenderSource/qchar17_v003.py`；以 `QCHAR_VERSION=v003` 建置與驗證；設定圖 `DesignSheets_v003/`，驗證 `validation_v003.json`。v001、v002 保留。

## v002：依使用者參考圖修改

使用者提供一張動漫 Q 版人偶參考圖，指定套用三項，服裝仍維持修仙風格、站姿維持 A 字：

- **動漫大眼與張口笑：** 眼白、雙色虹膜（下半較亮）、瞳孔、上下兩點高光、粗上睫毛線與眼尾上揚；每位人物不同眼色（琥珀、藍、玉、褐、灰、紫、綠）；張口笑看得到舌頭。長老、店主、婆婆維持 ^^ 笑眼。
- **蓬鬆高層次頭髮：** 頭髮整體放大，瀏海更多更厚，頭頂往後腦加一圈放射狀髮束，兩側各兩片垂到肩、尾端向前彎，玩家與弟子加呆毛。丹修弟子的背後長髮改成扇形五束。戴帽／頭巾的人物不加頭頂髮束。
- **2.5 頭身與細四肢：** 頭縮小、身體與腿拉長、四肢變細；青年角色袍子到膝上並加白色綁腿，長老、婆婆、老闆娘、店主仍是長袍。身高約 1.30 m。

另修正使用者指出的「拿東西怪怪的」：拿道具的手改成握拳（手背、四指彎曲包住握把、拇指扣住），道具握把穿過掌心。鐵鎚、拐杖、斧頭、茶壺提把、算盤邊框（改成側握，像拿帳本）、丹瓶都依此重排；背劍、藥簍、葫蘆不需握。握持軸線記在 model_info.json 的 `grips`，日後可做骨架掛點。

v002 由 `BlenderSource/qchar17_v002.py` 建出（v001 模組 `qchar17.py` 保留），建置與驗證以 `QCHAR_VERSION=v002` 執行；設定圖在 `DesignSheets_v002/`，驗證在 `validation_v002.json`。v001 全部檔案保留。

## v001（保留）

2026-10-24。使用者重新開啟人物製作，指定「更可愛的 2 頭身」、整套村民與長老。QPlayerStart16 停工時的人物試作（大頭、塊狀身體）保留不動，本批是新做的另一套，不覆寫舊檔。

入口：[本批圖庫](index.html)，含三張全員設定圖（正面、斜角、背面）與每位人物的十視圖。

## 人物（12 位）

| ID | 名稱 | 髮型／特徵 | 道具 |
| --- | --- | --- | --- |
| QPlayerMale | 玩家（男） | 頭頂髮髻、木簪 | — |
| QPlayerFemale | 玩家（女） | 雙丸子頭、玉色緞帶 | — |
| QDiscipleSword | 劍修弟子 | 高馬尾 | 背劍 |
| QDiscipleAlchemy | 丹修弟子 | 長髮半束、玉簪、玉色眼 | 丹瓶、葫蘆 |
| QDiscipleFarmer | 體修弟子 | 短髮紅頭帶、捲袖 | — |
| QSectElder | 宗門長老 | 白髮玉冠、長鬍、笑眼、披肩 | 葫蘆拐杖 |
| QBlacksmith | 鐵匠 | 刺蝟頭、皮圍裙、捲袖、體型較壯 | 鐵鎚 |
| QShopkeeper | 雜貨店主 | 瓜皮帽、八字鬍、笑眼、圓肚 | 算盤 |
| QInnkeeper | 客棧老闆娘 | 低髮髻、白圍裙 | 茶壺 |
| QHerbalist | 藥師 | 側編辮 | 背藥簍 |
| QGranny | 村中婆婆 | 頭巾、笑眼、披肩、較矮 | 拐杖 |
| QWoodcutter | 樵夫 | 斗笠、捲袖 | 斧頭 |

## 規格

- 約 2 頭身：身高 1.25 m（婆婆 ×0.92、長老 ×1.04），頭高約佔一半。1 單位 = 1 m，正面 -Y，原點在腳底中心。
- A 字站姿（手臂斜下約 35°），各部位分件：頭、臉部零件、頭髮、袍、袖、手、腿、鞋、道具，方便日後綁骨架或換裝。
- 全部由 `BlenderSource/qchar17.py` 的共用零件程序化組成：身體、臉（大眼＋兩點高光＋睫毛、笑眼、腮紅、小嘴）、12 種髮型、交領袍＋腰帶結＋袖口與下襬滾邊、圍裙、披肩、帽子與道具。改參數即可做新人物。
- 配色沿用 SectCore04：青綠、暖木、淺石、淡玉。
- **沒有使用 AI 生圖**：本工作階段沒有生圖工具。設定圖與十視圖都是同一份 Blender 幾何的渲染。

## 交付

每位：`Models/<ID>/v001/` 的 .blend、FBX、model_info.json；`ArtLibrary/Turnarounds/<ID>_v001/` 的 10 張 1024×1024 PNG 與 views.json。主目錄 `Models/`、`ArtLibrary/Turnarounds/` 另有雜湊核對過的副本。設定圖在 `DesignSheets/`（原圖 3200×800 與加註姓名版）。

## 驗證（`validation.json`）

重新開檔、頂點有限值、腳底中心原點、雙眼／雙手／雙鞋齊全、臉部零件位於頭部前方、FBX 回匯物件數與尺寸、十張互不相同的 1024 圖。

**未做：** 骨架、蒙皮、動作、UV／貼圖烘焙、LOD、Unreal 匯入，以及和門、家具、場景的實際尺寸比例檢查（QPlayerStart16 記載人物尺寸尚未定案）。

## 修正紀錄

- 第一版頭髮用刪面做出臉部開口，太陽穴出現階梯鋸齒，側面像頭盔；改成把開口處頂點平滑縮進頭內，並讓兩側頭髮蓋過耳朵。
- 後腦原本是平切碗型，加了髮尾；第一版髮尾像冰柱，改成較寬、圓潤、長短交錯。
- 圍裙原本被交領與腰帶穿出，調整前後層次：圍裙蓋住領子、腰帶繫在圍裙外。
- 瞇眼原本是扁橢圓，改成 ^^ 笑眼；店主八字鬍原本下垂像皺眉，改成上翹。
- 黑髮在攝影棚燈下偏灰，降低頭髮鏡面反射。

## 重建

```sh
blender --background --python-exit-code 1 --python BlenderSource/build_qchar17.py -- lineup
blender --background --python-exit-code 1 --python BlenderSource/build_qchar17.py
blender --background --python-exit-code 1 --python BlenderSource/verify_qchar17.py
uv run --no-project --with pillow python BlenderSource/install_qchar17.py
```

建置遇到已有 views.json 的人物會跳過；修改時請另存 v002。
