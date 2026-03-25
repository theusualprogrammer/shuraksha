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
from PyQt6.QtGui import QColor, QPalette

from src.core.crypto import hash_value, encrypt_json

# -----------------------------------------------
# STORAGE
# -----------------------------------------------
APP_DATA_DIR   = Path(os.environ.get('APPDATA', '')) / 'Shuraksha'
USER_DATA_FILE = APP_DATA_DIR / 'user.dat'
VAULT_DIR      = APP_DATA_DIR / 'vault'

# -----------------------------------------------
# DIMENSIONS  (all in pixels, fixed layout)
# -----------------------------------------------
WIN_W       = 1024
WIN_H       = 720
PROG_H      = 3
TITLE_H     = 42
DIV_H       = 1
NAVBAR_H    = 76
SIDEBAR_W   = 240
# Content height = total minus all fixed rows
CONTENT_H   = WIN_H - PROG_H - TITLE_H - DIV_H - NAVBAR_H - DIV_H

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
# BUTTON STYLES applied directly to widgets
# so the global stylesheet cannot override them
# -----------------------------------------------
STYLE_CONTINUE = (
    f"QPushButton{{"
    f"  background-color: #38C8FF;"
    f"  color: #000000;"
    f"  border: none;"
    f"  font-size: 13px;"
    f"  font-weight: bold;"
    f"  font-family: 'Consolas','Courier New',monospace;"
    f"  letter-spacing: 1px;"
    f"}}"
    f"QPushButton:hover{{"
    f"  background-color: #60D8FF;"
    f"  color: #000000;"
    f"}}"
    f"QPushButton:pressed{{"
    f"  background-color: #20A0CC;"
    f"  color: #000000;"
    f"}}"
)

STYLE_BACK = (
    f"QPushButton{{"
    f"  background-color: transparent;"
    f"  color: #2A4A62;"
    f"  border: 1px solid #112040;"
    f"  font-size: 13px;"
    f"  font-family: 'Consolas','Courier New',monospace;"
    f"  letter-spacing: 1px;"
    f"}}"
    f"QPushButton:hover{{"
    f"  color: #38C8FF;"
    f"  border: 1px solid #38C8FF;"
    f"  background-color: transparent;"
    f"}}"
    f"QPushButton:disabled{{"
    f"  color: #0E1E2E;"
    f"  border: 1px solid #0E1E2E;"
    f"  background-color: transparent;"
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
    Uses a fixed pixel layout so nothing is ever hidden or cut off.
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

        # Apply global stylesheet - does NOT touch buttons
        self.setStyleSheet(STYLE_GLOBAL)
        self._build_layout()

    # -----------------------------------------------
    # SMALL HELPERS
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
        """
        Create a QLabel with precise styling.
        Keeps all text creation in one place so styles are consistent.
        """
        lbl = QLabel(text)
        family = (
            "'Consolas','Courier New',monospace" if mono
            else "'Segoe UI',Arial,sans-serif"
        )
        weight = "font-weight:bold;" if bold else ""
        ls = f"letter-spacing:{spacing}px;" if spacing else ""
        lbl.setStyleSheet(
            f"color:{color};font-size:{size}px;"
            f"font-family:{family};{weight}{ls}"
            f"background:transparent;"
        )
        if wrap:
            lbl.setWordWrap(True)
        return lbl

    def _step_active(self):
        return (
            f"color:{C_CYAN};font-size:12px;font-weight:bold;"
            f"font-family:'Consolas','Courier New',monospace;"
            f"letter-spacing:1px;"
            f"background:{C_STEP_ACT};"
            f"border-left:3px solid {C_CYAN};"
            f"padding-left:25px;"
        )

    def _step_done(self):
        return (
            f"color:{C_DIM};font-size:12px;"
            f"font-family:'Consolas','Courier New',monospace;"
            f"padding-left:28px;"
        )

    def _step_future(self):
        return (
            f"color:{C_GHOST};font-size:12px;"
            f"font-family:'Consolas','Courier New',monospace;"
            f"padding-left:28px;"
        )

    # -----------------------------------------------
    # LAYOUT
    # -----------------------------------------------

    def _build_layout(self):
        """
        Precise fixed-pixel vertical layout:
            PROG_H    progress bar
            TITLE_H   title bar
            DIV_H     divider
            CONTENT_H sidebar + pages (side by side)
            DIV_H     divider
            NAVBAR_H  navigation bar   <-- always last, always visible
        Total = WIN_H = 720px
        """
        root = QWidget()
        self.setCentralWidget(root)

        v = QVBoxLayout(root)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # 1. Progress bar
        self.prog = QProgressBar()
        self.prog.setMaximum(8)
        self.prog.setValue(0)
        self.prog.setTextVisible(False)
        self.prog.setFixedHeight(PROG_H)
        self.prog.setStyleSheet(
            f"QProgressBar{{background:{C_TITLEBAR};border:none;}}"
            f"QProgressBar::chunk{{background:{C_CYAN};border:none;}}"
        )
        v.addWidget(self.prog)

        # 2. Title bar
        v.addWidget(self._build_titlebar())

        # 3. Divider
        v.addWidget(self._hline())

        # 4. Content row - fixed height so navbar cannot be pushed down
        content = QWidget()
        content.setFixedHeight(CONTENT_H)
        content.setStyleSheet(f"background:{C_BG};")
        h = QHBoxLayout(content)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)
        h.addWidget(self._build_sidebar())
        h.addWidget(self._vline())
        h.addWidget(self._build_pages())
        v.addWidget(content)

        # 5. Divider
        v.addWidget(self._hline())

        # 6. Navigation bar - always the last widget, always fully visible
        v.addWidget(self._build_navbar())

    def _build_titlebar(self):
        bar = QWidget()
        bar.setFixedHeight(TITLE_H)
        bar.setStyleSheet(f"background:{C_TITLEBAR};")

        h = QHBoxLayout(bar)
        h.setContentsMargins(24, 0, 24, 0)
        h.setSpacing(0)

        h.addWidget(
            self._lbl("[  SHR  ]", C_CYAN, 12, bold=True, mono=True, spacing=2)
        )
        h.addWidget(self._lbl("  //  ", C_GHOST, 12, mono=True))
        h.addWidget(
            self._lbl("SETUP AND REGISTRATION", C_DIM, 12, mono=True, spacing=2)
        )
        h.addStretch()

        self.title_step = self._lbl("01 / 09", C_DIM, 12, mono=True)
        h.addWidget(self.title_step)
        h.addSpacing(24)

        cancel = QPushButton("[ CANCEL ]")
        cancel.setStyleSheet(
            f"QPushButton{{background:transparent;color:{C_DIM};"
            f"border:none;font-size:12px;"
            f"font-family:'Consolas','Courier New',monospace;}}"
            f"QPushButton:hover{{color:{C_RED};}}"
        )
        cancel.clicked.connect(self._on_cancel)
        h.addWidget(cancel)

        return bar

    def _build_sidebar(self):
        side = QWidget()
        side.setFixedWidth(SIDEBAR_W)
        side.setStyleSheet(f"background:{C_SIDEBAR};")

        v = QVBoxLayout(side)
        v.setContentsMargins(0, 32, 0, 24)
        v.setSpacing(0)

        # Brand name
        bl = QVBoxLayout()
        bl.setContentsMargins(28, 0, 28, 0)
        bl.setSpacing(4)
        brand = QLabel("SHURAKSHA")
        brand.setStyleSheet(
            f"color:{C_WHITE};font-size:16px;font-weight:bold;"
            f"letter-spacing:4px;background:transparent;"
        )
        bl.addWidget(brand)
        bl.addWidget(
            self._lbl("> security_vault.exe", C_DIM, 11, mono=True)
        )
        v.addLayout(bl)
        v.addSpacing(22)

        # Horizontal rule
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(
            f"background:{C_BORDER};"
            f"margin-left:28px;margin-right:28px;"
        )
        v.addWidget(div)
        v.addSpacing(18)

        # Step list
        steps = [
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
        for i, (num, name) in enumerate(steps):
            lbl = QLabel(f"  {num}  {name}")
            lbl.setFixedHeight(36)
            lbl.setStyleSheet(
                self._step_active() if i == 0 else self._step_future()
            )
            self.step_labels.append(lbl)
            v.addWidget(lbl)

        v.addStretch()

        enc = self._lbl("// AES-256-GCM  |  LOCAL ONLY", C_GHOST, 10, mono=True)
        enc.setContentsMargins(28, 0, 0, 0)
        v.addWidget(enc)

        return side

    def _build_pages(self):
        self.pages = QStackedWidget()
        self.pages.setStyleSheet(f"background:{C_BG};")

        self.pages.addWidget(self._wrap(self._page_welcome()))
        self.pages.addWidget(self._wrap(self._page_profile()))
        self.pages.addWidget(self._wrap(self._page_password()))
        self.pages.addWidget(self._wrap(self._page_hints()))
        self.pages.addWidget(self._wrap(self._page_dob()))
        self.pages.addWidget(self._wrap(self._page_tutorial(1,
            "THE DECOY DASHBOARD",
            "What any observer watching your screen will see.",
            [
                ("> light_mode  =  decoy_layer",
                 "Shuraksha always opens in light mode showing a realistic "
                 "file manager with photos and documents from your system. "
                 "Anyone watching sees a completely normal application. "
                 "Nothing looks suspicious from the outside."),
                ("> decoy_files  =  real_looking,  not_your_protected_files",
                 "The decoy pulls real system files to appear genuine. "
                 "None of your actually protected files are visible here. "
                 "They exist only inside the encrypted dark mode layer "
                 "which no observer can reach."),
                ("> decoy.interactive  =  true",
                 "You can click folders and open files in the decoy. "
                 "It behaves exactly like a real file manager. "
                 "This makes it completely convincing to anyone "
                 "watching over your shoulder."),
            ]
        )))
        self.pages.addWidget(self._wrap(self._page_tutorial(2,
            "THE DARK MODE TOGGLE",
            "How to move from the decoy into the real vault.",
            [
                ("> locate:  top_right_corner  >  theme_toggle",
                 "In the top right corner of Shuraksha there is a small "
                 "light and dark mode slider. It looks like a standard "
                 "theme toggle found on any modern application. "
                 "Nobody would ever suspect it is a security trigger."),
                ("> action:  slide_to_dark_mode",
                 "Sliding to dark mode triggers the second layer. "
                 "A BODMAS arithmetic question immediately appears. "
                 "To any observer this looks like a mathematical "
                 "security challenge they need to solve."),
                ("> toggle  =  hidden_gateway",
                 "Nobody watching your screen would guess a theme toggle "
                 "is the gateway to a hidden encrypted vault. "
                 "This is the first half of the two-layer deception "
                 "system built into Shuraksha."),
            ]
        )))
        self.pages.addWidget(self._wrap(self._page_tutorial(3,
            "THE BODMAS SCREEN",
            "The final step to open your real vault.",
            [
                ("> display:  arithmetic_challenge",
                 "After switching to dark mode a BODMAS arithmetic question "
                 "appears on screen. To any observer it looks like a genuine "
                 "mathematical challenge that must be answered correctly. "
                 "It is completely convincing."),
                ("> input:  date_of_birth  (NOT the math answer)",
                 "You do not solve the maths question at all. "
                 "Type your date of birth in DD/MM/YYYY format "
                 "into the answer box. The real vault opens "
                 "immediately the moment you submit it."),
                ("> wrong_input:  lockout  +  fake_crash",
                 "Multiple wrong answers trigger a lockout and show "
                 "a convincing fake crash screen. "
                 "This prevents brute force completely and looks "
                 "authentic to any attacker watching."),
            ]
        )))
        self.pages.addWidget(self._wrap(self._page_complete()))

        return self.pages

    def _wrap(self, widget):
        """
        Wrap any page in a scroll area.
        Content never gets hidden even if screen scaling is unusual.
        """
        s = QScrollArea()
        s.setWidget(widget)
        s.setWidgetResizable(True)
        s.setFrameShape(QFrame.Shape.NoFrame)
        s.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        s.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        s.setStyleSheet(f"QScrollArea{{background:{C_BG};border:none;}}")
        return s

    def _build_navbar(self):
        """
        Navigation bar.
        Button styles are set DIRECTLY on each button with setStyleSheet()
        so the global stylesheet cannot override them.
        """
        nav = QWidget()
        nav.setFixedHeight(NAVBAR_H)
        nav.setStyleSheet(f"background:{C_NAVBAR};border:none;")

        h = QHBoxLayout(nav)
        h.setContentsMargins(36, 0, 36, 0)
        h.setSpacing(0)

        # Back button - styled directly
        self.back_btn = QPushButton("[ BACK ]")
        self.back_btn.setFixedSize(130, 46)
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

        # Continue button - styled directly with full opacity cyan
        self.next_btn = QPushButton("CONTINUE  >>")
        self.next_btn.setFixedSize(164, 46)
        self.next_btn.setStyleSheet(STYLE_CONTINUE)
        self.next_btn.clicked.connect(self._go_next)
        h.addWidget(self.next_btn)

        return nav

    # -----------------------------------------------
    # PAGE BUILDERS
    # -----------------------------------------------

    def _header(self, layout, badge, title, subtitle):
        """Standard page header: badge + title + underline + subtitle."""
        if badge:
            layout.addWidget(
                self._lbl(badge, C_CYAN, 11, bold=True, mono=True, spacing=2)
            )
            layout.addSpacing(8)

        t = QLabel(title)
        t.setStyleSheet(
            f"color:{C_WHITE};font-size:26px;font-weight:bold;"
            f"background:transparent;"
        )
        layout.addWidget(t)

        ul = QFrame()
        ul.setFixedSize(52, 2)
        ul.setStyleSheet(f"background:{C_CYAN};border:none;")
        layout.addWidget(ul)

        layout.addSpacing(12)

        layout.addWidget(self._lbl(subtitle, C_MID, 14, wrap=True))
        layout.addSpacing(28)

    def _card(self, num, heading, body):
        """
        Feature card with number on left and text on right.
        Single unified frame - no nested borders.
        """
        f = QFrame()
        f.setStyleSheet(
            f"QFrame#{f.objectName()}{{}}"
        )
        # Use object name trick to scope the border to this frame only
        f.setObjectName(f"card_{num}")
        f.setStyleSheet(
            f"QFrame#card_{num}{{"
            f"  background:{C_CARD};"
            f"  border:1px solid {C_BCARD};"
            f"  border-left:3px solid {C_CYAN};"
            f"}}"
            # Make sure child labels do not get borders
            f"QFrame#card_{num} QLabel{{"
            f"  border:none;"
            f"  background:transparent;"
            f"}}"
        )

        row = QHBoxLayout(f)
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

        return f

    def _tblock(self, heading, body):
        """Tutorial item block with cyan left border."""
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
            f"  border:none;"
            f"  background:transparent;"
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
            f"color:{C_MID};font-size:13px;line-height:1.6;"
            f"border:none;background:transparent;"
        )
        bl.setWordWrap(True)

        v.addWidget(hl)
        v.addWidget(bl)
        return f

    def _page_welcome(self):
        p = QWidget()
        v = QVBoxLayout(p)
        v.setContentsMargins(52, 44, 52, 32)
        v.setSpacing(14)

        self._header(
            v, "//  INITIALISING SETUP",
            "Welcome to Shuraksha",
            "Your personal encrypted security vault. "
            "Setup takes less than two minutes."
        )
        v.addWidget(self._card(
            "01", "NO CLOUD.  NO SERVERS.",
            "Everything is stored only on this machine. "
            "Nothing is ever sent outside your device under any circumstance."
        ))
        v.addWidget(self._card(
            "02", "TWO LAYERS OF DECEPTION.",
            "A fully working decoy dashboard hides the real vault from "
            "anyone who can see your screen or picks up your device."
        ))
        v.addWidget(self._card(
            "03", "ONE-TIME SETUP.",
            "Your credentials are configured right now during installation. "
            "This registration screen never appears again."
        ))
        v.addStretch()
        return p

    def _page_profile(self):
        p = QWidget()
        v = QVBoxLayout(p)
        v.setContentsMargins(52, 44, 52, 32)
        v.setSpacing(14)

        self._header(
            v, "//  STEP  02  OF  09",
            "Your Profile",
            "This name is shown as a greeting when you open your vault. "
            "It does not need to be your real name."
        )

        v.addWidget(
            self._lbl("// DISPLAY NAME", C_MID, 12, mono=True, spacing=1)
        )
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("enter_your_name")
        self.name_input.setFixedHeight(52)
        v.addWidget(self.name_input)
        v.addSpacing(8)
        v.addWidget(self._lbl(
            "// You can use any name, nickname, or alias you prefer.",
            C_DIM, 12, mono=True
        ))
        v.addStretch()
        return p

    def _page_password(self):
        p = QWidget()
        v = QVBoxLayout(p)
        v.setContentsMargins(52, 44, 52, 32)
        v.setSpacing(14)

        self._header(
            v, "//  STEP  03  OF  09",
            "Master Password",
            "This password opens the application on every single launch. "
            "Choose something strong and memorable."
        )

        v.addWidget(
            self._lbl("// CREATE PASSWORD", C_MID, 12, mono=True, spacing=1)
        )
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
            f"QProgressBar::chunk{{background:{C_CYAN};border:none;}}"
        )
        v.addWidget(self.strength_bar)

        self.strength_lbl = self._lbl("// STRENGTH:  ---", C_DIM, 11, mono=True)
        v.addWidget(self.strength_lbl)
        v.addSpacing(18)

        v.addWidget(
            self._lbl("// CONFIRM PASSWORD", C_MID, 12, mono=True, spacing=1)
        )
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setPlaceholderText("re_enter_master_password")
        self.confirm_input.setFixedHeight(52)
        v.addWidget(self.confirm_input)
        v.addSpacing(8)
        v.addWidget(self._lbl(
            "// Minimum 8 characters. Mix of uppercase, lowercase, "
            "numbers, and symbols.",
            C_DIM, 12, mono=True, wrap=True
        ))
        v.addStretch()
        return p

    def _page_hints(self):
        p = QWidget()
        v = QVBoxLayout(p)
        v.setContentsMargins(52, 44, 52, 32)
        v.setSpacing(14)

        self._header(
            v, "//  STEP  04  OF  09",
            "Password Hints",
            "Three personal clues only you would understand. "
            "These help you remember your master password."
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
            "// WARNING: Do NOT write the actual password or any part of it.\n"
            "// Write personal clues only you would understand.",
            C_MID, 13, mono=True, wrap=True
        ))
        v.addWidget(warn)
        v.addSpacing(8)

        self.hint_inputs = []
        for i in range(3):
            v.addWidget(
                self._lbl(
                    f"// HINT  [ {i+1}  OF  3 ]",
                    C_MID, 12, mono=True, spacing=1
                )
            )
            inp = QLineEdit()
            inp.setPlaceholderText(f"enter_hint_{i+1}")
            inp.setFixedHeight(50)
            self.hint_inputs.append(inp)
            v.addWidget(inp)
            v.addSpacing(6)

        v.addStretch()
        return p

    def _page_dob(self):
        p = QWidget()
        v = QVBoxLayout(p)
        v.setContentsMargins(52, 44, 52, 32)
        v.setSpacing(14)

        self._header(
            v, "//  STEP  05  OF  09",
            "Your Secret Key",
            "The hidden input that opens the real vault through the BODMAS screen. "
            "This is the most critical part of setup."
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
        el.addWidget(
            self._lbl(
                "// CRITICAL  -  READ THIS BEFORE CONTINUING",
                C_RED, 13, bold=True, mono=True
            )
        )
        el.addWidget(self._lbl(
            "Shuraksha opens in light mode showing the decoy file manager.\n\n"
            "Slide the theme toggle at the top right corner to dark mode.\n"
            "A BODMAS arithmetic question will appear on the screen.\n\n"
            "DO NOT solve the maths question.\n"
            "Type your date of birth in DD/MM/YYYY format instead.\n"
            "The real vault opens immediately.",
            "#AA4422", 13, mono=True, wrap=True
        ))
        v.addWidget(exp)
        v.addSpacing(18)

        v.addWidget(
            self._lbl(
                "// DATE OF BIRTH  [ FORMAT: DD/MM/YYYY ]",
                C_MID, 12, mono=True, spacing=1
            )
        )
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
            "// There is NO recovery option if you forget this date.",
            "#662211", 12, mono=True
        ))
        v.addStretch()
        return p

    def _page_tutorial(self, number, title, subtitle, items):
        p = QWidget()
        v = QVBoxLayout(p)
        v.setContentsMargins(52, 44, 52, 32)
        v.setSpacing(14)

        self._header(v, f"//  TUTORIAL  {number}  OF  3", title, subtitle)
        for heading, body in items:
            v.addWidget(self._tblock(heading, body))
        v.addStretch()
        return p

    def _page_complete(self):
        p = QWidget()
        v = QVBoxLayout(p)
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
        rl.addWidget(
            self._lbl(
                "// REMEMBER_THESE  [ 3 RULES ]",
                C_CYAN, 12, bold=True, mono=True, spacing=1
            )
        )

        for num, text in [
            ("[1]", "Your master password opens the application on every launch."),
            ("[2]", "The dark mode toggle at top-right reveals the hidden vault."),
            ("[3]", "Your date of birth typed on BODMAS opens the real vault."),
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
        return p

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
                self._err("// ERROR: password must be at least 8 characters.")
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
        self._refresh()
        self.prog.setValue(self.current_page)
        num = str(self.current_page + 1).zfill(2)
        self.step_counter.setText(f"STEP  {num}  OF  09")
        self.title_step.setText(f"{num} / 09")
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
            self._refresh()
            self.prog.setValue(self.current_page)
            num = str(self.current_page + 1).zfill(2)
            self.step_counter.setText(f"STEP  {num}  OF  09")
            self.title_step.setText(f"{num} / 09")
            self.next_btn.setText("CONTINUE  >>")
            if self.current_page == 0:
                self.back_btn.setEnabled(False)

    def _refresh(self):
        for i, lbl in enumerate(self.step_labels):
            if i < self.current_page:
                lbl.setStyleSheet(self._step_done())
            elif i == self.current_page:
                lbl.setStyleSheet(self._step_active())
            else:
                lbl.setStyleSheet(self._step_future())

    # -----------------------------------------------
    # INPUT HELPERS
    # -----------------------------------------------

    def _check_strength(self, pwd):
        score = 0
        if len(pwd) >= 8:  score += 1
        if len(pwd) >= 12: score += 1
        if any(c.isdigit() for c in pwd): score += 1
        if any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in pwd): score += 1

        cols  = {0:'#333355',1:'#FF3A1A',2:'#FF8800',3:'#CCCC00',4:'#00CC66'}
        names = {0:'TOO_SHORT',1:'WEAK',2:'FAIR',3:'GOOD',4:'STRONG'}
        c = cols.get(score, '#333355')

        self.strength_bar.setValue(score)
        self.strength_bar.setStyleSheet(
            f"QProgressBar{{background:{C_BORDER};border:none;}}"
            f"QProgressBar::chunk{{background:{c};border:none;}}"
        )
        self.strength_lbl.setText(f"// STRENGTH:  {names.get(score,'---')}")
        self.strength_lbl.setStyleSheet(
            f"color:{c};font-size:11px;"
            f"font-family:'Consolas','Courier New',monospace;"
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

    def _err(self, msg):
        box = QMessageBox(self)
        box.setWindowTitle("// INPUT ERROR")
        box.setText(msg)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setStyleSheet(
            f"QMessageBox{{background:{C_BG};color:{C_WHITE};"
            f"font-family:'Consolas','Courier New',monospace;font-size:13px;}}"
            f"QPushButton{{background:{C_CYAN};color:#000000;border:none;"
            f"padding:8px 22px;font-weight:bold;font-size:12px;"
            f"font-family:'Consolas','Courier New',monospace;}}"
        )
        box.exec()

    # -----------------------------------------------
    # SAVE
    # -----------------------------------------------

    def _save(self):
        try:
            APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
            VAULT_DIR.mkdir(parents=True, exist_ok=True)

            data = {
                'username'      : self.user_data['username'],
                'password_hash' : self.user_data['password_hash'],
                'password_salt' : self.user_data['password_salt'],
                'hints'         : self.user_data['hints'],
                'dob_hash'      : self.user_data['dob_hash'],
                'dob_salt'      : self.user_data['dob_salt'],
                'setup_complete': True,
            }
            enc = encrypt_json(data, self._plain_password)
            with open(USER_DATA_FILE, 'w') as f:
                json.dump(enc, f)
            self._plain_password = ''

            QMessageBox.information(
                self, "// SETUP COMPLETE",
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
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        box.setStyleSheet(
            f"QMessageBox{{background:{C_BG};color:{C_WHITE};"
            f"font-family:'Consolas','Courier New',monospace;font-size:13px;}}"
            f"QPushButton{{background:{C_CYAN};color:#000000;border:none;"
            f"padding:8px 20px;font-weight:bold;font-size:12px;"
            f"font-family:'Consolas','Courier New',monospace;}}"
        )
        if box.exec() == QMessageBox.StandardButton.Yes:
            QApplication.quit()

    # -----------------------------------------------
    # WINDOW DRAG
    # -----------------------------------------------

    def mousePressEvent(self, event):
        if event.position().y() < PROG_H + TITLE_H:
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
