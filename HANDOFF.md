## 2026-10-24 最新：TownLayout_13（Q 版玩家角色）＋Q 版人物 17 v006

`/Game/Maps/TownLayout_13` 由 12 另存（12 未改動），只在這張地圖把遊戲模式換成 `BP_QPlayerGameMode`，預設玩家是 Q 版男玩家。**預設啟動與遊戲地圖、`開始遊玩.ps1` 已改為 13**（`DefaultEngine.ini`）；以遊戲模式不指定地圖啟動時，會載入 13 並產生 BP_QPlayerMale 與動作驅動元件（`Unreal/default13_game.log`）。

- **角色：** `BP_QPlayerMale`／`BP_QPlayerFemale`（`/Game/Art/QCharacters17/Blueprints`）複製自範本角色，範本本身未改。膠囊體半徑 32、半高 73，最高步行速度 204 cm/s。這個速度讓走路動作以 3.4 倍速播放，腳步剛好跟上移動，不滑步；比範本的 500 慢。網格的 tick 設定改為 Always Tick Pose and Refresh Bones。
- **動作：** C++ 新增 `UQCharacterAnimDriver`（`Source/XiuXianTown/QCharacterAnimDriver.*`），不用動畫藍圖，依地面速度切換 Idle／Walk，並依速度調整播放速率。
- **建置／測試：** `Unreal/Tools/build_qplayer13.py` 建置，`test_qplayer13.py` 測試。實際 PIE、以 AddMovementInput 逐格移動，男女各一場，全部通過（`qplayer13_runtime.json`）：17 根骨頭名稱正確、骨架為公分、站在地面、待機會動、走 6 m、進入 Walk 狀態、播放速率與速度相符、腳步前後約 29 cm、停下回到 Idle。宗門經營回歸測試 `test_management13.py` 70 項全部通過（`management13_runtime.json`）。截圖在 `Unreal/Validation/qplayer13_*.png`。
- **過程中修正的問題：**
  - v005 FBX 匯入後骨架小 100 倍，改用 v006 的公分 FBX，12 位都已重出。
  - 骨頭 head／neck 被改名，原因是和分件撞名。
  - 匯入任務沒有存骨架、物理資產和材質，改為整個資料夾存檔。
  - 範本網格 tick 設定在未渲染時不刷新骨頭。
  - 失敗的中間報告保留為 `qplayer13_*_initial_*.json`、`*_v005_fbx_scale.json`、`*_v006_metres.json`。
- **未做：**
  - 跳躍和落下時只顯示 Idle 姿勢。
  - 沒有跑步動作：若要恢復範本的 500 cm/s，需要另做跑步循環。
  - 材質用的是 FBX 匯入的預設材質，顏色比 Blender 渲染暗。
  - 沒有實際鍵盤遊玩、遊戲中選男女角色、打包與效能測試。
  - 編輯器每次腳本結束後 QUIT 時回傳存取違規，日誌已正常寫完 Exiting，資產與地圖都有存檔。

## 2026-10-24：Q 版人物 17 v005（骨架＋待機／走路）

v004 外觀不變，12 位加上 17 骨骼骨架（Unreal 風格命名，物件名 `Armature`）、蒙皮與兩段原地循環動作 `Idle`（49 格）與 `Walk`（25 格，24 fps）。`rig_qchar17.py` 產生、`verify_rig17.py` 驗證 12 位通過：權重和為 1、可循環、動作中手／腳／頭不脫離、走路著地腳貼地、FBX 回匯保留骨架與兩段動作。主圖庫改指向 v005（標記已綁骨架）；v001–v004 保留。**尚未匯入 Unreal**，頭髮與袍子沒有物理擺動，手臂與袍子的穿插未逐格量測。

## 2026-10-24：Q 版人物 17 v004（黑髮、嘴巴、女性側髮）

使用者確認 v003 眼睛後指定三項：黑髮調黑（低鏡面、集中高光）、嘴巴放大約 25% 並改為貼臉圖層、四位女性角色（玩家女、丹修、老闆娘、藥師）側髮做出括號弧度與外翹髮尾。其餘同 v003。12 位重開、FBX 回匯、十視圖檢查通過，主圖庫改指向 v004；v001–v003 保留。設定圖 `QCharacters17/DesignSheets_v004/`。仍未綁骨架、未進 UE。

## 2026-10-24：Q 版人物 17 v003（眼睛重做）

使用者回饋 v002「眼睛怪怪的」：眼睛改為貼合臉部曲面的平面圖層（眼白、虹膜藏進睫毛、深色帶、亮部、瞳孔、高光、實心睫毛線），霧面略帶自發光；被瀏海遮住的眉毛移除。12 位通過驗證，主圖庫改指向 v003；v001、v002 保留。設定圖 `QCharacters17/DesignSheets_v003/`。

## 2026-10-24：Q 版人物 17 v002（依使用者參考圖修改）

12 位另存 v002：動漫大眼（眼白、雙色虹膜、粗睫毛線）、張口笑，頭髮加頭頂放射髮束與及肩側髮，2.5 頭身、細四肢、短袍加綁腿；拿道具改為握拳、握把穿過掌心。12 位重開、FBX 回匯、十視圖檢查通過，主圖庫索引改指向 v002（v001 檔案保留）。設定圖 `ArtLibrary/ExpansionBatches/QCharacters17/DesignSheets_v002/`。仍未綁骨架、未進 UE。

## 2026-10-24：Q 版人物 17（Blender，Claude）

使用者重新開啟人物製作，指定「更可愛的 2 頭身」、整套人物。新增 `ArtLibrary/ExpansionBatches/QCharacters17`：玩家男女、三位弟子、宗門長老、鐵匠、雜貨店主、客棧老闆娘、藥師、村中婆婆、樵夫，共 12 位／120 張十視圖＋三張全員設定圖。身高 1.25 m、A 字站姿、分件，全部由 `qchar17.py` 共用零件程序化組成；未使用 AI 生圖。12 位通過重開、FBX 回匯、十視圖檢查並裝入主圖庫，目錄 112 組／1,120 張。未綁骨架、未進 UE，人物與場景的實際比例仍待定。QPlayerStart16 的舊人物試作保留未動。

秘境規則已由使用者確認並寫入 `Story/玩家成長與宗門秘境_需求紀錄.md`：年齡＝創角後實際日數；死亡踢出並失去當次收穫；時限到帶收穫安全傳出；不同宗門會在秘境相遇。

**注意：** 這份 D:\dondon2.0-main 是 D:\DONDON2.0 複製過來的內容。Claude 先前在舊子資料夾做的 TownLayout_10／11（凌雲山谷地形版）已被同名的宗門經營版 10／11 覆蓋，地圖不存在；其 UE 素材 `/Game/Art/LingyunValley10`、報告 `Unreal/expansion10_*.json`、`expansion11_*.json` 與批次 `LingyunValley15` 仍在，可依 `Unreal/Tools/build_expansion10.py`、`build_expansion11.py` 重建到新編號。

## 2026-10-24 最新：人物停工，非人物首批交付與選拔規則修訂

使用者明確指示「人物你別做了」，隨後指定「其他繼續做」。不得繼續生成或修改人物、髮型與服裝；`QPlayerStart16` 中六項舊人物初模只保留參考，未加入主素材索引。

已交付 10 組非人物外觀原型：山兔、山豬、靈石、丹瓶、煉氣訣、測靈晶石、洞府入口、地板、直牆、雙扇門。入口使用 v003，其餘 v002；另有洞府剖面配置 v002。主交付在 Models 與 ArtLibrary/Turnarounds，批次副本、圖庫與驗證在 `ArtLibrary/ExpansionBatches/QPlayerStart16/`。100 張單項十視圖、1 張開門預覽、10 張場景圖；主索引目前 100 組／1000 張（未含主索引外的 LingyunValley15 三組營地模型）。

非人物 `.blend` 重開、FBX 尺寸回匯、圖片規格與門軸動畫 FBX 回匯已通過；來源檔與安裝副本雜湊已核對。洞府預覽為低側牆、無洞頂的剖面，不是可玩關卡。生物骨架、UV、LOD、碰撞、導航與 UE 驗證尚未完成。未改遊戲地圖。

宗門選拔新規則：**角色創建完成後，現實經過整整 10 天即開放；離線照常計時，不要求累積在線時數**。離線期間達標，下次登入直接提供資格與廣場引導；不自動入宗。此規則已同步 Story 兩份需求／主線文件與美術規劃，目前仍為待實作設計。

以下為歷史紀錄。

2026-10-23 地形研究：新增 LingyunValleyTerrain v002 可編輯 Blender 初模與 FBX、10 張實際渲染、10 張內建 ImageGen 概念參考。入口 ArtLibrary/ExpansionBatches/LingyunValleyTerrain14/index.html。UE TownLayout_10 未改動；原版地形問題尚未在遊戲內修復。回匯與十視圖檢查見 Models/LingyunValleyTerrain/v002/validation.json。v001 為保留的試作。

## 2026-10-23：宗門經營與招募原型 TownLayout_10

使用者本輪指定方向為「經營宗門＋招募弟子」。從 09 另存 10，加入南側重建營地，採藥後可招募石砥、修復藥圃、建弟子舍與靜修臺、招募林溪與岳青、分工生產、以木石換靈石、晉升宗門。林溪與岳青為暫定測試角色，未改寫第一章劇情。

新增 `SectAdventure` C++ 導演與 SaveGame，舊關卡仍使用原本導演。Windows UE 5.8 編譯已通過；建立、保存與重載 10 的檢查通過，09 雜湊不變。PIE 71 項檢查通過，含正常進度、缺糧恢復、局部連續行走與第二次 PIE 還原；預設啟動／遊戲地圖已切為 10。證據見 `Unreal/management10_runtime.json`，保留初次射線判定失敗及測試器唯讀屬性誤用報告。不得把反射互動與局部連續行走稱為全程實體鍵鼠驗收。

說明：`Unreal/宗門經營試玩.md`。工具：`build_management10.py`（拒絕覆寫）、`test_management10.py`、`capture_management10.py`、`run_management10.ps1`。Windows 本機 `開始遊玩.ps1` 可啟動 10。玩家存檔槽為 `Dondon_SectManagement_v1`；測試另用 `Management10_Test_*`。

NPC 與弟子舍為簡化雛形，沒有新增獨立 Blender 模型。建築外觀無碰撞，互動使用入口標記；弟子尚無尋路／工作動畫。重開從安全出生點出發，離線不生產。正式效能與打包待驗收。

Windows 編譯需英文 junction 路徑與重建 Intermediate，以解決 MSVC 中文路徑的 PCH 錯誤；原快取移至忽略的 `work/management10-original-intermediate`。`Unreal/import_audit_20261023.json` 顯示部分 Blender／FBX／PNG 原本就是 LFS 指標，本輪只使用 UE 已匯入實體素材，圖庫盤點未通過。

以下為歷史紀錄。

## 2026-10-23：TownLayout_09 客棧室內補光

09 = 08 ＋ 客棧一、二樓 8 盞暖色點光（開陰影、避免漏光），保存重載通過；08 前／09 後同機位室內截圖已檢視，室內由近乎全黑改為可辨識。之後在 09 重跑 PIE，38 項全過（11 段任務路線得 10 靈石、草地 9 段、松樹／苔石阻擋），**預設啟動與遊戲關卡已改為 TownLayout_09**（`Config/DefaultEngine.ini`，UE 讀回確認）。證據：`Unreal/expansion09_runtime.json`。細節與燈表見 `Unreal/README.md` 頂部。尚未提交。

## 2026-10-22：TownLayout_08（07＋野外植被），PIE 38 項通過

Windows 已裝 VS 2022 Build Tools 17.14，C++ 模組可編譯（`SectQuest.cpp` 一個變數改名以通過 MSVC）。`/Game/Maps/TownLayout_08` = 07 原樣＋串流子關卡 `Sublevels/TownWild08_Sublevel`（WildVegetation13 五件共 24 個 Actor）；07 未修改。PIE：07 任務路線全數通過，草地行走、灌木可穿越、松樹樹幹與苔石會阻擋；6 張 UE 畫面已檢視。**預設關卡仍為 06。** 細節見 `Unreal/README.md` 頂部。本機 `Unreal/` 已由 LFS 指標換成實體檔（雜湊全符）；其餘目錄仍是指標檔。尚未提交。

待辦：07 本身的通行驗證仍是中斷狀態（08 已覆蓋同一路線）。客棧室內過暗已於 09 處理。

## 2026-10-22 新批次：野外植被與岩石 13（Windows 本機）

新增 `ArtLibrary/ExpansionBatches/WildVegetation13`：普通松 CommonPine、竹叢 BambooClump、野灌木 WildShrub、苔石組 MossBoulderSet、碎石堆 ScreePile，共 5 組／50 張十視圖，素材索引更新為 89 組／890 張。全部以 `build_wild13.py` 程序化建模（固定種子），在 Windows 的 Blender 5.2.2 LTS 建置；未使用 AI 生成模型或概念圖。驗證與安裝結果見該批次 `validation.json`、`inventory.json`。

本機這份專案是 ZIP 解壓，不是 git 儲存庫，既有 .blend／FBX／PNG 全是 Git LFS 指標檔，因此本輪無法開啟既有模型比對畫風，只沿用腳本中的色票。植被為靜態網格，竹葉需雙面材質；UV 烘焙、碰撞、LOD、Unreal 匯入與場景配置未做。本批次尚未提交或推送。

## 2026-10-22 新儲存庫交接

目的地：`https://github.com/joshsu54/dondon2.0`，分支 `main`。本儲存庫使用乾淨初始提交，保留 Blender／UE5 檔案與 Git LFS 資產；原始專案與舊儲存庫不變。下方舊分支下載說明屬歷史紀錄；新交接請取得 dondon2.0/main 並執行 `git lfs pull`。預設 06，07 待驗證。

## 2026-10-22 待續：TownLayout_07 基座與照明修整

07 已另存，新增公告板低石基座及公告板／休憩亭暖色補光，8 項保存重載檢查通過；原 06 與模型原檔保留，兩張關卡雜湊已核對。這是既有模型的 UE 放置與照明修改，沒有新 Blender 物件或十視圖交付。

PIE 已通過前 7 段路線與 20 項檢查，但在回程前編輯器收到 QUIT_EDITOR 並正常關閉，不能視為完整通過。原始中斷報告保存在 `Unreal/expansion07_runtime_interrupted_initial.json`；目前未產生 07 外觀截圖。Mac 鎖定，解鎖後從 07 執行 `Unreal/Tools/review_expansion07.py` 重跑完整路線及三張外觀截圖；不要重跑建置或覆寫既有 07。

預設仍為已通過驗證的 06；07 尚未完成驗收；本次將其作為待驗證進度納入 dondon2.0/main。完成外觀與互動檢查後再決定切換預設。

## 2026-10-22 最新：TownLayout_06 按鍵驗證完成

最新與預設啟動／遊戲關卡為 `/Game/Maps/TownLayout_06`，舊關卡保留。七種既有模型（休憩亭、石欄杆、松樹、草叢、石燈、路標、公告板）已整合；本輪沒有新增 Blender 幾何，沿用已核對的七件來源及 70 張角度圖。

06 已完成五次實際 E 鍵互動：接委託、三次採草、交付並取得 10 靈石，五張 UE 截圖的中文 HUD 與進度已檢視。按鍵測試由腳本傳送到各目標；既有 11 段連續路線使用 CharacterMovement API，並非全程手動行走。關卡 SHA-256 與前次 39 項保存檢查及 27 項執行檢查時相同。

證據：`Unreal/expansion06_keyboard.json`、`Unreal/expansion06_validation.json`、`Unreal/expansion06_runtime.json`、`Unreal/Validation/expansion06_key_0.png` 至 `_4.png`。Play 後 WASD 移動、滑鼠轉向、空白鍵跳躍、E 互動；重開遊戲仍會重置任務與靈石。

接續改善公告板基座與路面接合、亭內及公告板照明、植被風動；UV／貼圖烘焙、LOD、全世界導航、存檔、效能及正式打包尚未驗收。UE 的 iOS 裝置偵測工具有架構警告，未驗證 iOS 支援。本輪只完成上述原型驗證與預設關卡切換。

以下為歷史紀錄，關卡預設值與驗證狀態以上述為準。

## 2026-10-21 GitHub 同步：UE5 專案與 TownLayout_06 進度

本次同步包含完整 UE5 專案來源（Config、Content、Source、uproject）、關卡 01–06、驗證工具與截圖。UE 資產、關卡與關卡備份由 Git LFS 管理；編譯產物、Saved、Intermediate、DerivedDataCache、本機登入資料與快取排除。Android File Server 未用於本專案的 Mac 流程，已停用並移除自動產生的 SecurityToken。

最新製作中關卡為 `/Game/Maps/TownLayout_06`；**預設啟動仍為已完整驗證的 TownLayout_05**。06 加入七種既有模型：六角休憩亭、獨立石欄杆、松樹、草叢、石燈、路標與公告板。新增 35 個配置 Actor、替換 3 個舊任務牌部件，總數 3,945；不新增 Blender 幾何，七件來源的原檔、FBX 與 70 張既有角度圖已核對。

06 已保存重載，39 項模型／放置檢查及 11 段連續 PIE 路線通過，包含進出亭子、採三株靈草及返回領取 10 靈石。測試以 CharacterMovement 與反射互動執行，**06 的實際 E 鍵複驗仍待完成**，不能沿用 05 結果當作 06 的鍵鼠驗收。公告板初版定位錯誤已修正，保留原失敗報告與關卡備份。三個不同場景視角已檢視；trail 截圖與 reststop 構圖重複，不列為額外角度。

後續：執行 `Unreal/Tools/check_expansion06_keyboard.py` 完成實際 E 鍵驗證，再決定是否將預設關卡切換為 06；改善公告板基座與路面接合、亭內照明。植被目前為靜態 FBX，尚無風動材質；程序貼圖烘焙、LOD、正式效能／打包、任務存檔仍待實作。

下載請使用 `solid-clouds-karst-peaks` 分支並執行 `git lfs pull`。以 UE 5.8 開啟 `Unreal/XiuXianTown/XiuXianTown.uproject`，首次需編譯 C++ 模組（Mac 需 Xcode／Metal 工具）；Binaries 刻意不納入版本庫。證據見 `Unreal/expansion06_source_audit.json`、`Unreal/expansion06_validation.json`、`Unreal/expansion06_runtime.json`。

以下是歷史紀錄；其中「尚未推送」描述當時狀態，本次上傳結果以 GitHub 分支提交為準。

## 2026-10-21 最新：TownLayout_05 宗門採藥原型

最新與預設啟動／遊戲關卡改為 `/Game/Maps/TownLayout_05`；03、04 與既有模型均保留。新增內容為既有山峰、山脊、雲群、山門、道路、兩段石階、委託牌及三株任務靈草的 UE 整合，沒有新建 Blender 幾何或新的獨立十視圖交付。05 修正了雲群過低過大、山峰旋轉誤用 pitch 的問題。

05 已保存重載，15 項放置檢查、八段連續 PIE 往返及 24 項任務／通行檢查通過。另以實際 E 鍵完成接任務、三次採集及交付 10 靈石，共五次互動；按鍵測試由腳本傳送到各目標，連續走路測試由 CharacterMovement API 驅動，兩者各自驗證，不代表全程手動行走。

中文 HUD、採集進度、獎勵文字、山門配色、山峰方向及雲群不遮路均已檢視實際 UE 截圖。來源 FBX 雜湊無變動。證據：`Unreal/expansion05_validation.json`、`Unreal/expansion05_runtime.json`、`Unreal/expansion05_keyboard.json`，截圖位於 `Unreal/Validation/expansion05_*.png`。從 UE 專案資料夾看，上述路徑去掉開頭的 Unreal/。

操作：Play 後 WASD 移動、滑鼠轉向、空白鍵跳躍；到小鎮北端木色委託牌旁按 E 接任務，沿青石路採三株靈草，再回牌旁按 E 領獎。重開遊戲會重置任務與靈石。

這是可測試的任務原型：大片平地、方塊支撐、空白委託牌仍待美術整理，遠山無碰撞；尚未完成效能、全世界導航、存檔或打包驗收。這批 UE 變更未推送 GitHub。前一輪截圖記錄器錯誤已修正並重跑通過，保留原錯誤報告供追查。

## 2026-10-20：宗門採藥原型進度（TownLayout_05，尚待最後驗證）

TownLayout_04 已加入山景、漂移雲群、連接宗門的道路／兩段石階、山門、委託牌與三株靈草。C++ 任務模組編譯成功；HUD 改在 NativeOnInitialized 建立後，實際 UE 畫面可讀取中文任務及操作提示。

04 的真實 PIE 連續往返路線八段與 24 項檢查通過：接任務、三株採集、返程交付 10 靈石，並阻擋遠距互動、未接任務採集、提前交付、重複採集與重複領獎。移動由 CharacterMovement API 驅動，互動由反射函式呼叫；不等於鍵鼠全流程驗收。證據：`expansion04_runtime.json`。

視覺檢查發現雲群遮路及山峰旋轉軸誤用，另存 05：縮小並抬高三群雲、取消雲投影，七個山景 Actor 改為明確 yaw 旋轉，已保存重載；04 保留。05 的 E 鍵接任務已實際成功，接著測試記錄器誤呼叫未公開的 PlayerController.console_command，導致截圖記錄失敗。腳本已改用 SystemLibrary.execute_console_command，仍須重跑全部五次 E 互動及最終截圖。錯誤原始紀錄保留在 `expansion05_keyboard_initial_capture_error.json`，修正工具為 `Tools/check_expansion04_keyboard.py`（支援 04/05）。

目前 Mac 鎖定，等待解鎖才能繼續操作 UE。預設關卡仍保留已驗證的 03；05 尚未標為完整完成。任務尚無存檔，遠山無碰撞，道路支撐與材質仍是原型；本輪沒有新增 Blender 幾何，也未推送 GitHub。詳見 `expansion05_progress.json`、`expansion05_revision.json`。

# 最新交接狀態｜2026-10-18

2026-10-19 UE 更新：最新關卡為 `TownPrototype_02`，專案 `Unreal/XiuXianTown/XiuXianTown.uproject`。首批模型已匯入，483 個民宅／長凳分件補回原檔配色，原始模型與 01 關卡保留。從磁碟重開後材質與七項真實 PIE 檢查通過：出生、移動、跳躍、落地、方塊阻擋、台階攀爬、關門阻擋。鍵鼠／鏡頭操作、完整小鎮、貼圖烘焙、效能及編輯器崩潰原因仍待處理。尚未打包或推送這批 UE 變更。詳見 `Unreal/README.md` 與最新 JSON 報告。

本機已完成 **TownRefinement12**：把 Claude 分支 `70d3fa4` 小鎮使用的 18 項素材修整為既有宗門畫風，逐件另存 v002、產出 180 張角度圖；TownLayout v004 另有 10 張場景圖與 4 張預覽。11 件保留原幾何，7 件另外修正入口尺寸、路緣、荷葉／紙張／草束／木框共面問題。原檔與 FBX 回匯驗證見 `ArtLibrary/ExpansionBatches/TownRefinement12/validation.json`。

- 目前本機索引：84 組獨立素材、840 張基本角度圖、3 個配置場景；額外場景圖不灌入獨立素材計數。
- 最新小鎮：`Models/TownLayout/v004/TownLayout_v004.blend`；完整新版圖庫：`ArtLibrary/ExpansionBatches/TownRefinement12/index.html`。
- 原 Claude 素材與十張概念圖逐檔保存在該批次 `SourceSnapshot`，`provenance.json` 記錄來源與雜湊。Claude 的其餘廚房／道路素材並未全部合併到本機索引。
- 本輪修整與本文件一併納入 `solid-clouds-karst-peaks` 分支提交；交接時請拉取此分支並執行 `git lfs pull`，不要使用仍為舊版的 `main`。
- 先前完整分卷交接包仍在本機 `work/handoff/claude-handoff-2026-10-17`，對應 `d4579bf`，**不含本輪修整**；GitHub Release 尚未發布。需要最新完整交接包時應驗證、提交後重新建包。
- 畫風依據：`SectCore04` 的青綠瓦、暖木、淺石、淡玉與柔光；不要再切回飽和紅柱、亮金或不同風格。
- 本輪未做角色碰撞、UV 烘焙、LOD、全鎮導航及 Unreal 匯入。舊交接中的山景與實體雲待辦仍有效。

以下為 2026-10-17 的歷史盤點，涉及數量、最新小鎮與下載狀態時以上方為準。

# Claude Code 交接｜2026-10-17

## 專案與下載

- GitHub：<https://github.com/joshsu54/dondon>
- 最新分支：`solid-clouds-karst-peaks`。交接前素材提交為 `44cb796`，2026-10-17 交接文件提交為 `d4579bf`；其後修整請以分支最新提交為準。尚未發布交接 Release tag。
- 複製版本庫：安裝 Git LFS，執行 `git clone --branch solid-clouds-karst-peaks https://github.com/joshsu54/dondon.git`，進入目錄後 `git lfs pull`、`git lfs fsck`。
- 分卷封裝與還原工具已備妥，但 GitHub Release 尚未發布，目前請使用 Git clone 與 Git LFS；歷史本機分卷包不含 2026-10-18 修整。

## 已完成內容

素材索引共 **66 組獨立素材、660 張基本角度圖、3 個配置場景**，另有多個歷史版本、額外預覽與風動影片。這是外觀原型素材庫，不是已可遊玩的完整開放世界專案。

| 內容 | 路徑／版本 | 狀態 |
| --- | --- | --- |
| 最新山景總場景 | Models/MountainSanctuary/v004 | 已替換實體雲、喀斯特山峰；四張場景預覽與靜態 FBX |
| 原登山步道 | Models/MountainSanctuary/v002 | 33 個路線模組、升高 48 m；歷史版本保留 |
| 凌雲孤峰、連綿山脊 | Models/CloudpiercerPeak/v002、Models/MountainRidge/v002 | 新版石柱型山峰；v001 保留 |
| 風動與實體雲 | Effects/WindFog/v002 | Blender 96 幀循環，4 秒／12fps 影片；非流體模擬 |
| 水景批次 09 | ArtLibrary/ExpansionBatches/MountainWaters09 | 瀑布、彎曲山溪、靈泉：3 組／30 圖；水為靜態幾何 |
| 山路設施 10 | ArtLibrary/ExpansionBatches/MountainWayside10 | 六角休憩亭、拱形石橋、獨立欄杆：3 組／30 圖，另有亭內預覽 |
| 宗門、商鋪、道具等 | ArtLibrary/asset_catalog.json | 其餘登錄素材與圖庫入口 |
| 故事 | Story/ | 序章、第一章大綱與 Word 劇本，尚未據此完成整套角色／動畫 |

## 重要版本差異與限制

1. 圖庫索引及部分歷史 README 仍指向 MountainSanctuary v002、山峰 v001、WindFog v001；不能把「索引目前選用」與「目錄內最新版本」視為相同。先核對 v004／v002 的內容及已有 validation，再決定是否切換索引，保留舊版連結。
2. `build_peaks_v002.py` 已修正山頂環高度遞增、`build_solid_clouds_v002.py` 已修正匯入時還原 sys.argv。這些修正已提交，但現有二進位是否由修正後腳本重建未另行證明，不能宣稱完全可重現；應在新版本或隔離輸出目錄重建比較。
3. 新增水景與山路設施尚未放入山景總場景。石橋長 9 m、淨寬 2.98 m、最高橋面 2.1 m；最大坡度約 35°，加入角色前需調整坡度或加階梯並驗證通行。
4. FBX 只保留靜態幾何與基本材質色；程序材質、雲漂移、植被形態鍵動畫並非已完成 Unreal 移植。
5. UV／貼圖烘焙、碰撞、LOD、導航及 Unreal 實際匯入尚未完成。石欄杆重複排列需整理端柱與接縫。
6. 批次 09／10 的本機安裝腳本在忽略的 work 內，不在交接來源中；已有成品、建模與驗證腳本均已交付。接下來新增批次應把安裝／圖庫更新流程寫成版本化工具。

## 目錄

- `ArtLibrary/index.html`：本機圖庫；`完整建模清單.md`：需求與尚缺項目。
- `ArtLibrary/ExpansionBatches/<batch>/BlenderSource/`：各批次 Blender 生成／驗證腳本。
- `Models/<asset>/vNNN/`：可編輯原檔、FBX、模型資料。
- `ArtLibrary/Turnarounds/<asset>_vNNN/`：十視圖與相機紀錄。
- `BlenderSource/`：較早期模型與動畫腳本。
- `Effects/`：風動雲霧；`ArtReferences/`：概念圖，不能當作同模型十視圖。
- `Deliverables/`：歷史完整批次 ZIP；交接 Release 也保留這些檔案。
- `Tools/BlenderMCP/`：既有 MCP 安裝記錄及鎖定需求；本機 .venv 與帳號設定不包含在包內。

## 環境與驗證

原機使用 macOS arm64、Blender 5.3.0 Beta（建置 98f8f23151d3），Python 腳本主要依賴 Blender 內建 bpy。尚未驗證其他 Blender 版本。`Tools/bin/blender` 是原機絕對路徑捷徑，在別台機器請改用實際的 `blender` 執行檔。讀圖／製作總覽時可使用 Pillow，但唯讀交接檢查僅需 Python 3.9+ 標準函式庫。

```sh
# 唯讀：索引、實際檔案、十視圖、LFS 指標與本地網頁連結
python3 Tools/Handoff/verify_project.py

# 重新開檔及 FBX 回匯驗證（會寫回批次 validation.json）
blender --background --python-exit-code 1 --python ArtLibrary/ExpansionBatches/MountainWaters09/BlenderSource/verify_waters09.py
blender --background --python-exit-code 1 --python ArtLibrary/ExpansionBatches/MountainWayside10/BlenderSource/verify_wayside10.py
```

批次 09／10 建模腳本遇到 views.json 會跳過該資產；不要為了強制重建而直接刪除正式成果。新建 v002 或改到獨立輸出路徑，再驗證、渲染、回匯與安裝。CLI 使用 `--python-exit-code 1`，避免 Blender Python 失敗但程序回傳 0。

## 建議接續順序

1. 跑唯讀盤點、閱讀最近 validation，回報實際現況與版本差異。
2. 優先整理新版山峰／實體雲的圖庫索引，先核對原檔及十視圖，不要直接改計數。
3. 在新的山景版本配置水景、休憩亭、石橋與欄杆；處理橋坡、岸線、入口高度與接縫。
4. 再依完整建模清單補竹林／灌木、秘境入口、小鎮水井／公告板等缺件；每件至少十視圖。
5. 美術原型確認後，另做 UV、材質烘焙、碰撞、LOD 與 Unreal 驗收。

## 可直接交給 Claude Code 的開場指令

> 請接手這個修仙 Blender 美術專案。先讀 CLAUDE.md、HANDOFF.md 與 ArtLibrary/完整建模清單.md，執行 python3 Tools/Handoff/verify_project.py，核對 git status。用繁體中文說明盤點結果，再從新版山峰／實體雲索引差異與山景設施整合接續工作。保留既有版本；每個獨立新素材必須有可編輯 Blender、FBX 和至少十個不同角度的同模型渲染圖。不要把外觀原型標成已通過 Unreal 驗證。

## UE 小鎮更新（2026-10-20，最新 03）

最新與預設關卡為 `/Game/Maps/TownLayout_03`，01／02 保留。3,877 分件、87 種材質、3,882 Actor。客棧樓梯側隔間留出 159 cm 開口，第一張床移開 125 cm；已保存重載、八項真實 PIE 通行／阻擋測試通過，四張 UE 畫面已檢視。只調整四個 UE Actor，原始 Blender／FBX 不變。

詳見 `Unreal/README.md`、`Unreal/town03_landing_revision.json`、`Unreal/town_routes_TownLayout_03.json`。測試使用各段獨立起點與 CharacterMovement API；連續全鎮路線、鍵鼠、室內照明、第三人稱鏡頭貼牆、地板接縫、互動、背景山景、LOD 與效能仍待處理。尚未推送 GitHub。
