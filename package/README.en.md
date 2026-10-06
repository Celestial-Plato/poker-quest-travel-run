# TRAVEL RUN

Version 0.3.6. Windows x64, Poker Quest v63 / build 2021 only.

1. Download the complete matching installer ZIP from GitHub Releases. No Workshop subscription is required.
2. Extract the entire ZIP into a writable folder. Keep the installer together with all its data and patch files.
3. Close Poker Quest and run `InstallTravelRun.exe` once. No Python installation is needed for players.
4. Launch the game from Steam. Choose New Run → Travel Run, then one of the 22 bonuses.

Downloading alone cannot install the native menu. Do not use only the original ModManager Apply/Launch for this package. The installer handles both the local executable patch and CSV data. It never launches the game.

Steam registry entries and library manifests locate your installation automatically. If discovery fails, its manifests cannot be read, or multiple installations are found, a Windows file picker asks you to select `PokerQuest.exe`. Cancel to exit without installing/restoring. Selecting another executable prompts you to try again; game-version verification still applies to the selected file. If the picker is unavailable, run `InstallTravelRun.exe --game-dir "D:\YourSteamLibrary\steamapps\common\Poker Quest"`. Chinese/non-ASCII save paths are supported.

The executable is patched locally from your own game installation. The original backup is `PokerQuest.before-TravelRun.exe` in the game folder. No original game executable, DLL, artwork or save is distributed.

Travel Run, ordinary modes, XP, hero unlocks and Mod Manager share `%APPDATA%\Playsaurus\PokerQuest`. Installation and updates keep your original-game progress, without resetting XP or hero unlocks. No save selection or switching is needed. Start a new run after installation.

Other applied mod tables, images and selections are preserved. Keep Travel Run checked in Mod Manager, select Boss Courts or other mods, Apply and restart. Ordinary mod-order conflicts still apply.

Opening New Run → Travel Run first snapshots every existing `.sol` file into `%APPDATA%\Playsaurus\PokerQuest\TravelRun-backups\<timestamp>`. UTC names end in Z; snapshots never overwrite one another. Backup failure prevents opening Travel Run. To restore progress, close the game, run `RestoreSaves.cmd` and paste the selected backup directory, or run `InstallTravelRun.exe --restore-saves "backup directory"`. Current progress is backed up before restoration. Installation/upgrade backups are under `%LOCALAPPDATA%\Playsaurus\PokerQuestTravelRun\backups`. Restoring a snapshot rolls all progress back to that time.

After a new release, download and extract its complete new ZIP, close the game and run its installer again. Shared progress and other mods remain. 56 hidden legacy definitions are included for compatibility with early Travel Run saves; only 22 current choices appear in the menu.

To restore the program: close the game and run `RestoreOriginal.cmd` or `InstallTravelRun.exe --restore`. Shared progress and backups remain. Uncheck Travel Run and Apply in Mod Manager to stop loading its bonus data. Restore before deleting the downloaded package; deletion alone does not undo the patch. A copy of the restore tool remains in `%LOCALAPPDATA%\Playsaurus\PokerQuestTravelRun\installed-tools\RestoreOriginal.cmd` even after deleting the downloaded package.

Steam file verification, game updates or reinstallation can replace the patch. Re-run the installer only for a supported game version. `InstallTravelRun.exe --check` checks package files and executable compatibility without installing or launching the game.

See EFFECTS.md for the choices and values.
