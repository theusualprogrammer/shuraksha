# Shuraksha - Security Hardening Module



import os
import ctypes
import ctypes.wintypes
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Callable

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

#UNKNOWN THREAT SIGNATURES

KEYLOGGER_SIGNATURES = [
    'keylogger', 'klw', 'klog', 'revealer',
    'spyrix', 'refog', 'ardamax', 'blackbox',
    'allspy', 'spytector', 'perfect keylogger',
]

SCREEN_RECORDER_SIGNATURES = [
    'obs.exe', 'obs64.exe', 'bandicam.exe',
    'camtasia.exe', 'fraps.exe', 'sharex.exe',
    'screenrec.exe', 'captura.exe', 'xsplit.exe',
    'action.exe', 'gamebar.exe',
]


# WINDOWS CONSTRAINTS 

WH_KEYBOARD_LL = 13
WM_KEYDOWN     = 0x0100
VK_SNAPSHOT    = 0x2C


class SecurityManager:
    """
    Central security manager for Shuraksha.

    Call start() when the real vault opens.
    Call stop() when the vault locks.
    set_lock_callback() registers the function
    that locks the vault on threat detection.
    """

    def __init__(self):
        self._lock_callback: Callable = None
        self._active                  = False
        self._scan_thread             = None
        self._kb_hook                 = None
        self._kb_hook_id              = None

    def set_lock_callback(self, callback: Callable):
        """Register the vault lock function."""
        self._lock_callback = callback

    def start(self):
        """
        Start all security monitoring.
        Called when the real vault dashboard opens.
        """
        self._active = True

        # Start background process scanner
        self._scan_thread = threading.Thread(
            target=self._scan_loop,
            daemon=True
        )
        self._scan_thread.start()

        # Block Print Screen key
        self._install_kb_hook()

    def stop(self):
        """
        Stop all security monitoring.
        Called when the vault locks.
        """
        self._active = False
        self._remove_kb_hook()

    # -----------------------------------------------
    # SCREENSHOT BLOCKING
    # -----------------------------------------------

    def _install_kb_hook(self):
        """
        Install a low-level keyboard hook that intercepts
        the Print Screen key and blocks it from capturing
        the screen while the vault is open.
        """
        try:
            HOOKPROC = ctypes.WINFUNCTYPE(
                ctypes.c_int,
                ctypes.c_int,
                ctypes.wintypes.WPARAM,
                ctypes.wintypes.LPARAM
            )

            def kb_callback(nCode, wParam, lParam):
                if nCode >= 0 and wParam == WM_KEYDOWN:
                    vk_code = ctypes.cast(
                        lParam,
                        ctypes.POINTER(ctypes.c_ulong)
                    )[0]
                    # Block Print Screen key
                    if vk_code == VK_SNAPSHOT:
                        return 1
                return ctypes.windll.user32.CallNextHookEx(
                    self._kb_hook_id, nCode, wParam, lParam
                )

            self._kb_hook = HOOKPROC(kb_callback)
            self._kb_hook_id = (
                ctypes.windll.user32.SetWindowsHookExW(
                    WH_KEYBOARD_LL,
                    self._kb_hook,
                    ctypes.windll.kernel32.GetModuleHandleW(None),
                    0
                )
            )
        except Exception:
            pass

    def _remove_kb_hook(self):
        """Remove the keyboard hook on vault lock."""
        try:
            if self._kb_hook_id:
                ctypes.windll.user32.UnhookWindowsHookEx(
                    self._kb_hook_id
                )
                self._kb_hook_id = None
                self._kb_hook    = None
        except Exception:
            pass

    def block_screenshot_api(self, hwnd: int):
        """
        Block the Windows screenshot API for a window.
        SetWindowDisplayAffinity makes the window appear
        black in any screenshot or screen recording tool.

        hwnd: Windows window handle from winId()
        """
        try:
            # WDA_EXCLUDEFROMCAPTURE = 0x00000011
            ctypes.windll.user32.SetWindowDisplayAffinity(
                hwnd, 0x00000011
            )
        except Exception:
            pass

    def unblock_screenshot_api(self, hwnd: int):
        """Re-enable normal window capture on vault lock."""
        try:
            # WDA_NONE = 0x00000000
            ctypes.windll.user32.SetWindowDisplayAffinity(
                hwnd, 0x00000000
            )
        except Exception:
            pass


# ANTI-DEBUG


    def is_debugger_attached(self) -> bool:
        """
        Check if a debugger is attached to this process.
        Attackers use debuggers to extract encryption
        keys and passwords from running processes.
        """
        try:
            if ctypes.windll.kernel32.IsDebuggerPresent():
                return True

            is_remote = ctypes.c_bool(False)
            ctypes.windll.kernel32.CheckRemoteDebuggerPresent(
                ctypes.windll.kernel32.GetCurrentProcess(),
                ctypes.byref(is_remote)
            )
            if is_remote.value:
                return True

        except Exception:
            pass

        return False

 # PROCESS SCANNER


    def _scan_loop(self):
        """
        Background thread that scans running processes
        every 5 seconds while the vault is open.
        Checks for keyloggers, screen recorders,
        and attached debuggers.
        """
        while self._active:
            try:
                if self.is_debugger_attached():
                    self._threat_detected("Debugger attached")
                    break

                if PSUTIL_AVAILABLE:
                    for proc in psutil.process_iter(['name']):
                        try:
                            name = (
                                proc.info['name'] or ''
                            ).lower()

                            for sig in KEYLOGGER_SIGNATURES:
                                if sig in name:
                                    self._threat_detected(
                                        f"Keylogger: {name}"
                                    )
                                    break

                            for sig in SCREEN_RECORDER_SIGNATURES:
                                if sig == name:
                                    self._threat_detected(
                                        f"Screen recorder: {name}"
                                    )
                                    break

                        except (
                            psutil.NoSuchProcess,
                            psutil.AccessDenied
                        ):
                            continue

            except Exception:
                pass

            time.sleep(5)

    def _threat_detected(self, reason: str):
        """
        Called when a security threat is detected.
        Writes to the log file directly (no imports
        from other Shuraksha modules to avoid circular
        import errors) and triggers the lock callback.
        """
        # Write to log directly without importing vault_dashboard
        try:
            log_file = (
                Path(os.environ.get('APPDATA', '')) /
                'Shuraksha' / 'vault' / 'access.log'
            )
            log_file.parent.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(
                    f"[{ts}]  SECURITY_THREAT  {reason}\n"
                )
        except Exception:
            pass

        # Trigger vault lock
        if self._lock_callback:
            try:
                self._lock_callback()
            except Exception:
                pass

    # -----------------------------------------------
    # CLIPBOARD CLEAR
    # -----------------------------------------------

    def schedule_clipboard_clear(self, delay_seconds: int = 30):
        """
        Clear the clipboard after a delay.
        Called whenever a password is copied to clipboard.
        Prevents passwords from sitting in the clipboard.
        """
        def clear():
            time.sleep(delay_seconds)
            try:
                import win32clipboard
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.CloseClipboard()
            except Exception:
                try:
                    # Fallback using PyQt6
                    from PyQt6.QtWidgets import QApplication
                    QApplication.clipboard().setText("")
                except Exception:
                    pass

        threading.Thread(target=clear, daemon=True).start()

    # -----------------------------------------------
    # PROCESS NAME
    # -----------------------------------------------

    def hide_process_name(self):
        """
        Change the console title to a neutral name
        so the process is less conspicuous in Task Manager.
        """
        try:
            ctypes.windll.kernel32.SetConsoleTitleW(
                "System Host Process"
            )
        except Exception:
            pass

security = SecurityManager()