"""Platform-specific system operations plugin."""

import platform
import shutil
import subprocess
from pathlib import Path

from plugins.base import Plugin


class SystemPlugin(Plugin):
    """Platform-specific system operations (dialogs, file manager)."""

    def get_platform(self) -> str:
        """Return the current platform identifier."""
        return platform.system()

    def show_folder_picker(self, initial_dir: Path | str | None = None) -> Path | None:
        """Show native folder picker dialog."""
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
        safe_dir = initial_dir if initial_dir and '"' not in initial_dir else None
        if safe_dir:
            script = (
                f'POSIX path of (choose folder with prompt "Select Download Folder" '
                f'default location POSIX file "{safe_dir}")'
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
        """Show Windows folder picker using the modern wide File Open dialog."""
        initial_path = (initial_dir or "").replace("'", "''")
        ps_script = f"""
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;

[ComImport]
[Guid("DC1C5A9C-E88A-4DDE-A5A1-60F82A20AEF7")]
[ClassInterface(ClassInterfaceType.None)]
class FileOpenDialog {{ }}

[ComImport]
[Guid("42F85136-DB7E-439C-85F1-E4075D135FC8")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IFileDialog {{
    [PreserveSig] int Show(IntPtr parent);
    [PreserveSig] int SetFileTypes(uint cFileTypes, IntPtr rgFilterSpec);
    [PreserveSig] int SetFileTypeIndex(uint iFileType);
    [PreserveSig] int GetFileTypeIndex(out uint piFileType);
    [PreserveSig] int Advise(IntPtr pfde, out uint pdwCookie);
    [PreserveSig] int Unadvise(uint dwCookie);
    [PreserveSig] int SetOptions(uint fos);
    [PreserveSig] int GetOptions(out uint pfos);
    [PreserveSig] int SetDefaultFolder(IShellItem psi);
    [PreserveSig] int SetFolder(IShellItem psi);
    [PreserveSig] int GetFolder(out IShellItem ppsi);
    [PreserveSig] int GetCurrentSelection(out IShellItem ppsi);
    [PreserveSig] int SetFileName([MarshalAs(UnmanagedType.LPWStr)] string pszName);
    [PreserveSig] int GetFileName(out IntPtr pszName);
    [PreserveSig] int SetTitle([MarshalAs(UnmanagedType.LPWStr)] string pszTitle);
    [PreserveSig] int SetOkButtonLabel([MarshalAs(UnmanagedType.LPWStr)] string pszText);
    [PreserveSig] int SetFileNameLabel([MarshalAs(UnmanagedType.LPWStr)] string pszLabel);
    [PreserveSig] int GetResult(out IShellItem ppsi);
    [PreserveSig] int AddPlace(IShellItem psi, uint fdap);
    [PreserveSig] int SetDefaultExtension([MarshalAs(UnmanagedType.LPWStr)] string pszDefaultExtension);
    [PreserveSig] int Close(int hr);
    [PreserveSig] int SetClientGuid(ref Guid guid);
    [PreserveSig] int ClearClientData();
    [PreserveSig] int SetFilter(IntPtr pFilter);
}}

[ComImport]
[Guid("43826D1E-E718-42EE-BC55-A1E261C37BFE")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IShellItem {{
    [PreserveSig] int BindToHandler(IntPtr pbc, ref Guid bhid, ref Guid riid, out IntPtr ppv);
    [PreserveSig] int GetParent(out IShellItem ppsi);
    [PreserveSig] int GetDisplayName(SIGDN sigdnName, out IntPtr ppszName);
    [PreserveSig] int GetAttributes(uint sfgaoMask, out uint psfgaoAttribs);
    [PreserveSig] int Compare(IShellItem psi, uint hint, out int piOrder);
}}

enum SIGDN : uint {{
    FILESYSPATH = 0x80058000
}}

static class NativeMethods {{
    [DllImport("shell32.dll", CharSet = CharSet.Unicode, PreserveSig = true)]
    public static extern int SHCreateItemFromParsingName(string pszPath, IntPtr pbc, ref Guid riid, out IShellItem ppv);
}}

public static class FolderPicker {{
    const uint FOS_PICKFOLDERS = 0x00000020;
    const uint FOS_FORCEFILESYSTEM = 0x00000040;
    const uint FOS_PATHMUSTEXIST = 0x00000800;
    const uint FOS_DONTADDTORECENT = 0x02000000;

    public static string PickFolder(string initialPath, string title) {{
        IFileDialog dialog = (IFileDialog)new FileOpenDialog();
        dialog.SetOptions(FOS_PICKFOLDERS | FOS_FORCEFILESYSTEM | FOS_PATHMUSTEXIST | FOS_DONTADDTORECENT);
        dialog.SetTitle(title);

        if (!string.IsNullOrWhiteSpace(initialPath)) {{
            Guid shellItemGuid = new Guid("43826D1E-E718-42EE-BC55-A1E261C37BFE");
            IShellItem folderItem;
            if (NativeMethods.SHCreateItemFromParsingName(initialPath, IntPtr.Zero, ref shellItemGuid, out folderItem) == 0 && folderItem != null) {{
                dialog.SetFolder(folderItem);
            }}
        }}

        if (dialog.Show(IntPtr.Zero) != 0) {{
            return null;
        }}

        IShellItem resultItem;
        if (dialog.GetResult(out resultItem) != 0 || resultItem == null) {{
            return null;
        }}

        IntPtr pathPtr = IntPtr.Zero;
        try {{
            if (resultItem.GetDisplayName(SIGDN.FILESYSPATH, out pathPtr) != 0 || pathPtr == IntPtr.Zero) {{
                return null;
            }}

            return Marshal.PtrToStringUni(pathPtr);
        }} finally {{
            if (pathPtr != IntPtr.Zero) {{
                Marshal.FreeCoTaskMem(pathPtr);
            }}
        }}
    }}
}}
'@ -Language CSharp

$selected = [FolderPicker]::PickFolder('{initial_path}', 'Select Download Folder')
if ($selected) {{
    Write-Output $selected
}}
"""
        result = subprocess.run(
            ["powershell", "-STA", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
        return None

    def reveal_in_file_manager(self, path: Path | str) -> bool:
        """Open file manager and select the specified file."""
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
