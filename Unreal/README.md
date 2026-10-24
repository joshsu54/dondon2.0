## 2026-10-24 最新：TownLayout_13 Q 版玩家角色

由 12 另存，只在這張地圖把遊戲模式換成 `/Game/Art/QCharacters17/Blueprints/BP_QPlayerGameMode`，預設玩家是 Q 版男玩家（Q 版人物 17 v006 的 FBX）；女玩家藍圖 `BP_QPlayerFemale` 也已建好。待機／走路由 C++ 元件 `UQCharacterAnimDriver` 依速度切換。建置 `Tools/build_qplayer13.py`，測試 `Tools/test_qplayer13.py`（報告 `qplayer13_runtime.json`，男女各一場 PIE 全部通過）與 `Tools/test_management13.py`（經營回歸 70 項通過）。預設啟動／遊戲地圖與 `開始遊玩.ps1` 已改為 13。限制與修正過程見專案根目錄 HANDOFF.md。

## 2026-10-23 最新：TownLayout_10 宗門經營與招募

預設啟動／遊戲地圖已切換到 10，原 01–09 保留。新南側營地提供三位弟子招募、工作分派、木石與糧食生產、藥圃／弟子舍／靜修臺建設、重複建材委託、宗門晉升及本機存檔。

詳見 [試玩說明](宗門經營試玩.md)。Windows UE 5.8 編譯與 PIE 71 項檢查通過，包含缺糧恢復、營地中央道路連續行走、第二次 PIE 還原資源與設施；互動透過反射呼叫，並非實體鍵鼠全流程驗收。報告：`management10_build.json`、`management10_runtime.json`。NPC 目前為簡化人形，沒有弟子尋路、正式建築室內碰撞或打包驗收。

以下為舊版紀錄。

## 2026-10-23：TownLayout_09 客棧室內暖色補光

`/Game/Maps/TownLayout_09` 由 `Tools/build_expansion09.py` 從 08 另存，只新增 8 盞客棧室內暖色點光（07 同色 (1, .86, .67)、燭光單位、Movable，資料夾 Expansion09）。與 07 戶外補光不同：室內燈**開啟陰影**，避免光穿透樓板與外牆。08、子關卡與所有模型未變（08 雜湊已核對）。

**預設啟動與遊戲關卡已改為 TownLayout_09**（2026-10-23）。切換前在 09 重跑 PIE（`TOWN_PIE_MAP=TownLayout_09 TOWN_PIE_NO_CAPTURE=1`，執行 `Tools/review_expansion08.py`）：38 項全過，含 11 段任務路線與 10 靈石、草地 9 段、松樹最近 64 cm／苔石 102 cm 阻擋；09 檔雜湊與檢視時相同。證據 `expansion09_runtime.json`、`expansion09_pie_review.json`。

| 燈 | 位置 (cm) | cd | 半徑 |
| --- | --- | ---: | ---: |
| InnHallFill09 一樓大廳 | -1390, -2220, 380 | 70 | 720 |
| InnCounterFill09 櫃台 | -1640, -2650, 400 | 35 | 460 |
| InnStairFootFill09 樓梯口 | -1700, -1830, 420 | 30 | 420 |
| InnCorridorFill09 二樓走廊 | -1320, -2300, 640 | 40 | 620 |
| InnUpperNorthFill09 二樓北端 | -1320, -1780, 650 | 30 | 420 |
| InnRoomSouthFill09 / InnRoomMidFill09 客房 | -1770, -2560 / -2240, 730 | 28 | 360 |
| InnStairTopFill09 樓梯頂 | -1760, -1820, 740 | 30 | 380 |

調整經過：初版 7 盞（140–360 cd）在固定曝光 EV100 0／+1 下室內過曝；第一輪降到約 1/5、大廳燈下移；第二輪降低走廊燈並補北端一盞。每輪皆保存重載核對，紀錄在 `expansion09_tune.json`（初版設定 `expansion09_revision.json`）。

外觀：同機位 08（前）／09（後）各 6 張已檢視（`Validation/inn08_*.png`、`inn09_*.png`）：大廳、櫃台與樓梯、上樓梯、二樓走廊、客房、正門外觀；一、二樓可辨識家具與動線，外觀只見門內暖光、門外地面無漏光。二樓走廊天花板仍有柔和亮區。PIE 見上方切換紀錄；未做夜間或實機效能檢查。重跑截圖：`Tools/capture_inn09.py`（`INN09_ONLY=1` 只拍 09）。

## 2026-10-22：TownLayout_08（07＋野外植被子關卡），PIE 通過

`/Game/Maps/TownLayout_08` 由 `Tools/assemble_town08.py` 從 07 另存：07 原樣（3,948 Actor，07 檔雜湊未變）＋常駐串流子關卡 `TownWild08_Sublevel`（24 個植被／岩石）。**預設關卡仍為 06**，是否切換由使用者決定。

- 編譯：Windows 安裝 VS 2022 Build Tools 17.14 後，C++ 模組編譯成功。`SectQuest.cpp` 的區域變數 `Slot` 遮蔽 `UWidget::Slot`，MSVC 視為錯誤，已改名為 `PanelSlot`（行為不變）。
- PIE（`Tools/test_expansion08.py`，38 項全過）：07 原有 11 段任務路線（接任務、三株採集、亭內、山門、交付得 10 靈石，含重複與越權阻擋）；草地 5 段行走、穿過灌木（無碰撞）；走向松樹時離樹幹中心最近 63.5 cm、走向苔石最近 102 cm（有碰撞阻擋）。移動仍由 CharacterMovement API 驅動，互動用反射呼叫，非實體鍵鼠；草地段由傳送起點開始。
- 外觀：6 張 UE 畫面已檢視（`Validation/expansion08_*.png`）：南側總覽、草地平視、東側竹叢（前景松樹遮住部分竹叢）、西側、公告板（07 基座與補光保留）、頂視。
- 碰撞修正經過：命令列匯入／生成的松樹與苔石在從磁碟載入後完全沒有碰撞。已在 GUI 編輯器重新匯入網格（`reimport_wild08_meshes.py`）、改用解析式簡單碰撞（松樹樹幹膠囊 r30 cm 高 260 cm、三顆大石各一個 Box；`simple_collision_wild08.py`），並在 GUI 重建 24 個 Actor（`rebuild_wild08_actors.py`），之後 08 從磁碟載入的掃掠與 PIE 皆會阻擋。舊的「是否停在樹前」測法本身有誤（角色會沿圓柱滑過），已改為量測最近距離；修正前究竟是無碰撞或繞過，無法事後區分。
- 未做：實體鍵鼠、全程手動行走、效能、LOD、打包、室內照明。子關卡單獨開啟時命令列掃掠仍不命中（只影響單獨檢視，08 正常）。

證據：`town08_assembly.json`、`expansion08_runtime.json`、`expansion08_capture.json`、`wild08_simple_collision.json`、`wild08_actor_rebuild.json`、`wild08_reimport.json`。重跑：開啟 08 後執行 `Tools/review_expansion08.py`（`-ExecutePythonScript … -unattended`）。

## 2026-10-22 新增：野外植被子關卡 TownWild08_Sublevel（Windows，已併入 08，見上方）

`/Game/Maps/Sublevels/TownWild08_Sublevel` 只含 WildVegetation13 的 24 個 Actor：普通松 5、竹叢 4、野灌木 8、苔石組 4、碎石堆 3，座標對齊 TownLayout_07 小鎮周邊（南側草地保留入口走廊 X ±500 cm、城鎮與東西山腳之間的空地）。資產在 `/Game/Art/WildVegetation08`：5 個 Static Mesh、17 個常數色材質（苔石用世界法線朝上混苔色，竹葉雙面）。松樹、苔石為 Complex As Simple 碰撞；竹叢、灌木、碎石堆關閉碰撞。

**沒有另存 TownLayout_08，也沒有修改 07。** 原因：Windows 本機只有 VS 2019 Build Tools，UE 5.8 要求 VS 17.8 以上（MSVC v14.50），C++ 任務模組無法編譯；在缺模組狀態下保存 07 衍生關卡會遺失任務 Actor。作法是在移除模組宣告的暫存專案副本中唯讀載入 07 收集 3,940 個障礙物包圍盒、匯入 FBX、建立子關卡，再只把 23 個新檔複製回本專案（已逐檔比對）。

已通過：FBX 雜湊與尺寸、24 個放置與 07 物件及彼此不重疊（2D 包圍盒，間距 40／20 cm）、全部貼齊 ValleyGround 頂面 -15 cm、保存後重載位置與網格一致。4 張 UE 畫面已檢視（07 於記憶體中串流此子關卡，未保存）；south_meadow 截圖未產生。未做 PIE 通行、鍵鼠或效能測試。

裝好 VS 2022 並編譯模組後，執行 `Tools/assemble_town08.py`（**尚未執行過**）把子關卡串流進 07 並另存 TownLayout_08，再補 PIE 路線與外觀檢查。本機 `Unreal/` 的 LFS 指標檔已從 GitHub `main`（8128925）換成實體檔，4,962 個 SHA-256 全數相符。

證據：`wild08_sublevel.json`、`wild08_capture.json`、`wild08_palette.json`、`Validation/wild08_*.png`。工具：`Tools/extract_wild08_palette.py`（Blender）、`Tools/build_wild08_sublevel.py`、`Tools/capture_wild08.py`、`Tools/assemble_town08.py`。

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

## 2026-10-20 最新：TownLayout_03 客棧樓梯修正

最新與預設啟動／遊戲地圖為 `/Game/Maps/TownLayout_03`，保留 01／02。共 3,882 Actor，沒有新增或覆寫 Blender、FBX 或 Static Mesh。

客棧二樓隔間縮短，樓梯側留 159 cm 開口；第一張床的三個分件向房內移 125 cm，空出上樓後的轉彎平台。已另存、重新載入確認位移，並檢視四張實際 UE 截圖。

八項真實 PIE 檢查全部通過：市集道路、客棧入口、內梯、二樓轉彎、鐵匠鋪入口、庭院入口、客棧背牆阻擋、庭院圍欄阻擋。使用 CharacterMovement API、各段獨立傳送起點，並非連續全鎮通行或鍵鼠驗收。首次入口測點碰到長凳；第二次庭院測點因背景低更新率越過終點碰到池邊。測試改用入口通道中央與接近終點減速，保留原始兩次報告，最終八項通過；未放寬高度／通行斷言。

室內偏暗、第三人稱鏡頭貼牆、地板接縫、室內互動、全鎮導航、LOD 與效能仍待改善。此輪只完成客棧樓梯通行修正，不能視為全遊戲驗收。UE 變更尚未推送 GitHub。

證據：[修正與視覺檢查](town03_landing_revision.json)、[八項 PIE 結果](town_routes_TownLayout_03.json)、[樓梯出口](Validation/town03_landing_from_stairs.png)、[二樓轉彎](Validation/town03_landing_turn.png)、[全景](Validation/town03_overview.png)。

重現工具：`Tools/fix_inn_landing.py` 從 02 另存 03，拒絕覆寫；`Tools/validate_town03.py` 在已開啟的 03 執行測試與截圖；`Tools/preview_town03_overview.py` 補充轉彎和全景。驗證暫時關閉背景 CPU 節流以持續渲染，結束後還原，沒有保存偏好變更。

# UE5 第三人稱小鎮原型

## 2026-10-19 歷史：TownLayout_02

當時預設地圖為 `/Game/Maps/TownLayout_02`；`TownLayout_01` 與民宅原型 01/02 均保留。

- 完整小鎮共有 3,877 個 Static Mesh，87 種配色材質。新版加上燈光、出生點及曝光設定後共 3,882 個 Actor；包含客棧、民居、鐵匠鋪、道路階梯、牌樓、市集、水井與庭院。
- 新增全域曝光設定：固定 EV100 0、補償 +1、Bloom 0.1，修正遠景因黑色背景導致整片過曝。已另存、重新載入並核對設定，遠景與街道近景均完成視覺檢查。
- 重新載入後逐件核對尺寸及方向，最大包圍盒差異 1.34 cm（檢查容差 3 cm），3,877 分件均有 TownPalette01 材質，沒有遺漏。整體包圍盒與原檔差異小於 0.001 cm。
- 真實 Play In Editor 測試通過：入口落地、向前走入小鎮、中央階梯攀升、跳躍及落地。角色由入口 `(0,850,116)` cm 到中央平台約 `(0,-468,224)` cm。測試以引擎 CharacterMovement API 輸入進行，未替代實際鍵鼠、全鎮路線與鏡頭操作驗收。

尚待處理：全鎮路線與建築碰撞覆蓋、室內／互動、LOD／效能、背景山景，以及 FBX smoothing／tangent 警告。碰撞仍採靜態原型 Complex As Simple；程序木紋、石紋尚未烘焙，水面未製作動畫。未新增 Blender 幾何，既有每物件十視圖不變。這批 UE 變更尚未推送 GitHub。

### 驗證證據

- [匯入紀錄](town_import_validation.json)、[來源材質](town_palette.json)、[來源清單](import_manifest.json)
- [新版逐件檢查與真實 PIE 結果](town_playtest_validation.json)
- [新版曝光保存重載檢查](town02_exposure_validation.json)
- [遠景](Validation/town02_overview_final.png)、[街道近景](Validation/town02_street_final.png)：均為實際 UE 編輯器畫面。
- `town02_editor_view_during_pie.png` 擷取到的是編輯器視角，不能當作角色近景證據；PIE 通行證據以位置及 MovementMode 紀錄為準。

### 可重現流程

1. `Tools/extract_town_palette.py` 在 Blender 唯讀提取原檔配色。
2. `Tools/import_full_town.py` 在完整 UE Editor 匯入及建立 TownLayout_01；拒絕覆寫既有關卡。
3. `Tools/town_lighting.py` 從 01 建立曝光修正版 02，拒絕覆寫既有 02。
4. `Tools/validate_full_town.py` 核對 02 資產與執行真實 PIE 通行測試。
5. `Tools/finalize_town02.py` 將本輪 02 曝光補償調為 +1，保存、重載並擷取遠近景。

## 先前民宅原型紀錄（TownPrototype_02）


2026-10-19：UE 5.8.3 已安裝，專案為 [XiuXianTown.uproject](XiuXianTown/XiuXianTown.uproject)。目前可載入新版 `/Game/Maps/TownPrototype_02`，保留原始 `TownPrototype_01` 和 Epic `Lvl_ThirdPerson`。

## 本輪完成

- 首批方塊、長凳、民宅共 484 個匯入靜態網格；加上地面，關卡共 489 個 Actor。方塊 100 cm，長凳約 180 × 62 × 61 cm，匯入尺寸通過。
- 修正 FBX 匯入後的預設棋盤材質：從 Blender 原檔讀取色帶平均值、粗糙度及金屬度，為 483 個民宅／長凳分件加入材質覆寫。新版另存，不改原始模型或匯入網格資產。
- 新版重新載入後，485 個靜態網格 Actor（含地面與方塊）均使用對應材質，無遺漏。已檢視引擎畫面，恢復青綠瓦、暖木、淺灰石配色。
- 真正的 Play In Editor 測試通過：安全出生、移動、跳躍、落地、方塊阻擋、攀上民宅台階、關閉門片阻擋。此測試由引擎 API 驅動 CharacterMovement，未代替實際鍵鼠操作驗收。

## 開啟方式與待辦

原型 02 可從 Content/Maps 手動開啟。Play 後沿用 Epic 第三人稱控制設定。鍵盤、滑鼠、鏡頭貼牆與效能仍需人工實測，尚未完成完整可玩驗收。

民宅門目前是關閉的靜態模型，不具備開門或室內互動。完整 TownLayout 已於本輪另存為 TownLayout_01，詳見上方最新紀錄。

材質目前為原檔配色近似，木紋／石紋等程序細節尚未烘焙；碰撞採靜態原型 Complex As Simple，仍需 LOD、效能與正式碰撞整理。未新增 Blender 模型，現有每物件十視圖交付不變。這批 UE 變更尚未推送 GitHub，也未打包遊戲。

## 驗證證據

- [來源與雜湊](import_manifest.json)、[匯入尺寸](import_validation.json)
- [原始材質資料](blender_palette.json)、[材質重新載入檢查](material_repair_validation.json)
- [新版 PIE 結果與角色位置](playtest_validation.json)
- [引擎內角色與台階截圖](Validation/prototype02_stairs_pie.png)
- `engine_check.json` 為上一輪原型 01 的載入檢查，最新 02 請以上述兩份報告為準。

## 可重現工具

- `Tools/create_starter.py`：由已安裝 Epic 範本建立專案，拒絕覆寫既有專案。
- `Tools/build_town_test.py`：完整 UnrealEditor 的 `-ExecutePythonScript` 匯入與建立 01；會重建 01，手動修改請先另存。不能用沒有 Slate 的命令列匯入替代。
- `Tools/extract_palette.py`：Blender 背景唯讀擷取兩份原檔的材質資料。
- `Tools/repair_prototype_materials.py`：由 01 另存材質修正版 02，02 存在時拒絕覆寫。
- `Tools/reload_prototype02.py`：從磁碟載入 02、核對所有材質，接續 `playtest_prototype.py` 的真實 PIE 檢查。
- `Tools/observe_keyboard_play.py`：已準備的被動鍵鼠測試記錄器，尚未執行驗收。

## 環境與穩定性

本機 Mac M2／16 GB，Xcode 27.1，Metal Toolchain 27A266a，UE 5.8.3。首次圖形編輯器、原型儲存及重新載入已成功。

測試期間編輯器曾在 Slate／ICU 文字通知清理路徑發生記憶體釋放崩潰；原因尚未確定。重開後 02 關卡材質與上述七項 PIE 檢查再次通過，不能據此宣稱編輯器長時間穩定性已解決。`idevice_id` 的 x86 工具警告尚在，本輪未做 iOS 開發。
