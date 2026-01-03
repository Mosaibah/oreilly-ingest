"""Platform-specific system operations plugin."""

import platform
import shutil
import subprocess
from pathlib import Path

from plugins.base import Plugin


class SystemPlugin(Plugin):
    """
    Platform-specific system operations.

    Responsibilities:
    - Show native folder picker dialogs
    - Reveal files in file manager
    - Platform detection
    """

    def get_platform(self) -> str:
        """Return the current platform identifier."""
        return platform.system()

    def show_folder_picker(self, initial_dir: Path | str | None = None) -> Path | None:
        """
        Show native folder picker dialog.

        Args:
            initial_dir: Initial directory to show in dialog

        Returns:
            Selected path or None if cancelled/failed
        """
        system = self.get_platform()
        initial = str(initial_dir) if initial_dir else None

        try:
            if system == "Darwin":
                return self._show_macos_picker(initial)
            elif system == "Linux":
                return self._show_linux_picker(initial)
            elif system == "Windows":
                return self._show_windows_picker(initial)
        except subprocess.TimeoutExpired:
            return None
        except Exception:
            return None

        return None

    def _show_macos_picker(self, initial_dir: str | None) -> Path | None:
        """Show macOS folder picker using osascript."""
        if initial_dir:
            script = (
                f'POSIX path of (choose folder with prompt "Select Download Folder" '
                f'default location POSIX file "{initial_dir}")'
            )
        else:
            script = 'POSIX path of (choose folder with prompt "Select Download Folder")'

        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0:
            return Path(result.stdout.strip())
        return None

    def _show_linux_picker(self, initial_dir: str | None) -> Path | None:
        """Show Linux folder picker using zenity or kdialog."""
        if shutil.which("zenity"):
            cmd = [
                "zenity",
                "--file-selection",
                "--directory",
                "--title=Select Download Folder",
            ]
            if initial_dir:
                cmd.extend(["--filename", initial_dir + "/"])
        elif shutil.which("kdialog"):
            cmd = [
                "kdialog",
                "--getexistingdirectory",
                initial_dir or ".",
                "--title",
                "Select Download Folder",
            ]
        else:
            return None  # No dialog tool available

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode == 0:
            return Path(result.stdout.strip())
        return None

    def _show_windows_picker(self, initial_dir: str | None) -> Path | None:
        """Show Windows folder picker using PowerShell."""
        ps_script = """
Add-Type -AssemblyName System.Windows.Forms
$dialog = New-Object System.Windows.Forms.FolderBrowserDialog
$dialog.Description = "Select Download Folder"
$dialog.ShowNewFolderButton = $true
if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
    Write-Output $dialog.SelectedPath
}
"""
        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
        return None

    def reveal_in_file_manager(self, path: Path | str) -> bool:
        """
        Open file manager and select the specified file.

        Args:
            path: Path to reveal

        Returns:
            True if successful, False otherwise
        """
        path = Path(path).resolve()

        if not path.exists():
            return False

        system = self.get_platform()

        try:
            if system == "Darwin":  # macOS
                subprocess.run(["open", "-R", str(path)], check=True)
            elif system == "Windows":
                subprocess.run(["explorer", "/select,", str(path)], check=True)
            else:  # Linux
                parent = path.parent if path.is_file() else path
                subprocess.run(["xdg-open", str(parent)], check=True)
            return True
        except Exception:
            return False
