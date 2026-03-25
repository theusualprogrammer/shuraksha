# -----------------------------------------------
# Shuraksha - Registration Wizard
# File: src/installer/registration.py
# -----------------------------------------------

import sys
import os
import json
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QStackedWidget, QProgressBar, QFrame, QMessageBox,
    QScrollArea
)
from PyQt6.QtCore import Qt

from src.core.crypto import hash_value, encrypt_json

# -----------------------------------------------
# STORAGE PATHS
# -----------------------------------------------
APP_DATA_DIR   = Path(os.environ.get('APPDATA', '')) / 'Shuraksha'
USER_DATA_FILE = APP_DATA_DIR / 'user.dat'
VAULT_DIR      = APP_DATA_DIR / 'vault'

# -----------------------------------------------
# WINDOW DIMENSIONS
# -----------------------------------------------
WIN_W       = 1024
WIN_H       = 720
PROGRESS_H  = 3
TITLEBAR_H  = 42
DIV_H       = 1
NAVBAR_H    = 72
SIDEBAR_W   = 240
CONTENT_H   = WIN_H - PROGRESS_H - TITLEBAR_H - DIV_H - NAVBAR_H - DIV_H

# -----------------------------------------------
# COLOURS
# -----------------------------------------------
C_BG        = "#060912"
C_SIDEBAR   = "#04060E"
C_CARD      = "#080C18"
C_INPUT     = "#050810"
C_TITLEBAR  = "#030508"
C_NAVBAR    = "#04060E"
C_STEP_ACT  = "#091828"
C_BORDER    = "#0E1830"
C_BCARD     = "#112040"
C_FOCUS     = "#38C8FF"
C_CYAN      = "#38C8FF"
C_CYAN_H    = "#60D8FF"
C_CYAN_DIM  = "#0A1E30"
C_WHITE     = "#E0F4FF"
C_MID       = "#7AB8D8"
C_DIM       = "#2A4A62"
C_GHOST     = "#0E1E2E"
C_RED       = "#FF3A1A"
C_RED_BG    = "#1A0500"

# -----------------------------------------------
# BUTTON STYLES
# -----------------------------------------------
STYLE_CONTINUE = (
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
)

STYLE_BACK = (
    f"QPushButton{{"
    f"  background-color:transparent;"
    f"  color:{C_DIM};"
    f"  border:1px solid {C_BCARD};"
    f"  font-size:13px;"
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

STYLE_GLOBAL = f"""
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
        font-size: 14px;
        font-family: 'Consolas','Courier New',monospace;
        padding: 10px 18px;
        border-radius: 0px;
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


class RegistrationWizard(QMainWindow):
    """
    Nine-page registration wizard for Shuraksha.

    Data structure saved to user.dat:
    {{
        "password_hash": "...",   <- stored OUTSIDE encrypted blob
        "password_salt": "...",   <- stored OUTSIDE encrypted blob
        "encrypted": {{           <- AES-256-GCM encrypted blob
            "ciphertext": "...",
            "nonce": "...",
            "salt": "..."
        }}
    }}

    The encrypted blob contains:
    {{
        "username": "...",
        "hints": [...],
        "dob_hash": "...",
        "dob_salt": "...",
        "setup_complete": true
    }}

    password_hash and password_salt are outside the encrypted
    blob so the login screen can verify the password WITHOUT
    needing to decrypt anything first. Decryption only happens
    after the password has been verified as correct.
    """

    def __init__(self):
        super().__init__()

        self.user_data = {
            'username'     : '',
            'password_hash': '',
            'password_salt': '',
            'hints'        : [],
            'dob_hash'     : '',
            'dob_salt'     : '',
        }
        self._plain_password = ''
        self.current_page    = 0

        self.setWindowTitle('Shuraksha // Setup')
        self.setFixedSize(WIN_W, WIN_H)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self._drag_pos = None
        self.setStyleSheet(STYLE_GLOBAL)
        self._build_layout()

    # -----------------------------------------------
    # HELPERS
    # -----------------------------------------------

    def _hline(self):
        f = QFrame()
        f.setFixedHeight(1)
        f.setStyleSheet(f"background:{C_BORDER};border:none;")
        return f

    def _vline(self):
        f = QFrame()
        f.setFixedWidth(1)
        f.setStyleSheet(f"background:{C_BORDER};border:none;")
        return f

    def _lbl(self, text, color=C_WHITE, size=13,
             bold=False, mono=False, wrap=False, spacing=0):
        l = QLabel(text)
        family = (
            "'Consolas','Courier New',monospace"
            if mono else "'Segoe UI',Arial,sans-serif"
        )
        weight = "font-weight:bold;" if bold else ""
        ls = f"letter-spacing:{spacing}px;" if spacing else ""
        l.setStyleSheet(
            f"color:{color};font-size:{size}px;"
            f"font-family:{family};{weight}{ls}"
            f"background:transparent;"
        )
        if wrap:
            l.setWordWrap(True)
        return l

    def _active_step_style(self):
        return (
            f"color:{C_CYAN};font-size:12px;font-weight:bold;"
            f"font-family:'Consolas','Courier New',monospace;"
            f"letter-spacing:1px;"
            f"background:{C_STEP_ACT};"
            f"border-left:3px solid {C_CYAN};"
            f"padding-left:25px;"
        )

    def _inactive_step_style(self):
        return (
            f"color:{C_GHOST};font-size:12px;"
            f"font-family:'Consolas','Courier New',monospace;"
            f"padding-left:28px;"
        )

    def _done_step_style(self):
        return (
            f"color:{C_DIM};font-size:12px;"
            f"font-family:'Consolas','Courier New',monospace;"
            f"padding-left:28px;"
        )

    # -----------------------------------------------
    # LAYOUT
    # -----------------------------------------------

    def _build_layout(self):
        root = QWidget()
        self.setCentralWidget(root)

        v = QVBoxLayout(root)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(8)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(PROGRESS_H)
        self.progress_bar.setStyleSheet(
            f"QProgressBar{{background:{C_TITLEBAR};border:none;}}"
            f"QProgressBar::chunk{{background:{C_CYAN};}}"
        )
        v.addWidget(self.progress_bar)

        v.addWidget(self._build_title_bar())
        v.addWidget(self._hline())

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(0)
        content_row.addWidget(self._build_sidebar())
        content_row.addWidget(self._vline())
        content_row.addWidget(self._build_pages_area())

        content_widget = QWidget()
        content_widget.setFixedHeight(CONTENT_H)
        content_widget.setLayout(content_row)
        v.addWidget(content_widget)

        v.addWidget(self._hline())
        v.addWidget(self._build_nav_bar())

    def _build_title_bar(self):
        bar = QWidget()
        bar.setFixedHeight(TITLEBAR_H)
        bar.setStyleSheet(f"background:{C_TITLEBAR};")

        h = QHBoxLayout(bar)
        h.setContentsMargins(24, 0, 24, 0)

        h.addWidget(self._lbl(
            "[  SHR  ]", C_CYAN, 12, bold=True, mono=True, spacing=2
        ))
        h.addWidget(self._lbl("  //  ", C_GHOST, 12, mono=True))
        h.addWidget(self._lbl(
            "SETUP AND REGISTRATION", C_DIM, 12, mono=True, spacing=2
        ))
        h.addStretch()

        self.title_counter = self._lbl("01 / 09", C_DIM, 12, mono=True)
        h.addWidget(self.title_counter)
        h.addSpacing(24)

        cancel_btn = QPushButton("[ CANCEL ]")
        cancel_btn.setStyleSheet(
            f"QPushButton{{background:transparent;color:{C_DIM};"
            f"border:none;font-size:12px;"
            f"font-family:'Consolas','Courier New',monospace;}}"
            f"QPushButton:hover{{color:{C_RED};}}"
        )
        cancel_btn.clicked.connect(self._on_cancel)
        h.addWidget(cancel_btn)

        return bar

    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setFixedWidth(SIDEBAR_W)
        sidebar.setStyleSheet(f"background:{C_SIDEBAR};")

        v = QVBoxLayout(sidebar)
        v.setContentsMargins(0, 36, 0, 24)
        v.setSpacing(0)

        b = QVBoxLayout()
        b.setContentsMargins(28, 0, 28, 0)
        b.setSpacing(4)

        brand = QLabel("SHURAKSHA")
        brand.setStyleSheet(
            f"color:{C_WHITE};font-size:16px;font-weight:bold;"
            f"letter-spacing:4px;background:transparent;"
        )
        b.addWidget(brand)
        b.addWidget(self._lbl(
            "> security_vault.exe", C_DIM, 11, mono=True
        ))
        v.addLayout(b)
        v.addSpacing(28)

        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(
            f"background:{C_BORDER};"
            f"margin-left:28px;margin-right:28px;"
        )
        v.addWidget(div)
        v.addSpacing(20)

        step_names = [
            ("00", "WELCOME"),
            ("01", "YOUR PROFILE"),
            ("02", "MASTER PASSWORD"),
            ("03", "PASSWORD HINTS"),
            ("04", "SECRET KEY"),
            ("05", "TUTORIAL  1/3"),
            ("06", "TUTORIAL  2/3"),
            ("07", "TUTORIAL  3/3"),
            ("08", "COMPLETE"),
        ]

        self.step_labels = []
        for i, (num, name) in enumerate(step_names):
            lbl = QLabel(f"  {num}  {name}")
            lbl.setFixedHeight(36)
            lbl.setStyleSheet(
                self._active_step_style() if i == 0
                else self._inactive_step_style()
            )
            self.step_labels.append(lbl)
            v.addWidget(lbl)

        v.addStretch()

        enc = self._lbl(
            "// AES-256-GCM  |  LOCAL ONLY",
            C_GHOST, 10, mono=True
        )
        enc.setContentsMargins(28, 0, 0, 0)
        v.addWidget(enc)

        return sidebar

    def _build_pages_area(self):
        self.pages = QStackedWidget()
        self.pages.setStyleSheet(f"background:{C_BG};")

        self.pages.addWidget(self._scroll(self._page_welcome()))
        self.pages.addWidget(self._scroll(self._page_profile()))
        self.pages.addWidget(self._scroll(self._page_password()))
        self.pages.addWidget(self._scroll(self._page_hints()))
        self.pages.addWidget(self._scroll(self._page_dob()))
        self.pages.addWidget(self._scroll(self._page_tutorial(1,
            "THE DECOY DASHBOARD",
            "What any observer watching your screen will see.",
            [
                ("> light_mode  =  decoy_layer",
                 "Shuraksha always opens in light mode showing a "
                 "realistic file manager with real system files. "
                 "Anyone watching sees a completely normal application."),
                ("> decoy_files  =  real_looking, not_protected",
                 "The decoy pulls real system files to appear genuine. "
                 "None of your protected files are visible here. "
                 "They exist only inside the encrypted dark mode layer."),
                ("> decoy.interactive  =  true",
                 "You can click folders and open files in the decoy. "
                 "It behaves exactly like a real file manager. "
                 "Completely convincing to any observer."),
            ]
        )))
        self.pages.addWidget(self._scroll(self._page_tutorial(2,
            "THE DARK MODE TOGGLE",
            "How to move from the decoy into the real vault.",
            [
                ("> locate:  top_right_corner  >  theme_toggle",
                 "In the top right corner there is a small light and "
                 "dark mode slider. It looks like a standard theme toggle. "
                 "Nobody would suspect it is a security trigger."),
                ("> action:  slide_to_dark_mode",
                 "Sliding to dark mode triggers the second layer. "
                 "A BODMAS arithmetic question immediately appears. "
                 "To any observer this looks like a math challenge."),
                ("> toggle  =  hidden_gateway",
                 "Nobody watching your screen would guess a theme toggle "
                 "is the gateway to a hidden encrypted vault. "
                 "This is the first half of the two-layer deception."),
            ]
        )))
        self.pages.addWidget(self._scroll(self._page_tutorial(3,
            "THE BODMAS SCREEN",
            "The final step to open your real vault.",
            [
                ("> display:  arithmetic_challenge",
                 "After switching to dark mode a BODMAS question appears. "
                 "To any observer it looks like a genuine math challenge "
                 "that must be answered correctly."),
                ("> input:  date_of_birth  (NOT the math answer)",
                 "You do not solve the maths question. "
                 "Type your date of birth in DD/MM/YYYY format. "
                 "The real vault opens immediately."),
                ("> wrong_input:  lockout  +  fake_crash",
                 "Multiple wrong answers trigger a lockout and show "
                 "a convincing fake crash screen. "
                 "Prevents brute force completely."),
            ]
        )))
        self.pages.addWidget(self._scroll(self._page_complete()))

        return self.pages

    def _scroll(self, widget):
        s = QScrollArea()
        s.setWidget(widget)
        s.setWidgetResizable(True)
        s.setFrameShape(QFrame.Shape.NoFrame)
        s.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        s.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        s.setStyleSheet(
            f"QScrollArea{{background:{C_BG};border:none;}}"
        )
        return s

    def _build_nav_bar(self):
        nav = QWidget()
        nav.setFixedHeight(NAVBAR_H)
        nav.setStyleSheet(f"background:{C_NAVBAR};")

        h = QHBoxLayout(nav)
        h.setContentsMargins(36, 0, 36, 0)
        h.setSpacing(0)

        self.back_btn = QPushButton("[ BACK ]")
        self.back_btn.setFixedSize(130, 44)
        self.back_btn.setEnabled(False)
        self.back_btn.setStyleSheet(STYLE_BACK)
        self.back_btn.clicked.connect(self._go_back)
        h.addWidget(self.back_btn)

        h.addStretch()

        self.step_counter = self._lbl(
            "STEP  01  OF  09", C_DIM, 11, mono=True, spacing=2
        )
        h.addWidget(self.step_counter)

        h.addStretch()

        self.next_btn = QPushButton("CONTINUE  >>")
        self.next_btn.setFixedSize(160, 44)
        self.next_btn.setStyleSheet(STYLE_CONTINUE)
        self.next_btn.clicked.connect(self._go_next)
        h.addWidget(self.next_btn)

        return nav

    # -----------------------------------------------
    # PAGE BUILDERS
    # -----------------------------------------------

    def _page_header(self, layout, badge, title, subtitle):
        if badge:
            layout.addWidget(
                self._lbl(badge, C_CYAN, 11, bold=True,
                          mono=True, spacing=2)
            )
            layout.addSpacing(8)

        t = QLabel(title)
        t.setStyleSheet(
            f"color:{C_WHITE};font-size:24px;font-weight:bold;"
            f"background:transparent;"
        )
        layout.addWidget(t)

        ul = QFrame()
        ul.setFixedSize(52, 2)
        ul.setStyleSheet(f"background:{C_CYAN};border:none;")
        layout.addWidget(ul)
        layout.addSpacing(10)

        sub = QLabel(subtitle)
        sub.setStyleSheet(f"color:{C_MID};font-size:13px;")
        sub.setWordWrap(True)
        layout.addWidget(sub)
        layout.addSpacing(28)

    def _info_card(self, num, heading, body):
        card = QFrame()
        card.setObjectName(f"card_{num}")
        card.setStyleSheet(
            f"QFrame#card_{num}{{"
            f"  background:{C_CARD};"
            f"  border:1px solid {C_BCARD};"
            f"  border-left:3px solid {C_CYAN};"
            f"}}"
            f"QFrame#card_{num} QLabel{{"
            f"  border:none;background:transparent;"
            f"}}"
        )

        row = QHBoxLayout(card)
        row.setContentsMargins(24, 20, 24, 20)
        row.setSpacing(22)

        n = QLabel(num)
        n.setFixedWidth(40)
        n.setAlignment(Qt.AlignmentFlag.AlignTop)
        n.setStyleSheet(
            f"color:{C_CYAN};font-size:28px;font-weight:bold;"
            f"font-family:'Consolas','Courier New',monospace;"
            f"border:none;background:transparent;"
        )
        row.addWidget(n)

        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setStyleSheet(f"background:{C_BCARD};border:none;")
        row.addWidget(sep)

        col = QVBoxLayout()
        col.setSpacing(7)
        col.setContentsMargins(0, 0, 0, 0)

        hl = QLabel(heading)
        hl.setStyleSheet(
            f"color:{C_WHITE};font-size:13px;font-weight:bold;"
            f"letter-spacing:1px;border:none;background:transparent;"
        )
        bl = QLabel(body)
        bl.setStyleSheet(
            f"color:{C_MID};font-size:13px;"
            f"border:none;background:transparent;"
        )
        bl.setWordWrap(True)

        col.addWidget(hl)
        col.addWidget(bl)
        row.addLayout(col)

        return card

    def _tblock(self, heading, body):
        f = QFrame()
        name = f"tb_{id(f)}"
        f.setObjectName(name)
        f.setStyleSheet(
            f"QFrame#{name}{{"
            f"  background:{C_CARD};"
            f"  border:1px solid {C_BCARD};"
            f"  border-left:3px solid {C_CYAN};"
            f"}}"
            f"QFrame#{name} QLabel{{"
            f"  border:none;background:transparent;"
            f"}}"
        )

        v = QVBoxLayout(f)
        v.setContentsMargins(22, 18, 22, 18)
        v.setSpacing(8)

        hl = QLabel(heading)
        hl.setStyleSheet(
            f"color:{C_CYAN};font-size:12px;font-weight:bold;"
            f"font-family:'Consolas','Courier New',monospace;"
            f"border:none;background:transparent;"
        )
        bl = QLabel(body)
        bl.setStyleSheet(
            f"color:{C_MID};font-size:13px;"
            f"border:none;background:transparent;"
        )
        bl.setWordWrap(True)

        v.addWidget(hl)
        v.addWidget(bl)
        return f

    def _page_welcome(self):
        page = QWidget()
        v    = QVBoxLayout(page)
        v.setContentsMargins(52, 44, 52, 32)
        v.setSpacing(14)

        self._page_header(
            v, "//  INITIALISING SETUP",
            "Welcome to Shuraksha",
            "Your personal encrypted security vault. "
            "Setup takes less than two minutes."
        )
        v.addWidget(self._info_card(
            "01", "NO CLOUD.  NO SERVERS.",
            "Everything is stored only on this machine. "
            "Nothing is ever sent outside your device."
        ))
        v.addWidget(self._info_card(
            "02", "TWO LAYERS OF DECEPTION.",
            "A fully working decoy dashboard hides the real vault "
            "from anyone who can see your screen."
        ))
        v.addWidget(self._info_card(
            "03", "ONE-TIME SETUP.",
            "Your credentials are configured right now. "
            "This registration screen never appears again."
        ))
        v.addStretch()
        return page

    def _page_profile(self):
        page = QWidget()
        v    = QVBoxLayout(page)
        v.setContentsMargins(52, 44, 52, 32)
        v.setSpacing(14)

        self._page_header(
            v, "//  STEP  02  OF  09",
            "Your Profile",
            "This name is shown as a greeting when you open your vault."
        )

        v.addWidget(self._lbl(
            "// DISPLAY NAME", C_MID, 12, mono=True, spacing=1
        ))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("enter_your_name")
        self.name_input.setFixedHeight(52)
        v.addWidget(self.name_input)
        v.addStretch()
        return page

    def _page_password(self):
        page = QWidget()
        v    = QVBoxLayout(page)
        v.setContentsMargins(52, 44, 52, 32)
        v.setSpacing(14)

        self._page_header(
            v, "//  STEP  03  OF  09",
            "Master Password",
            "This password opens the application on every launch."
        )

        v.addWidget(self._lbl(
            "// CREATE PASSWORD", C_MID, 12, mono=True, spacing=1
        ))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("enter_master_password")
        self.password_input.setFixedHeight(52)
        self.password_input.textChanged.connect(self._check_strength)
        v.addWidget(self.password_input)

        self.strength_bar = QProgressBar()
        self.strength_bar.setMaximum(4)
        self.strength_bar.setValue(0)
        self.strength_bar.setTextVisible(False)
        self.strength_bar.setFixedHeight(3)
        self.strength_bar.setStyleSheet(
            f"QProgressBar{{background:{C_BORDER};border:none;}}"
            f"QProgressBar::chunk{{background:{C_CYAN};}}"
        )
        v.addWidget(self.strength_bar)

        self.strength_lbl = self._lbl(
            "// STRENGTH:  ---", C_DIM, 11, mono=True
        )
        v.addWidget(self.strength_lbl)
        v.addSpacing(18)

        v.addWidget(self._lbl(
            "// CONFIRM PASSWORD", C_MID, 12, mono=True, spacing=1
        ))
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setPlaceholderText("re_enter_master_password")
        self.confirm_input.setFixedHeight(52)
        v.addWidget(self.confirm_input)
        v.addSpacing(8)

        v.addWidget(self._lbl(
            "// Minimum 8 characters. "
            "Mix of uppercase, lowercase, numbers, and symbols.",
            C_DIM, 12, mono=True, wrap=True
        ))
        v.addStretch()
        return page

    def _page_hints(self):
        page = QWidget()
        v    = QVBoxLayout(page)
        v.setContentsMargins(52, 44, 52, 32)
        v.setSpacing(14)

        self._page_header(
            v, "//  STEP  04  OF  09",
            "Password Hints",
            "Three personal clues only you would understand."
        )

        warn = QFrame()
        warn.setObjectName("warnbox")
        warn.setStyleSheet(
            f"QFrame#warnbox{{"
            f"  background:{C_CYAN_DIM};"
            f"  border:1px solid {C_FOCUS};"
            f"  border-left:3px solid {C_CYAN};"
            f"}}"
            f"QFrame#warnbox QLabel{{"
            f"  border:none;background:transparent;"
            f"}}"
        )
        wl = QVBoxLayout(warn)
        wl.setContentsMargins(20, 14, 20, 14)
        wl.addWidget(self._lbl(
            "// WARNING: Do NOT write the actual password.\n"
            "// Write personal clues only you would understand.",
            C_MID, 13, mono=True, wrap=True
        ))
        v.addWidget(warn)
        v.addSpacing(10)

        self.hint_inputs = []
        for i in range(3):
            v.addWidget(self._lbl(
                f"// HINT  [ {i+1}  OF  3 ]",
                C_MID, 12, mono=True, spacing=1
            ))
            inp = QLineEdit()
            inp.setPlaceholderText(f"enter_hint_{i+1}")
            inp.setFixedHeight(50)
            self.hint_inputs.append(inp)
            v.addWidget(inp)
            v.addSpacing(6)

        v.addStretch()
        return page

    def _page_dob(self):
        page = QWidget()
        v    = QVBoxLayout(page)
        v.setContentsMargins(52, 44, 52, 32)
        v.setSpacing(14)

        self._page_header(
            v, "//  STEP  05  OF  09",
            "Your Secret Key",
            "The hidden input that opens the real vault "
            "through the BODMAS screen."
        )

        exp = QFrame()
        exp.setObjectName("expbox")
        exp.setStyleSheet(
            f"QFrame#expbox{{"
            f"  background:{C_RED_BG};"
            f"  border:1px solid {C_RED};"
            f"  border-left:3px solid {C_RED};"
            f"}}"
            f"QFrame#expbox QLabel{{"
            f"  border:none;background:transparent;"
            f"}}"
        )
        el = QVBoxLayout(exp)
        el.setContentsMargins(22, 18, 22, 18)
        el.setSpacing(10)
        el.addWidget(self._lbl(
            "// CRITICAL  -  READ THIS BEFORE CONTINUING",
            C_RED, 13, bold=True, mono=True
        ))
        el.addWidget(self._lbl(
            "Shuraksha opens in light mode showing the decoy.\n\n"
            "Slide the theme toggle at the top right to dark mode.\n"
            "A BODMAS arithmetic question will appear.\n\n"
            "DO NOT solve the maths question.\n"
            "Type your date of birth in DD/MM/YYYY format instead.\n"
            "The real vault opens immediately.",
            "#AA4422", 13, mono=True, wrap=True
        ))
        v.addWidget(exp)
        v.addSpacing(18)

        v.addWidget(self._lbl(
            "// DATE OF BIRTH  [ FORMAT: DD/MM/YYYY ]",
            C_MID, 12, mono=True, spacing=1
        ))
        self.dob_input = QLineEdit()
        self.dob_input.setPlaceholderText("DD/MM/YYYY")
        self.dob_input.setFixedHeight(52)
        self.dob_input.setMaxLength(10)
        self.dob_input.textChanged.connect(self._format_dob)
        v.addWidget(self.dob_input)

        self.dob_error = self._lbl("", C_RED, 12, mono=True)
        v.addWidget(self.dob_error)
        v.addSpacing(6)
        v.addWidget(self._lbl(
            "// There is NO recovery if you forget this date.",
            "#662211", 12, mono=True
        ))
        v.addStretch()
        return page

    def _page_tutorial(self, number, title, subtitle, items):
        page = QWidget()
        v    = QVBoxLayout(page)
        v.setContentsMargins(52, 44, 52, 32)
        v.setSpacing(14)
        self._page_header(
            v, f"//  TUTORIAL  {number}  OF  3", title, subtitle
        )
        for heading, body in items:
            v.addWidget(self._tblock(heading, body))
        v.addStretch()
        return page

    def _page_complete(self):
        page = QWidget()
        v    = QVBoxLayout(page)
        v.setContentsMargins(52, 52, 52, 32)
        v.setSpacing(14)

        badge = self._lbl(
            "//  SETUP_STATUS:  COMPLETE",
            C_CYAN, 12, bold=True, mono=True, spacing=2
        )
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(badge)
        v.addSpacing(8)

        t = QLabel("Vault Initialised")
        t.setStyleSheet(
            f"color:{C_WHITE};font-size:28px;font-weight:bold;"
            f"background:transparent;"
        )
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(t)

        self.welcome_lbl = self._lbl("", C_DIM, 13, mono=True)
        self.welcome_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(self.welcome_lbl)
        v.addSpacing(28)

        rem = QFrame()
        rem.setObjectName("rembox")
        rem.setStyleSheet(
            f"QFrame#rembox{{"
            f"  background:{C_CARD};"
            f"  border:1px solid {C_BCARD};"
            f"  border-left:3px solid {C_CYAN};"
            f"}}"
            f"QFrame#rembox QLabel{{"
            f"  border:none;background:transparent;"
            f"}}"
        )
        rl = QVBoxLayout(rem)
        rl.setContentsMargins(28, 22, 28, 22)
        rl.setSpacing(16)
        rl.addWidget(self._lbl(
            "// REMEMBER_THESE  [ 3 RULES ]",
            C_CYAN, 12, bold=True, mono=True, spacing=1
        ))

        for num, text in [
            ("[1]", "Master password opens the application on every launch."),
            ("[2]", "Dark mode toggle at top-right reveals the hidden vault."),
            ("[3]", "Date of birth typed on BODMAS opens the real vault."),
        ]:
            row = QHBoxLayout()
            row.setSpacing(16)
            n = self._lbl(num, C_CYAN, 13, bold=True, mono=True)
            n.setFixedWidth(34)
            t2 = QLabel(text)
            t2.setStyleSheet(
                f"color:{C_MID};font-size:13px;"
                f"border:none;background:transparent;"
            )
            t2.setWordWrap(True)
            row.addWidget(n)
            row.addWidget(t2)
            rl.addLayout(row)

        v.addWidget(rem)
        v.addStretch()
        return page

    # -----------------------------------------------
    # NAVIGATION
    # -----------------------------------------------

    def _go_next(self):
        if self.current_page == 1:
            name = self.name_input.text().strip()
            if not name:
                self._err("// ERROR: display name cannot be empty.")
                return
            self.user_data['username'] = name

        elif self.current_page == 2:
            pwd = self.password_input.text()
            cfm = self.confirm_input.text()
            if len(pwd) < 8:
                self._err(
                    "// ERROR: password must be at least 8 characters."
                )
                return
            if pwd != cfm:
                self._err("// ERROR: the two passwords do not match.")
                return
            h, s = hash_value(pwd)
            self.user_data['password_hash'] = h
            self.user_data['password_salt'] = s
            self._plain_password = pwd

        elif self.current_page == 3:
            hints = [i.text().strip() for i in self.hint_inputs]
            if not any(hints):
                self._err("// ERROR: at least one hint is required.")
                return
            self.user_data['hints'] = hints

        elif self.current_page == 4:
            dob = self.dob_input.text().strip()
            if not self._valid_dob(dob):
                self.dob_error.setText(
                    "// ERROR: invalid date - use DD/MM/YYYY"
                )
                return
            self.dob_error.setText("")
            h, s = hash_value(dob)
            self.user_data['dob_hash'] = h
            self.user_data['dob_salt'] = s

        elif self.current_page == 8:
            self._save()
            return

        self.current_page += 1
        self.pages.setCurrentIndex(self.current_page)
        self._refresh_sidebar()
        self.progress_bar.setValue(self.current_page)

        num = str(self.current_page + 1).zfill(2)
        self.step_counter.setText(f"STEP  {num}  OF  09")
        self.title_counter.setText(f"{num} / 09")
        self.back_btn.setEnabled(True)

        if self.current_page == 8:
            self.next_btn.setText("FINALISE  >>")
            self.welcome_lbl.setText(
                f"// operator:  {self.user_data['username']}"
                f"  |  status:  READY"
            )

    def _go_back(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.pages.setCurrentIndex(self.current_page)
            self._refresh_sidebar()
            self.progress_bar.setValue(self.current_page)
            num = str(self.current_page + 1).zfill(2)
            self.step_counter.setText(f"STEP  {num}  OF  09")
            self.title_counter.setText(f"{num} / 09")
            self.next_btn.setText("CONTINUE  >>")
            if self.current_page == 0:
                self.back_btn.setEnabled(False)

    def _refresh_sidebar(self):
        for i, lbl in enumerate(self.step_labels):
            if i < self.current_page:
                lbl.setStyleSheet(self._done_step_style())
            elif i == self.current_page:
                lbl.setStyleSheet(self._active_step_style())
            else:
                lbl.setStyleSheet(self._inactive_step_style())

    # -----------------------------------------------
    # INPUT HELPERS
    # -----------------------------------------------

    def _check_strength(self, pwd):
        score = 0
        if len(pwd) >= 8:  score += 1
        if len(pwd) >= 12: score += 1
        if any(c.isdigit() for c in pwd): score += 1
        if any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in pwd):
            score += 1

        cols  = {0:'#333355',1:'#FF3A1A',2:'#FF8800',
                 3:'#CCCC00',4:'#00CC66'}
        names = {0:'TOO_SHORT',1:'WEAK',2:'FAIR',
                 3:'GOOD',4:'STRONG'}
        c = cols.get(score, '#333355')
        self.strength_bar.setValue(score)
        self.strength_lbl.setText(
            f"// STRENGTH:  {names.get(score, '---')}"
        )
        self.strength_lbl.setStyleSheet(
            f"color:{c};font-size:11px;"
            f"font-family:'Consolas','Courier New',monospace;"
            f"background:transparent;"
        )
        self.strength_bar.setStyleSheet(
            f"QProgressBar{{background:{C_BORDER};border:none;}}"
            f"QProgressBar::chunk{{background:{c};}}"
        )

    def _format_dob(self, text):
        digits = ''.join(c for c in text if c.isdigit())
        fmt = ''
        if len(digits) >= 1: fmt = digits[:2]
        if len(digits) >= 3: fmt += '/' + digits[2:4]
        if len(digits) >= 5: fmt += '/' + digits[4:8]
        if text != fmt:
            self.dob_input.blockSignals(True)
            self.dob_input.setText(fmt)
            self.dob_input.setCursorPosition(len(fmt))
            self.dob_input.blockSignals(False)

    def _valid_dob(self, dob):
        if not re.match(r'^\d{2}/\d{2}/\d{4}$', dob):
            return False
        try:
            d, m, y = (int(x) for x in dob.split('/'))
            return 1 <= m <= 12 and 1 <= d <= 31 and 1900 <= y <= 2025
        except ValueError:
            return False

    def _err(self, message):
        box = QMessageBox(self)
        box.setWindowTitle("// INPUT ERROR")
        box.setText(message)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setStyleSheet(
            f"QMessageBox{{background:{C_BG};color:{C_WHITE};"
            f"font-family:'Consolas','Courier New',monospace;"
            f"font-size:13px;}}"
            f"QPushButton{{background:{C_CYAN};color:#000000;"
            f"border:none;padding:8px 22px;font-weight:bold;"
            f"font-size:12px;"
            f"font-family:'Consolas','Courier New',monospace;}}"
        )
        box.exec()

    # -----------------------------------------------
    # SAVE
    # The most important method in registration.
    #
    # Structure written to user.dat:
    # {
    #   "password_hash": "...",   <- OUTSIDE encrypted blob
    #   "password_salt": "...",   <- OUTSIDE encrypted blob
    #   "encrypted": {            <- AES-256-GCM encrypted
    #     "ciphertext": "...",
    #     "nonce": "...",
    #     "salt": "..."
    #   }
    # }
    #
    # password_hash and password_salt are outside so the
    # login screen can verify the password WITHOUT decrypting.
    # Only after verification does decryption happen.
    # -----------------------------------------------

    def _save(self):
        try:
            APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
            VAULT_DIR.mkdir(parents=True, exist_ok=True)

            # Inner data - goes inside the encrypted blob
            inner = {
                'username'      : self.user_data['username'],
                'hints'         : self.user_data['hints'],
                'dob_hash'      : self.user_data['dob_hash'],
                'dob_salt'      : self.user_data['dob_salt'],
                'setup_complete': True,
            }

            # Encrypt the inner data with the master password
            encrypted_blob = encrypt_json(inner, self._plain_password)

            # Final structure written to disk
            # password_hash and password_salt sit OUTSIDE
            # the encrypted blob for login verification
            save_data = {
                'password_hash': self.user_data['password_hash'],
                'password_salt': self.user_data['password_salt'],
                'encrypted'    : encrypted_blob,
            }

            with open(USER_DATA_FILE, 'w') as f:
                json.dump(save_data, f)

            # Wipe plain password from memory immediately
            self._plain_password = ''

            QMessageBox.information(
                self,
                "// SETUP COMPLETE",
                "Vault initialised successfully.\n\nClick OK to finish."
            )
            QApplication.quit()

        except Exception as e:
            self._err(f"// CRITICAL ERROR:\n{str(e)}")

    def _on_cancel(self):
        box = QMessageBox(self)
        box.setWindowTitle("// CANCEL SETUP")
        box.setText(
            "Abort installation?\n\n"
            "Shuraksha will not function until setup is complete."
        )
        box.setStandardButtons(
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No
        )
        box.setStyleSheet(
            f"QMessageBox{{background:{C_BG};color:{C_WHITE};"
            f"font-family:'Consolas','Courier New',monospace;"
            f"font-size:13px;}}"
            f"QPushButton{{background:{C_CYAN};color:#000000;"
            f"border:none;padding:8px 20px;font-weight:bold;"
            f"font-size:12px;"
            f"font-family:'Consolas','Courier New',monospace;}}"
        )
        if box.exec() == QMessageBox.StandardButton.Yes:
            QApplication.quit()

    # -----------------------------------------------
    # WINDOW DRAG
    # -----------------------------------------------

    def mousePressEvent(self, event):
        if event.position().y() < PROGRESS_H + TITLEBAR_H:
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
    window = RegistrationWizard()
    window.show()
    sys.exit(app.exec())