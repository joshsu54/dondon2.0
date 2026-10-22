# Blender 工具安裝紀錄

2026-10-15 完成。

- Computer Use：沿用已安裝的工具，已成功開啟 Blender 5.3 並擷取視窗。
- Blender MCP：PyPI `mcp-for-blender==2.1.9`，安裝在本資料夾 `.venv`，相依版本見 `requirements.lock.txt`。
- 外掛：已在 Blender 5.3 和 5.4 的使用者外掛資料夾安裝並啟用。既有偏好設定如存在，已先建立帶時間戳記的 `.bak`。
- Codex：全域 MCP 名稱 `blender`，啟動器為本資料夾 `start-mcp`。已透過實際 MCP 工具讀取 Blender 5.3 的預設場景，協定版本 13 相符。
- Blender CLI：沿用 `/Applications/Blender 2.app/Contents/MacOS/Blender`，專案捷徑為 `Tools/bin/blender`，已驗證背景 Python 執行。

## 使用

開啟 Blender 2.app，外掛會自動啟動本機連線。若手動停止過，可在 3D 視窗按 N，從 MCP 面板重新啟動。避免同時開啟兩個 Blender 搶用同一連接埠。

在專案根目錄執行 CLI：

```sh
./Tools/bin/blender --background --python BlenderSource/MaterialShop/build_material_shop.py
```

這會執行建模腳本；請先查看該腳本的輸出位置。CLI 捷徑未修改系統 PATH。

MCP 啟動器連到 `127.0.0.1:9876`，設定 `DISABLE_TELEMETRY=true`；Blender 外掛的遙測同意維持關閉。素材服務與付費生成服務未啟用。

獨立環境與 Codex 設定使用絕對路徑；若移動專案資料夾，需重建環境並更新連線路徑。

來源：[MCP for Blender](https://github.com/ahujasid/mcp-for-blender)（社群專案）、[Codex MCP 文件](https://developers.openai.com/codex/mcp)。
