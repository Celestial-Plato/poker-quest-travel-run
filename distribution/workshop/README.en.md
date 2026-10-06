# TRAVEL RUN

Version 0.3.5. Windows x64, Poker Quest v63 / build 2021 only.

1. Subscribe and wait for Steam to finish downloading.
2. Locate this Workshop item's folder: `<Steam library>\steamapps\workshop\content\1184820\<item ID>`.
3. Close Poker Quest and run `InstallTravelRun.exe` once. No Python installation is needed for players.
4. Launch the game from Steam. Choose New Run → Travel Run, then one of the 22 bonuses.

Subscription alone cannot install the native menu. Do not use only the original ModManager Apply/Launch for this package. The installer handles both the local executable patch and CSV data. It never launches the game.

Steam registry entries and library manifests locate your installation automatically. If discovery fails, its manifests cannot be read, or multiple installations are found, a Windows file picker asks you to select `PokerQuest.exe`. Cancel to exit without installing/restoring. Selecting another executable prompts you to try again; game-version verification still applies to the selected file. If the picker is unavailable, run `InstallTravelRun.exe --game-dir "D:\YourSteamLibrary\steamapps\common\Poker Quest"`. Chinese/non-ASCII user paths are supported by the generated save-path literal.

The executable is patched locally from your own game installation. The original backup is `PokerQuest.before-TravelRun.exe` in the game folder. No original game executable, DLL, artwork or save is distributed.

Separate saves: `%LOCALAPPDATA%\Playsaurus\PokerQuestTravelRun\appdata\Playsaurus\PokerQuest`. On first installation existing `.sol` progress and display settings are copied; verified earlier Travel Run saves are preferred. Original saves are left intact. Steam Cloud is disabled for Travel Run. Start a new run after installation. This isolated profile loads Travel Run only, without combining other mods.

After a Workshop update, close the game and run the installer again. Travel saves remain. 56 hidden legacy definitions are included for compatibility with early Travel Run saves; only 22 current choices appear in the menu.

To restore: close the game and run `RestoreOriginal.cmd` or `InstallTravelRun.exe --restore`. Travel saves and backups remain. Restore before unsubscribing; unsubscription alone does not undo the patch. A copy of the restore tool remains in `%LOCALAPPDATA%\Playsaurus\PokerQuestTravelRun\installed-tools\RestoreOriginal.cmd` even after unsubscribing.

Steam file verification, game updates or reinstallation can replace the patch. Re-run the installer only for a supported game version. `InstallTravelRun.exe --check` checks package files and executable compatibility without installing or launching the game.

See EFFECTS.md for the choices and values.
