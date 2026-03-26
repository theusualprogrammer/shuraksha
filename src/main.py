# Shuraksha - Main Application Entry Point


import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from src.ui.login            import LoginWindow
from src.ui.fake_dashboard   import FakeDashboard
from src.ui.bodmas           import BodmasScreen
from src.ui.vault_dashboard  import VaultDashboard
from src.ui.fake_vault2      import FakeVault2
from src.installer.registration import RegistrationWizard


# PATHS

APP_DATA_DIR   = Path(os.environ.get('APPDATA', '')) / 'Shuraksha'
USER_DATA_FILE = APP_DATA_DIR / 'user.dat'


def is_registered() -> bool:
    """
    Return True if the user has completed registration.
    Checks that user.dat exists and is not empty.
    """
    return (
        USER_DATA_FILE.exists() and
        USER_DATA_FILE.stat().st_size > 0
    )



# APPLICATION CONTROLLER

class ShurakshaApp:
    """
    Central controller managing every screen transition.
    Only one window is visible at any time.

    Screen flow:
        Registration (first time only)
            |
            v
        Login screen
            |
        Correct master password
            |
            v
        Fake Dashboard (light mode decoy file manager)
            |
        Theme toggle -> dark mode
            |
            v
        BODMAS screen
            |
            +-- Correct DOB      -> Real Vault
            +-- Correct math     -> Second Fake Vault
            +-- Wrong answer     -> Error / Lockout
            +-- Back to light    -> Fake Dashboard
    """

    def __init__(self, app: QApplication):
        self.app              = app

        # All window references
        # Keeping them all here ensures _hide_all
        # can clean up every single one
        self.reg_window       = None
        self.login_window     = None
        self.fake_dashboard   = None
        self.bodmas_screen    = None
        self.vault_dashboard  = None
        self.fake_vault2      = None   # Second fake vault

        # Decrypted user data from the login step
        self.user_data        = {}

        # Master password held in memory only long enough
        # to open the vault. Cleared after vault is locked.
        self._master_password = ''

    def start(self):
        """
        Decide the first screen based on registration state.
        """
        if not is_registered():
            self._show_registration()
        else:
            self._show_login()


# REGISTRATION


    def _show_registration(self):
        """
        Show the one-time registration wizard.
        After it completes the app moves to the login screen.
        """
        self._hide_all()
        self.reg_window = RegistrationWizard()
        self.reg_window.show()

        self.app.aboutToQuit.connect(
            self._check_after_registration
        )

    def _check_after_registration(self):
        """
        Called when the registration wizard finishes.
        If registration succeeded show the login screen.
        """
        if is_registered():
            try:
                self.app.aboutToQuit.disconnect(
                    self._check_after_registration
                )
            except Exception:
                pass
            self._show_login()


# LOGIN


    def _show_login(self):
        """Show the master password login screen."""
        self._hide_all()

        self.login_window = LoginWindow()
        self.login_window.login_success.connect(
            self._on_login_success
        )
        self.login_window.show()

    def _on_login_success(self, decrypted_data: dict,
                          password: str):
        """
        Called when the correct master password is entered.
        Receives the decrypted user data and master password
        directly through the signal so neither is ever lost.
        """
        self.user_data        = decrypted_data
        self._master_password = password

        if not self._master_password:
            self._show_login()
            return

        self._show_fake_dashboard()


# FAKE DASHBOARD (decoy layer one)


    def _show_fake_dashboard(self):
        """
        Show the fake light mode file manager.
        This is the first decoy layer.
        The theme toggle on this screen is the hidden trigger.
        """
        self._hide_all()

        username = self.user_data.get('username', 'User')
        self.fake_dashboard = FakeDashboard(username=username)
        self.fake_dashboard.dark_mode_triggered.connect(
            self._show_bodmas
        )
        self.fake_dashboard.logout_requested.connect(
            self._show_login
        )
        self.fake_dashboard.show()


    # BODMAS SCREEN


    def _show_bodmas(self):
        """
        Show the fake BODMAS maths challenge.
        Triggered when the theme toggle is set to dark.

        Three outcomes:
            Correct DOB    -> real vault
            Correct math   -> second fake vault
            Wrong answer   -> error and lockout
        """
        self._hide_all()

        dob_hash = self.user_data.get('dob_hash', '')
        dob_salt = self.user_data.get('dob_salt', '')

        if not dob_hash or not dob_salt:
            self._show_login()
            return

        self.bodmas_screen = BodmasScreen(
            dob_hash=dob_hash,
            dob_salt=dob_salt
        )

        # Correct DOB typed -> open real vault
        self.bodmas_screen.vault_access_granted.connect(
            self._show_vault
        )

        # Correct math answer typed -> open second fake vault
        self.bodmas_screen.fake_vault_access.connect(
            self._show_fake_vault2
        )

        # Back button -> return to fake dashboard
        self.bodmas_screen.back_to_light.connect(
            self._show_fake_dashboard
        )

        self.bodmas_screen.show()


# REAL VAULT


    def _show_vault(self):
        """
        Show the real encrypted vault dashboard.
        Only reachable after the correct DOB is entered
        on the BODMAS screen.
        """
        self._hide_all()

        self.vault_dashboard = VaultDashboard(
            user_data=self.user_data,
            master_password=self._master_password
        )
        self.vault_dashboard.lock_requested.connect(
            self._on_vault_locked
        )
        self.vault_dashboard.show()

    def _on_vault_locked(self):
        """
        Called when the real vault is locked.
        Clears all sensitive data and returns to login.
        """
        self._master_password = ''
        self.user_data        = {}
        self._show_login()


# SECOND FAKE VAULT (decoy layer two)


    def _show_fake_vault2(self):
        """
        Show the second fake vault.
        Triggered when someone correctly solves the
        BODMAS math question instead of typing the DOB.

        This vault looks completely real but contains
        only fabricated file entries and no actual data.
        Anyone who correctly solves the math ends up
        here instead of the real vault.
        """
        self._hide_all()

        username = self.user_data.get('username', 'User')
        self.fake_vault2 = FakeVault2(username=username)
        self.fake_vault2.lock_requested.connect(
            self._on_fake_vault2_locked
        )
        self.fake_vault2.show()

    def _on_fake_vault2_locked(self):
        """
        Called when the second fake vault is locked.
        Returns to login screen.
        Does NOT clear master password or user data
        in case the real user locks and wants to re-enter.
        """
        self._show_login()


# UTILITIES


    def _hide_all(self):
        """
        Hide and destroy every open window.
        Ensures only one window is active at a time.
        All six possible windows are handled here.
        """
        for window in [
            self.reg_window,
            self.login_window,
            self.fake_dashboard,
            self.bodmas_screen,
            self.vault_dashboard,
            self.fake_vault2,       # Second fake vault
        ]:
            if window is not None:
                try:
                    window.hide()
                    window.deleteLater()
                except Exception:
                    pass

        self.reg_window      = None
        self.login_window    = None
        self.fake_dashboard  = None
        self.bodmas_screen   = None
        self.vault_dashboard = None
        self.fake_vault2     = None



# ENTRY POINT

def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setApplicationName("Shuraksha")
    app.setApplicationVersion("1.0.0")

    icon_path = (
        Path(__file__).parent.parent /
        'assets' / 'icons' / 'icon.ico'
    )
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Handle command line flags from the installer
    args = sys.argv[1:]

    if '--wipe' in args:
        # Called by the uninstaller to clean vault data
        import shutil
        vault_path = (
            Path(os.environ.get('APPDATA', '')) / 'Shuraksha'
        )
        if vault_path.exists():
            shutil.rmtree(vault_path)
        sys.exit(0)

    if '--register' in args:
        # Called by the installer after installation
        # Force show the registration wizard
        app2 = QApplication.instance() or QApplication(sys.argv)
        wizard = RegistrationWizard()
        wizard.show()
        sys.exit(app.exec())

    # Normal launch
    controller = ShurakshaApp(app)
    controller.start()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
