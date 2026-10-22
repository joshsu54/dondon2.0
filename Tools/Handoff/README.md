# 完整交接包

Git clone + Git LFS 是需要繼續版本控制時的首選。Release 分卷則提供完整實體檔案，方便無 Git LFS 的環境還原；包含所有已追蹤素材、圖片、影片、歷史交付 ZIP、劇本與程式碼，不含 .git、work、快取或登入資訊。

打包使用 tar 內部重複檔案參照減少容量；還原工具會複製成各自獨立的檔案，不讓不同版本共用可修改的硬連結。外層 gzip 切成 700 MB 以下分卷。還原後占用約 4.75 GB，另需分卷與臨時壓縮檔空間，建議至少預留 12 GB。

## 還原

將 Release 的 `dondon-handoff.tar.gz.part*`、`handoff-manifest.json`、`restore_handoff.py` 放在同一個新資料夾：

```sh
python3 restore_handoff.py --destination ./dondon-handoff
cd dondon-handoff
python3 Tools/Handoff/verify_project.py
```

Windows 若命令名稱不同，可使用 `py -3` 代替 `python3`。目標資料夾必須為空；程式會先核對每卷 SHA-256，再還原並逐檔校驗。需要 Python 3.9+，沒有額外套件依賴。

還原不會登入 GitHub，也不會啟動 Claude Code 或 Blender。接手時在還原／clone 的專案目錄開啟 Claude Code，讀 CLAUDE.md 與 HANDOFF.md。

## 維護者重建

先提交要交付的完整快照並確保工作樹乾淨，再執行：

```sh
python3 Tools/Handoff/build_bundle.py --output work/handoff/new-release
python3 Tools/Handoff/restore_handoff.py --bundle-dir work/handoff/new-release --destination work/handoff/restore-check
```

新包只能從已提交且 LFS 已還原的檔案建立。先驗證還原樹的 `verify_project.py`，再發布 Release。不要把交接包再放進 Git LFS，以免重複儲存整個版本庫；發布為 Release 附件即可。
