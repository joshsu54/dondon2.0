# dondon2.0

修仙開放世界專案：UE5 遊戲開發與 Blender 美術素材。

## 開啟專案

使用 Git LFS 取得完整模型、圖片與 UE 資產：

```sh
git clone https://github.com/joshsu54/dondon2.0.git
cd dondon2.0
git lfs pull
```

以 UE 5.8 開啟 `Unreal/XiuXianTown/XiuXianTown.uproject`。Mac 首次開啟需 Xcode／Metal 工具並編譯 C++ 模組。

預設關卡為 TownLayout_06，已通過保存檢查、11 段 PIE 路線及五次實際 E 鍵互動。TownLayout_07 包含基座與照明修整，但通行驗證中斷、外觀尚待檢查；請勿視為完成版本。

## 美術素材

84 組素材、840 張基本角度圖；模型原檔及 FBX 位於 `Models/`，圖庫位於 `ArtLibrary/`，參考圖與製作腳本分別位於 `ArtReferences/`、`BlenderSource/`。沿用青綠瓦、暖木、淺灰石與淡玉畫風。

詳見 [交接紀錄](HANDOFF.md)、[UE5 說明](Unreal/README.md) 與 [素材圖庫](ArtLibrary/index.html)。

此儲存庫從目前 Blender／UE5 檔案建立乾淨初始版本，不包含舊引擎專案與其 Git 歷史。快取、登入資訊、編譯產物不納入版本庫。
