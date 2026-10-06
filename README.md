# Poker Quest TRAVEL RUN

为 Poker Quest 增加类似 Challenge Run 的 TRAVEL RUN 选择列表，每局选择一项增益，共 22 项。替换 Custom Run 菜单入口。支持 **Windows x64 / 原版 v63、build 2021**；不支持的程序哈希会拒绝安装。

## 玩家安装

1. 在 [Releases](https://github.com/Celestial-Plato/poker-quest-travel-run/releases) 下载 `TravelRun-Installer-v0.3.2.zip` 和校验文件，解压整个 ZIP。
2. 关闭游戏，运行解压后的 `InstallTravelRun.exe`。无需安装 Python。
3. 安装器读取 Steam 注册表、Steam 库配置和游戏安装清单定位目录；找不到或找到多份安装时，会弹出文件选择窗口，请选择游戏的 `PokerQuest.exe`。
4. 从 Steam 启动游戏，选择 **New Run → Travel Run**，选择一项增益并开始新一局。

工坊数据条目：[3814137517](https://steamcommunity.com/sharedfiles/filedetails/?id=3814137517)。工坊条目已公开，可正常订阅。**GitHub 的完整安装包可独立使用**；订阅工坊本身不会安装原生菜单。

安装器核对原版程序和 CSV 的哈希，备份原版程序，再安装菜单补丁及匹配的增益数据。更新时下载完整新版本 ZIP 后重新运行安装器。详见包内中英文说明与 [增益列表](EFFECTS.md)。

## 存档与恢复

独立存档目录：`%LOCALAPPDATA%\Playsaurus\PokerQuestTravelRun\appdata\Playsaurus\PokerQuest`。初次安装复制已有进度，保留原版存档；TRAVEL RUN 的 Steam Cloud 关闭。

需要恢复原版时，关闭游戏，运行 `RestoreOriginal.cmd`。取消订阅不会自动还原。还原工具也缓存于 `%LOCALAPPDATA%\Playsaurus\PokerQuestTravelRun\installed-tools`。还原只接受已核对的备份和已安装程序，不覆盖未知修改。

## 开发者构建

源码包含安装器、Steam 目录识别、文件选择窗口、菜单补丁 C 源码，以及项目自己的增益数据和版本限定补丁描述。**不包含游戏原版 EXE、DLL、素材或个人存档。**

在 Windows x64 上安装 Python 3.11，并运行：

```powershell
py -3.11 -m pip install -r requirements-build.txt
py -3.11 build_release.py
```

这会使用仓库中已有的原生补丁构建独立安装器和 ZIP，不运行安装器或游戏。需要重编原生补丁时，在 x64 Visual Studio 开发者终端运行：

```powershell
py -3.11 native/build_native.py
py -3.11 build_release.py
```

原生补丁使用对应游戏版本的固定地址；支持新游戏版本前必须重新分析并审核地址和事件，不应放宽哈希检查。重新构建的二进制可能因编译器和时间戳不同而有不同哈希，构建脚本会更新对应清单。

## English

Download and extract the complete installer ZIP from Releases, close Poker Quest, run InstallTravelRun.exe, then launch through Steam and choose New Run → Travel Run. No Python is required for players. If Steam discovery fails, select PokerQuest.exe in the file picker.

Windows x64 / Poker Quest v63, build 2021 only. The native menu needs this installer; subscribing to the Workshop CSV/docs alone is insufficient. The GitHub package also works independently of a Workshop subscription. Separate local saves, Steam Cloud disabled for Travel Run. RestoreOriginal.cmd restores the verified original executable.

**Build and static package checks completed; in-game validation remains pending.** This is an unofficial community modification.
