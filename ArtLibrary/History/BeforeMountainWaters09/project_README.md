# dondon｜修仙開放世界美術素材

宗門、山景、登山步道與生活道具的 Blender 素材專案。模型、圖片、影片與 ZIP 交付包使用 Git LFS 管理。

目前素材庫有 **60 組模型、600 張基本角度圖、3 個配置場景**。每組獨立素材至少有十個方位與角度；另有 4 秒山風與雲霧動態預覽。

- 最新登山路線：`ArtLibrary/ExpansionBatches/MountainRoute08/`。
- 山頂宗門與登山步道：`Models/MountainSanctuary/v002/`。
- 山風與雲霧：`Effects/WindFog/v001/`。
- 模型屬於可編輯外觀原型；引擎碰撞、導航、UV 烘焙與 LOD 尚未完成。

## 下載完整模型與圖片

先安裝 Git 與 Git LFS，再執行：

```sh
git lfs install
git clone https://github.com/joshsu54/dondon.git
cd dondon
git lfs pull
```

請從本機開啟 `ArtLibrary/index.html` 瀏覽素材與十視圖。單獨下載文字指標檔不會取得模型本體；完整交付包位於 `Deliverables/`。工作暫存、本機虛擬環境與登入資訊不納入版本庫。

## 專案方向

目前方向：**Blender 製作模型與建模參考圖，Unreal Engine 作為後續遊戲開發環境**。現階段優先準備美術素材，Unity 系統擴充已暫停。

素材入口：`ArtLibrary/index.html`；說明與待製作項目：`ArtLibrary/README.md`、`ArtLibrary/完整建模清單.md`。交付包位於 `Deliverables/UnrealArtPrep_vNNN.zip`。

下方 Unity 說明保留作為歷史原型紀錄，並非目前的 Unreal 開發步驟。`Assets/XiuXian/Runtime/Sect/Core` 的兩個 C# 檔只是中途保留的核心草稿，尚未編譯、整合或完成可玩流程。

## 目前內容

- 鍵盤移動、奔跑、跳躍、重力、落出地圖後回到起點。
- 滑鼠旋轉鏡頭、滾輪縮放、球形偵測縮短鏡頭距離以減少牆壁遮擋。
- 一鍵產生灰盒測試場景：小鎮道路、四間建築占位、樹林、跳躍階梯、宗門門樓、秘境標記。
- 建築與秘境目前只有外觀占位，尚無買賣、料理、傳送、戰鬥或修煉功能。

這是可匯入的原始碼與模型素材包，**不是已建立、已執行驗證的完整 Unity 專案**。目前已使用 Blender 製作迎客松、出生廣場、新手民宅與鐵匠鋪，並組合成小鎮街道原型；尚未完成 Unity 編譯、模型匯入和實機操作驗證。

## Blender 模型

- `Models/WelcomingPine/v002`：迎客松 Blender 檔、FBX 與渲染圖。
- `Models/SpawnTown`：版本化出生廣場，包含青石路、階梯、出生石台、石燈、木構牌樓、指路碑、長凳與迎客松。
- `Models/StarterHouse`：版本化新手民宅，包含木構灰牆、青瓦屋頂、格窗、雙扇門、前廊與石階。
- `Models/TownLayout`：出生廣場、東側民宅與連接步道組合成的第一段小鎮街道。
- `Models/Blacksmith`：半開放鐵匠鋪與爐灶、鐵砧、工作台、武器架、水桶等可編輯道具；新版 `Models/TownLayout` 已加入鐵匠鋪與環形步行路線的空間配置。
- `BlenderSource/Blacksmith/README.md`：鐵匠鋪分件、生成方式與目前限制。
- `BlenderSource/SpawnTown/小鎮街道配置.md`：組合場景的位置、編輯方式與驗證範圍。
- `BlenderSource/StarterHouse/README.md`：民宅零件分組、門軸操作、尺度與交接限制。
- `BlenderSource/SpawnTown/出生小鎮建模清單.md`：各批模型、製作順序與交接限制。
- `BlenderSource/SpawnTown/build_spawn_town.py`：使用 Blender 背景模式生成場景，既有版本不會覆寫。

## 啟動方式

1. 在 Unity Hub 安裝 Unity 6 編輯器，建立 **Universal 3D（URP）** 專案。Built-in 3D 亦為程式預定支援範圍；HDRP 不在此原型範圍內。
2. 把本資料夾內的 `Assets/XiuXian` 複製到新專案的 `Assets` 裡。不要把這個素材包資料夾當成完整 Unity 專案開啟。
3. 等待編譯，確認 Console 沒有紅色錯誤。
4. 在選單選 **XiuXian → Create Prototype Scene**。若原場景有未儲存變更，Unity 會先詢問是否儲存。
5. 場景和材質會產生在 `Assets/XiuXian/Generated/Prototype`；再次產生使用新的編號資料夾，不覆蓋舊版本。
6. 按 **Play**，點一下 Game 視窗開始操作。

輸入程式會優先使用啟用中的 Input System；否則走舊版 Input Manager。舊版路徑使用預設 `Mouse X`、`Mouse Y` 軸。這一版只涵蓋鍵盤滑鼠，尚未提供手把、手機或按鍵重綁。

| 操作 | 按鍵 |
| --- | --- |
| 移動 | W / A / S / D |
| 奔跑 | 左 Shift |
| 跳躍 | Space |
| 轉動鏡頭 | 滑鼠 |
| 拉近／拉遠 | 滾輪 |
| 釋放游標、暫停操作輸入 | Esc |
| 恢復操作 | 點擊 Game 視窗 |

Esc 不會暫停世界時間。切換到其他視窗後也會釋放游標，回來點擊才恢復操作。

## 在 Unity 驗收

- 前後左右移動，轉動鏡頭後確認 W 仍往鏡頭朝向前進。
- 比較直走和斜走速度，檢查斜走沒有加速。
- 奔跑、跳上階梯，確認空中不能連續起跳，撞到頂部會停止上升。
- 靠近建築繞轉鏡頭、縮放，檢查遮擋；極窄空間仍需後續調整鏡頭策略。
- Esc 與切換視窗後，確認游標可操作且角色不繼續接收移動輸入。
- 走出地板邊緣，確認掉落後回到起點。
- 儲存、關閉再重開生成的場景，確認腳本與材質引用仍正常。

## Blender 素材製作約定

以下是本專案採用的製作規格，正式匯出設定待第一件素材往返匯入驗證後固定：

- 以 1 Unity 單位代表 1 公尺；人物目標高度約 1.8 公尺。
- 建築和道具原點放在底部中心；人物骨架根節點放在腳底。
- 先做 1 公尺測試方塊，以 FBX 匯入驗證尺寸、朝向、材質，再製作正式模型。
- 遊戲素材放 `Assets/XiuXian/Art`；Blender 原始檔放 Unity 專案外的 `BlenderSource`，以 FBX 作為交接檔案。
- 第一次先做一把劍、一棟鐵匠鋪外觀及一塊山石，確認統一比例與風格。
- 替換玩家 Visual 時保留 Player 的 CharacterController，移除舊膠囊與方向標記，將 `ThirdPersonMotor.visual` 指向新模型。新模型及子物件採 Ignore Raycast 圖層，避免鏡頭撞到自己。
- 正式人物動畫、骨架重定向與 Root Motion 尚未加入；目前位移由 CharacterController 驅動。

## 後續製作順序

1. 在 Unity 跑通此原型，確定操作與人物尺度。
2. 增加互動按鍵、採藥點、物品資料與背包。
3. 加入一種妖獸、普通攻擊、一個法術、掉落。
4. 串起一名委託 NPC、商店及一個採藥任務。
5. 加入修煉與煉氣到築基的進度，再做可進入的第一處秘境。
6. 用 Blender 正式素材逐步替換灰盒。

## 技術參考

- [Unity CharacterController.Move 官方文件](https://docs.unity.com/en-us/engine/6000.0/script-reference/unityengine/charactercontroller/move)：移動與碰撞由 CharacterController 處理；程式另外計算重力。
- [Unity Input System 安裝與輸入後端文件](https://github.com/Unity-Technologies/InputSystem/blob/develop/Packages/com.unity.inputsystem/Documentation~/Installation.md)：依輸入後端的編譯符號選擇輸入路徑。
