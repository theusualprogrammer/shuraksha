# Shuraksha - Login Screen


import sys
import os
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QMessageBox, QStackedWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

from src.core.crypto import verify_value, decrypt_json


# PATHS

APP_DATA_DIR   = Path(os.environ.get('APPDATA', '')) / 'Shuraksha'
USER_DATA_FILE = APP_DATA_DIR / 'user.dat'


# SETTINGS

MAX_ATTEMPTS    = 5
LOCKOUT_SECONDS = 300


# DIMENSIONS

WIN_W = 520
WIN_H = 660


# COLOURS

C_BG       = "#060912"
C_PANEL    = "#04060E"
C_CARD     = "#080C18"
C_INPUT    = "#050810"
C_TITLEBAR = "#030508"
C_BORDER   = "#0E1830"
C_BCARD    = "#112040"
C_FOCUS    = "#38C8FF"
C_CYAN     = "#38C8FF"
C_CYAN_H   = "#60D8FF"
C_CYAN_DIM = "#0A1E30"
C_WHITE    = "#E0F4FF"
C_MID      = "#7AB8D8"
C_DIM      = "#2A4A62"
C_GHOST    = "#0E1E2E"
C_RED      = "#FF3A1A"
C_RED_BG   = "#1A0500"

BTN_PRIMARY = (
    f"QPushButton{{"
    f"  background-color:{C_CYAN};"
    f"  color:#000000;"
    f"  border:none;"
    f"  font-size:13px;"
    f"  font-weight:bold;"
    f"  font-family:'Consolas','Courier New',monospace;"
    f"  letter-spacing:1px;"
    f"}}"
    f"QPushButton:hover{{"
    f"  background-color:{C_CYAN_H};"
    f"  color:#000000;"
    f"}}"
    f"QPushButton:pressed{{"
    f"  background-color:#20A0CC;"
    f"  color:#000000;"
    f"}}"
    f"QPushButton:disabled{{"
    f"  background-color:#0A1E30;"
    f"  color:#1A3A52;"
    f"}}"
)

BTN_GHOST = (
    f"QPushButton{{"
    f"  background-color:transparent;"
    f"  color:{C_DIM};"
    f"  border:1px solid {C_BCARD};"
    f"  font-size:12px;"
    f"  font-family:'Consolas','Courier New',monospace;"
    f"  letter-spacing:1px;"
    f"}}"
    f"QPushButton:hover{{"
    f"  color:{C_CYAN};"
    f"  border:1px solid {C_CYAN};"
    f"  background-color:transparent;"
    f"}}"
    f"QPushButton:disabled{{"
    f"  color:{C_GHOST};"
    f"  border:1px solid {C_GHOST};"
    f"  background-color:transparent;"
    f"}}"
)

GLOBAL_STYLE = f"""
    QMainWindow, QWidget {{
        background-color: {C_BG};
        color: {C_WHITE};
        font-family: 'Segoe UI', Arial, sans-serif;
    }}
    QLabel {{
        background: transparent;
        color: {C_WHITE};
    }}
    QLineEdit {{
        background-color: {C_INPUT};
        border: 1px solid {C_BCARD};
        color: {C_WHITE};
        font-size: 16px;
        font-family: 'Consolas','Courier New',monospace;
        padding: 12px 18px;
        border-radius: 0px;
        letter-spacing: 4px;
    }}
    QLineEdit:focus {{
        border: 1px solid {C_FOCUS};
        border-bottom: 2px solid {C_CYAN};
    }}
    QScrollBar:vertical {{
        background: {C_BG};
        width: 5px;
        border: none;
    }}
    QScrollBar::handle:vertical {{
        background: {C_BCARD};
        border-radius: 2px;
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
"""


def mk_lbl(text, color=C_WHITE, size=13, bold=False,
           mono=False, wrap=False, align=None):
    l = QLabel(text)
    family = (
        "'Consolas','Courier New',monospace"
        if mono else "'Segoe UI',Arial,sans-serif"
    )
    weight = "font-weight:bold;" if bold else ""
    l.setStyleSheet(
        f"color:{color};font-size:{size}px;"
        f"font-family:{family};{weight}"
        f"background:transparent;"
    )
    if wrap:
        l.setWordWrap(True)
    if align:
        l.setAlignment(align)
    return l



# HINTS OVERLAY

class HintsOverlay(QWidget):

    back_requested = pyqtSignal()
    wipe_requested = pyqtSignal()

    def __init__(self, hints: list, parent=None):
        super().__init__(parent)
        self.hints    = hints
        self.revealed = 0
        self.setStyleSheet(GLOBAL_STYLE)
        self._build()

    def _build(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(52, 52, 52, 40)
        v.setSpacing(16)

        v.addWidget(mk_lbl(
            "//  FORGOT_PASSWORD", C_CYAN, 11, bold=True, mono=True
        ))
        v.addSpacing(4)

        t = QLabel("Password Hints")
        t.setStyleSheet(
            f"color:{C_WHITE};font-size:24px;font-weight:bold;"
            f"background:transparent;"
        )
        v.addWidget(t)

        ul = QFrame()
        ul.setFixedSize(48, 2)
        ul.setStyleSheet(f"background:{C_CYAN};border:none;")
        v.addWidget(ul)
        v.addSpacing(6)

        v.addWidget(mk_lbl(
            "Hints are revealed one at a time.",
            C_MID, 13, wrap=True
        ))
        v.addSpacing(16)

        self.hint_frames = []
        self.hint_labels = []

        for i in range(3):
            frame = QFrame()
            name  = f"hf{i}"
            frame.setObjectName(name)
            frame.setStyleSheet(
                f"QFrame#{name}{{"
                f"  background:{C_CARD};"
                f"  border:1px solid {C_BCARD};"
                f"  border-left:3px solid {C_BCARD};"
                f"}}"
                f"QFrame#{name} QLabel{{"
                f"  border:none;background:transparent;"
                f"}}"
            )
            fl = QHBoxLayout(frame)
            fl.setContentsMargins(20, 16, 20, 16)
            fl.setSpacing(16)

            num_lbl = mk_lbl(
                f"[ {i+1} ]", C_DIM, 13, bold=True, mono=True
            )
            num_lbl.setFixedWidth(44)
            fl.addWidget(num_lbl)

            hint_text = mk_lbl(
                "  . . . . . . . .", C_GHOST, 13, mono=True
            )
            fl.addWidget(hint_text)

            self.hint_frames.append(frame)
            self.hint_labels.append(hint_text)
            v.addWidget(frame)

        v.addSpacing(12)

        self.reveal_btn = QPushButton("[ REVEAL NEXT HINT ]")
        self.reveal_btn.setFixedHeight(46)
        self.reveal_btn.setStyleSheet(BTN_GHOST)
        self.reveal_btn.clicked.connect(self._reveal_next)
        v.addWidget(self.reveal_btn)

        self.wipe_btn = QPushButton("[ WIPE VAULT AND RESET ]")
        self.wipe_btn.setFixedHeight(46)
        self.wipe_btn.setVisible(False)
        self.wipe_btn.setStyleSheet(
            f"QPushButton{{"
            f"  background-color:{C_RED_BG};"
            f"  color:{C_RED};"
            f"  border:1px solid {C_RED};"
            f"  font-size:13px;font-weight:bold;"
            f"  font-family:'Consolas','Courier New',monospace;"
            f"}}"
            f"QPushButton:hover{{"
            f"  background-color:{C_RED};color:#000000;"
            f"}}"
        )
        self.wipe_btn.clicked.connect(self._confirm_wipe)
        v.addWidget(self.wipe_btn)

        v.addStretch()

        back = QPushButton("[ BACK TO LOGIN ]")
        back.setFixedHeight(44)
        back.setStyleSheet(BTN_GHOST)
        back.clicked.connect(self.back_requested.emit)
        v.addWidget(back)

    def _reveal_next(self):
        if self.revealed >= len(self.hints):
            return
        i    = self.revealed
        text = (
            self.hints[i] if self.hints[i]
            else "(no hint entered)"
        )
        self.hint_labels[i].setText(text)
        self.hint_labels[i].setStyleSheet(
            f"color:{C_MID};font-size:13px;background:transparent;"
        )
        name = f"hf{i}"
        self.hint_frames[i].setStyleSheet(
            f"QFrame#{name}{{"
            f"  background:{C_CYAN_DIM};"
            f"  border:1px solid {C_FOCUS};"
            f"  border-left:3px solid {C_CYAN};"
            f"}}"
            f"QFrame#{name} QLabel{{"
            f"  border:none;background:transparent;"
            f"}}"
        )
        self.revealed += 1
        if self.revealed >= 3:
            self.reveal_btn.setVisible(False)
            self.wipe_btn.setVisible(True)

    def _confirm_wipe(self):
        box = QMessageBox(self)
        box.setWindowTitle("// CONFIRM VAULT WIPE")
        box.setText(
            "This will permanently delete ALL vault data.\n\n"
            "Are you absolutely sure?"
        )
        box.setStandardButtons(
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No
        )
        box.button(
            QMessageBox.StandardButton.Yes
        ).setText("WIPE EVERYTHING")
        box.button(
            QMessageBox.StandardButton.No
        ).setText("CANCEL")
        box.setStyleSheet(
            f"QMessageBox{{background:{C_BG};color:{C_WHITE};"
            f"font-family:'Consolas','Courier New',monospace;"
            f"font-size:13px;}}"
            f"QPushButton{{background:{C_RED};color:#000000;"
            f"border:none;padding:8px 20px;font-weight:bold;"
            f"font-size:12px;"
            f"font-family:'Consolas','Courier New',monospace;}}"
        )
        if box.exec() == QMessageBox.StandardButton.Yes:
            self.wipe_requested.emit()



# LOCKOUT SCREEN

class LockoutScreen(QWidget):

    unlocked = pyqtSignal()

    def __init__(self, seconds: int, parent=None):
        super().__init__(parent)
        self.remaining = seconds
        self.setStyleSheet(GLOBAL_STYLE)
        self._build()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(1000)

    def _build(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(52, 80, 52, 52)
        v.setSpacing(18)
        v.setAlignment(Qt.AlignmentFlag.AlignTop)

        v.addWidget(mk_lbl(
            "//  SECURITY_EXCEPTION  [0x00FF3A]",
            C_RED, 12, bold=True, mono=True
        ))
        v.addSpacing(8)

        title = QLabel("Access Denied")
        title.setStyleSheet(
            f"color:{C_RED};font-size:30px;font-weight:bold;"
            f"background:transparent;"
        )
        v.addWidget(title)

        ul = QFrame()
        ul.setFixedSize(52, 2)
        ul.setStyleSheet(f"background:{C_RED};border:none;")
        v.addWidget(ul)
        v.addSpacing(10)

        v.addWidget(mk_lbl(
            "Maximum login attempts exceeded.\n"
            "Vault access has been suspended.",
            C_MID, 14, wrap=True
        ))
        v.addSpacing(28)

        self.countdown_lbl = QLabel(self._fmt(self.remaining))
        self.countdown_lbl.setStyleSheet(
            f"color:{C_CYAN};font-size:52px;font-weight:bold;"
            f"font-family:'Consolas','Courier New',monospace;"
            f"background:transparent;"
        )
        self.countdown_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(self.countdown_lbl)

        v.addSpacing(10)
        v.addWidget(mk_lbl(
            "Vault will unlock when the countdown reaches zero.",
            C_DIM, 13, wrap=True,
            align=Qt.AlignmentFlag.AlignCenter
        ))
        v.addStretch()

        for line in [
            "> suspending_vault_access . . . done",
            "> logging_attempt_timestamp . . . done",
            "> incrementing_lockout_counter . . . done",
        ]:
            v.addWidget(mk_lbl(line, C_GHOST, 11, mono=True))

    def _fmt(self, s: int) -> str:
        return f"{s // 60:02d}:{s % 60:02d}"

    def _tick(self):
        self.remaining -= 1
        self.countdown_lbl.setText(self._fmt(self.remaining))
        if self.remaining <= 0:
            self.timer.stop()
            self.unlocked.emit()



# LOGIN WINDOW

class LoginWindow(QMainWindow):
    """
    Login screen shown on every app launch.

    user.dat structure expected:
    {
        "password_hash": "...",   <- verified directly (no decryption)
        "password_salt": "...",   <- verified directly (no decryption)
        "encrypted": {...}        <- decrypted only after correct password
    }

    Signal login_success(dict, str) carries:
        dict - the decrypted inner data
        str  - the plain master password for the vault manager
    """

    login_success = pyqtSignal(dict, str)

    def __init__(self):
        super().__init__()

        self.raw_data      = self._load_raw()
        self.attempts_left = MAX_ATTEMPTS
        self.locked_out    = False

        self.setWindowTitle('Shuraksha')
        self.setFixedSize(WIN_W, WIN_H)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self._drag_pos = None
        self.setStyleSheet(GLOBAL_STYLE)
        self._build()

    def _load_raw(self) -> dict:
        """
        Load the full JSON from user.dat.
        Expected keys: password_hash, password_salt, encrypted.
        Returns empty dict if file missing or unreadable.
        """
        if not USER_DATA_FILE.exists():
            return {}
        try:
            with open(USER_DATA_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}

    def _build(self):
        root = QWidget()
        self.setCentralWidget(root)

        v = QVBoxLayout(root)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        v.addWidget(self._build_titlebar())

        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background:{C_BORDER};border:none;")
        v.addWidget(div)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_login_form())   # 0
        self.stack.addWidget(self._build_hints_view())   # 1

        lockout = LockoutScreen(LOCKOUT_SECONDS)
        lockout.unlocked.connect(self._on_unlock)
        self.stack.addWidget(lockout)                    # 2

        v.addWidget(self.stack)

    def _build_titlebar(self):
        bar = QWidget()
        bar.setFixedHeight(38)
        bar.setStyleSheet(f"background:{C_TITLEBAR};")

        h = QHBoxLayout(bar)
        h.setContentsMargins(20, 0, 20, 0)
        h.addWidget(mk_lbl(
            "[  SHR  ]", C_CYAN, 11, bold=True, mono=True
        ))
        h.addWidget(mk_lbl("  //  ", C_GHOST, 11, mono=True))
        h.addWidget(mk_lbl("SECURITY VAULT", C_DIM, 11, mono=True))
        h.addStretch()

        close = QPushButton("[ EXIT ]")
        close.setStyleSheet(
            f"QPushButton{{background:transparent;color:{C_DIM};"
            f"border:none;font-size:11px;"
            f"font-family:'Consolas','Courier New',monospace;}}"
            f"QPushButton:hover{{color:{C_RED};}}"
        )
        close.clicked.connect(QApplication.quit)
        h.addWidget(close)
        return bar

    def _build_login_form(self):
        widget = QWidget()
        v      = QVBoxLayout(widget)
        v.setContentsMargins(52, 56, 52, 44)
        v.setSpacing(0)

        brand = QLabel("SHURAKSHA")
        brand.setStyleSheet(
            f"color:{C_WHITE};font-size:22px;font-weight:bold;"
            f"letter-spacing:5px;background:transparent;"
        )
        v.addWidget(brand)
        v.addSpacing(4)
        v.addWidget(mk_lbl(
            "> security_vault.exe", C_DIM, 11, mono=True
        ))
        v.addSpacing(28)

        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background:{C_BORDER};border:none;")
        v.addWidget(div)
        v.addSpacing(32)

        v.addWidget(mk_lbl(
            "//  ACCESS_REQUIRED", C_CYAN, 11, bold=True, mono=True
        ))
        v.addSpacing(8)

        title = QLabel("Enter Master Password")
        title.setStyleSheet(
            f"color:{C_WHITE};font-size:22px;font-weight:bold;"
            f"background:transparent;"
        )
        v.addWidget(title)

        ul = QFrame()
        ul.setFixedSize(48, 2)
        ul.setStyleSheet(f"background:{C_CYAN};border:none;")
        v.addWidget(ul)
        v.addSpacing(10)

        v.addWidget(mk_lbl(
            "Type your master password to unlock the vault.",
            C_MID, 13
        ))
        v.addSpacing(36)

        v.addWidget(mk_lbl(
            "// MASTER PASSWORD", C_MID, 12, mono=True
        ))
        v.addSpacing(8)

        self.pwd_input = QLineEdit()
        self.pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pwd_input.setPlaceholderText("enter_password")
        self.pwd_input.setFixedHeight(56)
        self.pwd_input.returnPressed.connect(self._attempt_login)
        v.addWidget(self.pwd_input)
        v.addSpacing(14)

        self.error_lbl = mk_lbl("", C_RED, 12, mono=True)
        self.error_lbl.setFixedHeight(20)
        v.addWidget(self.error_lbl)
        v.addSpacing(16)

        self.login_btn = QPushButton("UNLOCK VAULT  >>")
        self.login_btn.setFixedHeight(54)
        self.login_btn.setStyleSheet(BTN_PRIMARY)
        self.login_btn.clicked.connect(self._attempt_login)
        v.addWidget(self.login_btn)
        v.addSpacing(22)

        dots_row = QHBoxLayout()
        dots_row.setSpacing(8)
        dots_row.addWidget(
            mk_lbl("// ATTEMPTS:", C_DIM, 11, mono=True)
        )

        self.attempt_dots = []
        for _ in range(MAX_ATTEMPTS):
            dot = QLabel("●")
            dot.setStyleSheet(
                f"color:{C_CYAN};font-size:16px;"
                f"background:transparent;"
            )
            self.attempt_dots.append(dot)
            dots_row.addWidget(dot)

        dots_row.addStretch()
        v.addLayout(dots_row)
        v.addSpacing(24)

        div2 = QFrame()
        div2.setFixedHeight(1)
        div2.setStyleSheet(f"background:{C_BORDER};border:none;")
        v.addWidget(div2)
        v.addSpacing(18)

        forgot = QPushButton("Forgot password?  Show hints  >>")
        forgot.setStyleSheet(
            f"QPushButton{{background:transparent;color:{C_DIM};"
            f"border:none;font-size:12px;"
            f"font-family:'Consolas','Courier New',monospace;}}"
            f"QPushButton:hover{{color:{C_CYAN};}}"
        )
        forgot.clicked.connect(self._show_hints)
        v.addWidget(forgot)

        v.addStretch()
        return widget

    def _build_hints_view(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.hints_overlay = HintsOverlay(['', '', ''])
        self.hints_overlay.back_requested.connect(self._show_login)
        self.hints_overlay.wipe_requested.connect(self._wipe_vault)

        layout.addWidget(self.hints_overlay)
        return widget


# LOGIN LOGIC


    def _attempt_login(self):
        """
        Login flow:

        Step 1: Read password_hash and password_salt directly
                from the outer JSON structure. These are NOT
                encrypted so we can read them without the password.

        Step 2: Verify the entered password against that hash
                using verify_value from crypto.py.

        Step 3: If correct, decrypt the inner 'encrypted' blob
                using the verified password.

        Step 4: Merge dob_hash and dob_salt from inner data,
                then emit login_success(inner_data, password).

        Step 5: If wrong, decrement attempts and update UI.
        """
        if self.locked_out:
            return

        password = self.pwd_input.text()

        if not password:
            self.error_lbl.setText(
                "// ERROR: password field is empty."
            )
            return

        if not self.raw_data:
            self.error_lbl.setText(
                "// ERROR: no registration data found. "
                "Run the installer."
            )
            return

        # Step 1: read hash and salt from outer structure
        pwd_hash = self.raw_data.get('password_hash', '')
        pwd_salt = self.raw_data.get('password_salt', '')

        if not pwd_hash or not pwd_salt:
            self.error_lbl.setText(
                "// ERROR: registration data corrupted. "
                "Delete AppData/Shuraksha and run installer again."
            )
            return

        # Step 2: verify password
        try:
            correct = verify_value(password, pwd_hash, pwd_salt)
        except Exception as e:
            self.error_lbl.setText(
                f"// ERROR: verification failed: {str(e)}"
            )
            return

        if correct:
            # Step 3: decrypt the inner blob
            encrypted_blob = self.raw_data.get('encrypted', {})
            if not encrypted_blob:
                self.error_lbl.setText(
                    "// ERROR: encrypted data missing. "
                    "Run installer again."
                )
                return

            try:
                inner = decrypt_json(encrypted_blob, password)
            except Exception as e:
                self.error_lbl.setText(
                    f"// ERROR: decryption failed: {str(e)}"
                )
                return

            # Step 4: clear input and emit success
            self.pwd_input.clear()
            self.login_success.emit(inner, password)

        else:
            # Step 5: wrong password
            self.attempts_left -= 1
            self.pwd_input.clear()

            used = MAX_ATTEMPTS - self.attempts_left
            for i, dot in enumerate(self.attempt_dots):
                dot.setStyleSheet(
                    f"color:"
                    f"{'#FF3A1A' if i < used else C_CYAN};"
                    f"font-size:16px;background:transparent;"
                )

            if self.attempts_left <= 0:
                self.locked_out = True
                self.stack.setCurrentIndex(2)
            else:
                self.error_lbl.setText(
                    f"// ERROR: incorrect password.  "
                    f"[ {self.attempts_left} "
                    f"attempt"
                    f"{'s' if self.attempts_left != 1 else ''} "
                    f"remaining ]"
                )

    def _show_hints(self):
        self.stack.setCurrentIndex(1)

    def _show_login(self):
        self.stack.setCurrentIndex(0)
        self.error_lbl.setText("")

    def _on_unlock(self):
        self.locked_out    = False
        self.attempts_left = MAX_ATTEMPTS
        self.error_lbl.setText("")
        for dot in self.attempt_dots:
            dot.setStyleSheet(
                f"color:{C_CYAN};font-size:16px;"
                f"background:transparent;"
            )
        self.stack.setCurrentIndex(0)

    def _wipe_vault(self):
        import shutil
        try:
            if APP_DATA_DIR.exists():
                shutil.rmtree(APP_DATA_DIR)
            QMessageBox.information(
                self, "// VAULT WIPED",
                "All data permanently deleted.\n\n"
                "Run the installer again."
            )
            QApplication.quit()
        except Exception as e:
            QMessageBox.critical(
                self, "// WIPE FAILED",
                f"Could not delete data.\n\nError: {str(e)}"
            )


# WINDOW DRAG


    def mousePressEvent(self, event):
        if event.position().y() < 40:
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None:
            self.move(
                self.pos() +
                event.globalPosition().toPoint() - self._drag_pos
            )
            self._drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())
