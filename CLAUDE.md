2026-10-24 最新：預設關卡改為 TownLayout_13（12 的宗門經營＋弟子工作，玩家換成 Q 版人物 17 v006 男玩家，含待機／走路；C++ 新增 QCharacterAnimDriver）。角色 PIE 與經營回歸 70 項通過；未提交、未推送、未打包。先讀 HANDOFF.md 頂部。以下為較早紀錄。
2026-10-24 最新指示：使用者已停止人物、髮型與服裝製作；其他素材繼續。只採用 QPlayerStart16 的 10 組非人物初模與洞府配置，人物舊試作不列為採用。宗門選拔改為「創角後現實經過整整 10 天，離線照常計時」，不要求累積在線時數。請先讀 HANDOFF.md 頂部、Story/玩家成長與宗門秘境_需求紀錄.md 與 ArtLibrary/ExpansionBatches/QPlayerStart16/README.md。以下為歷史紀錄。

2026-10-23 本輪最新：使用者指定「經營宗門＋招募弟子」。預設關卡已改為 TownLayout_10，新增南側重建營地與 SectAdventure 導演，PIE 71 項功能檢查通過（反射互動、營地局部行走、缺糧恢復、存檔重開）。舊關卡 01–09 保留。先讀 HANDOFF.md 頂部與 Unreal/宗門經營試玩.md；本輪未提交、未推送、未正式打包。下方為歷史紀錄。

# Claude Code 接手規則



- 使用者已指定沿用過去畫風：以 SectCore04 的青綠瓦、暖木、淺石、淡玉及柔光為基準；TownRefinement12 已將小鎮 18 項素材另存 v002，最新小鎮場景為 TownLayout v004。閱讀該批次 README 與 validation 後接續。
- 目前主線：UE5 第三人稱小鎮開發。最新與預設關卡 TownLayout_09（08 的野外植被子關卡＋客棧室內補光），PIE 38 項通過（任務路線、草地、植被碰撞）。06 的實際 E 鍵驗證是最後一次實體按鍵測試；09 的 PIE 以 API 驅動，不代表全程手動行走；效能與打包尚未驗收。Windows 本機已可編譯 C++ 模組（VS 2022）。讀 HANDOFF.md 頂部最新紀錄，保留舊版。
- 每個獨立交付物件至少 10 個不同方位／角度。以同一模型渲染正前、右、後、左、四斜角、頂視、高前視；組合圖及動畫影格不能取代單項十視圖。
- 交付可編輯 .blend、FBX、1024×1024 PNG、views.json、model_info.json、validation.json、圖庫頁面。1 單位 = 1 公尺，正面 -Y，底部中心原點。
- 保留版本與分件。既有模型不要直接覆寫，先使用新的 vNNN 或新批次。生成腳本的跳過條件與寫入位置各不相同，執行前必須閱讀。
- 檢查 `git status`，保留使用者及其他工作中的修改；不要重設分支或強制推送。
- 分支 `solid-clouds-karst-peaks` 包含最新素材；`main` 不是完整最新版本。
- `ArtLibrary/asset_catalog.json` 是已登錄素材索引，但部分山峰、雲霧條目仍指向舊版；參照 HANDOFF.md 的版本表，核對後才更新索引。
- `Models/` 與 `ArtLibrary/Turnarounds/` 是主交付位置；`ExpansionBatches/` 保存完整批次副本。更新時核對兩處檔案雜湊，不要只更新其中一處。
- 圖庫／檢查報告只能宣稱實際通過的檢查。FBX 在 Blender 回匯不等於 Unreal 驗證；UV 烘焙、碰撞、LOD、導航、角色可通行目前仍有大量待辦。
- 外觀檢查需要打開渲染結果。檢查開檔、FBX 回匯尺寸、圖片數、角度、裁切及修改相關幾何；不需要重跑無關大型建置。
- `work/` 是忽略的本機暫存；不要依賴其中腳本完成新批次安裝。必要的可重現工具應保存到版本庫內。
- 不要提交 `.env`、登入資訊、虛擬環境、快取或本機工具下載。大檔使用現有 Git LFS 規則。GitHub CLI 的本機登入不會隨交接包移轉。

先跑 `python3 Tools/Handoff/verify_project.py` 做唯讀盤點；這個檢查不啟動 Blender，不更動模型。

## UE 小鎮更新（2026-10-20，最新 03）

最新與預設關卡為 `/Game/Maps/TownLayout_03`，01／02 保留。3,877 分件、87 種材質、3,882 Actor。客棧樓梯側隔間留出 159 cm 開口，第一張床移開 125 cm；已保存重載、八項真實 PIE 通行／阻擋測試通過，四張 UE 畫面已檢視。只調整四個 UE Actor，原始 Blender／FBX 不變。

詳見 `Unreal/README.md`、`Unreal/town03_landing_revision.json`、`Unreal/town_routes_TownLayout_03.json`。測試使用各段獨立起點與 CharacterMovement API；連續全鎮路線、鍵鼠、室內照明、第三人稱鏡頭貼牆、地板接縫、互動、背景山景、LOD 與效能仍待處理。尚未推送 GitHub。
