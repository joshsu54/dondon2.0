# dondon2.0

修仙開放世界專案：UE5 遊戲開發與 Blender 美術素材。

## 目前預設：TownLayout_13（Q 版玩家角色）

預設啟動與遊戲關卡為 `TownLayout_13`：宗門經營版（12 的弟子工作與尋路）加上 Q 版男玩家角色（Q 版人物 17 v006，含待機與走路動作）。`開始遊玩.ps1` 也啟動 13。需要先編譯含 `QCharacterAnimDriver` 的 C++ 模組。角色 PIE 測試與經營回歸 70 項通過（`Unreal/qplayer13_runtime.json`、`Unreal/management13_runtime.json`）；移動速度為 204 cm/s（配合走路步幅），尚無跑步與跳躍動作，也未做實體鍵鼠全流程驗收。舊關卡 01–12 保留。

## 宗門經營試玩版（TownLayout_10 起）

新增南側重建營地，串接採藥、招募石砥／林溪／岳青、弟子分工、糧食與木石生產、藥圃／弟子舍／靜修臺建設、建材委託、宗門晉升與本機存檔。舊關卡 01–09 保留。

操作與第一輪流程見 [宗門經營試玩說明](Unreal/宗門經營試玩.md)。Windows 本機可執行 `開始遊玩.ps1`（現在啟動 13）；也可在 UE Editor 選擇 `TownLayout_13`（或 10–12）按 Play。NPC 仍為簡化人形，尚未實作弟子尋路或正式打包。

以下 09 說明為原本小鎮版本紀錄；10 的測試結果見 `Unreal/management10_runtime.json`。

## 開啟專案

使用 Git LFS 取得完整模型、圖片與 UE 資產：

```sh
git clone https://github.com/joshsu54/dondon2.0.git
cd dondon2.0
git lfs pull
```

以 UE 5.8 開啟 `Unreal/XiuXianTown/XiuXianTown.uproject`。Mac 首次開啟需 Xcode／Metal 工具並編譯 C++ 模組。

預設關卡已改為 TownLayout_13（見上方）。10（宗門經營版）的 PIE 功能檢查 71 項通過，包含局部連續行走與存檔重開。原 09 保留小鎮、野外植被與客棧補光。實體 E 鍵互動最後驗證於 06；本輪 10 使用反射互動，不代表全程手動鍵鼠驗收。

## 美術素材

最新地形研究：開啟 [凌雲山谷十角度對照圖庫](ArtLibrary/ExpansionBatches/LingyunValleyTerrain14/index.html)，包含 10 張概念圖與 10 張同一 Blender 模型渲染。可編輯原檔為 `Models/LingyunValleyTerrain/v002/LingyunValleyTerrain_v002.blend`；此地形仍為外觀初模，尚未套入遊戲關卡。

89 組素材、890 張基本角度圖；模型原檔及 FBX 位於 `Models/`，圖庫位於 `ArtLibrary/`，參考圖與製作腳本分別位於 `ArtReferences/`、`BlenderSource/`。沿用青綠瓦、暖木、淺灰石與淡玉畫風。

詳見 [交接紀錄](HANDOFF.md)、[UE5 說明](Unreal/README.md) 與 [素材圖庫](ArtLibrary/index.html)。

此儲存庫從目前 Blender／UE5 檔案建立乾淨初始版本，不包含舊引擎專案與其 Git 歷史。快取、登入資訊、編譯產物不納入版本庫。
