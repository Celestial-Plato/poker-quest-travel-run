# TRAVEL RUN 安装说明

版本：0.3.6。支持 Windows x64 原版 Poker Quest v63 / build 2021。

## 第一次安装

1. 订阅工坊条目，等待 Steam 下载完成。
2. 从工坊条目查看条目 ID。打开游戏所在 Steam 库的 `steamapps\workshop\content\1184820\<条目ID>` 文件夹，找到本说明和 `InstallTravelRun.exe`。
3. 关闭游戏，双击 `InstallTravelRun.exe`（或 `InstallTravelRun.cmd`）。玩家不需要安装 Python。
4. 提示安装成功后，从 Steam 启动 Poker Quest。选择 New Run → Travel Run，再选择一项增益。

这是需要首次运行安装器的程序补丁模组，订阅本身不会修改菜单。不要仅使用原版 ModManager 的 Apply/Launch 来安装本包；安装器会同时处理菜单与 CSV。

自动定位使用 Steam 注册表和游戏库清单，没有开发者电脑路径。若找不到游戏、清单读取失败或检测出多份安装，会弹出 Windows 文件选择窗口，请选择游戏目录中的 `PokerQuest.exe`。取消选择会退出，不执行安装或还原；选错其他程序会提示重新选择。选定后仍需通过游戏版本校验。

若文件选择窗口无法打开，也可在本文件夹打开终端运行：

```bat
InstallTravelRun.exe --game-dir "D:\YourSteamLibrary\steamapps\common\Poker Quest"
```

路径仅为示例。路径或 Windows 用户名可以包含中文。程序没有自动管理员提权；如果系统提示目录不可写，可将游戏移到可写的 Steam 库后安装。

## 内容与存档

TRAVEL RUN 提供 22 项旅途增益，每次选一项。具体数值见 EFFECTS.md。

安装器从玩家本地原版程序生成补丁并替换 `PokerQuest.exe`，原版备份为游戏目录中的 `PokerQuest.before-TravelRun.exe`。发布包不包含原版 EXE、游戏 DLL 或游戏素材。

Travel Run、普通模式的 XP、角色解锁、进度和 Mod Manager 共用原版目录：

```text
%APPDATA%\Playsaurus\PokerQuest
```

安装和更新直接沿用原版进度，不重置 XP 或角色解锁，无需选择或切换存档。安装后请开始新一局。

安装器保留其他已应用 Mod 的 CSV、图片和启用列表，把 Travel 增益注册成正常数据模组。以后在 Mod Manager 中保留 Travel Run 勾选，勾选 Boss Courts 或其他 Mod 后 Apply，再重启游戏即可；模组之间修改同一数据的冲突仍按原版加载顺序处理。

每次从 New Run 打开 Travel Run 时，会先把现有 `.sol` 存档复制到 `%APPDATA%\Playsaurus\PokerQuest\TravelRun-backups\<时间>`。目录名使用 UTC 时间并以 Z 标记，每次生成新快照；备份失败时不会打开 Travel Run。备份是当时的全部进度，手动还原会回到那个时间点。

需要还原进度时，关闭游戏，双击 `RestoreSaves.cmd`，粘贴要恢复的备份文件夹路径。工具会先备份当前进度，验证所选快照完整后再还原。也可用 `InstallTravelRun.exe --restore-saves "备份目录"`。升级和安装前的备份位于 `%LOCALAPPDATA%\Playsaurus\PokerQuestTravelRun\backups`。此工具与还原游戏程序的 `RestoreOriginal.cmd` 分开。

## 更新与恢复

工坊更新下载后，关闭游戏，再运行一次安装器。新包更新 Travel 增益和程序补丁，保留共用进度及其他模组。保留的旧版 56 条隐藏定义用于早期 TRAVEL RUN 存档兼容，新菜单仅展示 22 项。

恢复原版程序：关闭游戏，双击 `RestoreOriginal.cmd`；或运行 `InstallTravelRun.exe --restore`。只恢复已校验的原版程序，共用进度和备份保留。需要停止加载 Travel 增益时，在 Mod Manager 取消勾选 Travel Run 并 Apply；其他模组按自己的勾选状态继续使用。

安装器还会把还原工具缓存到：

```text
%LOCALAPPDATA%\Playsaurus\PokerQuestTravelRun\installed-tools\RestoreOriginal.cmd
```

取消订阅不会自动恢复程序。请先恢复再取消订阅；若已取消，仍可使用上述缓存工具。恢复后要重新安装可再次运行安装器。

若 Steam 验证文件完整性、更新或重装游戏，程序补丁可能被覆盖；检查版本后重新运行安装器。检测到不支持的游戏版本时会停止，不能强制套用旧补丁。

## 检查与问题反馈

`InstallTravelRun.exe --check` 只检查包和支持的程序版本，不安装或启动游戏。失败时保留窗口信息，并反馈游戏版本和具体报错。不要发送存档或个人路径给公开工坊评论。
