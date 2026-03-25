# -----------------------------------------------
# Shuraksha - BODMAS Screen
# File: src/ui/bodmas.py
# -----------------------------------------------
# This screen appears when the user slides the
# theme toggle to dark mode.
#
# What an observer sees:
#   - A dark screen with a maths question
#   - An answer input field
#   - A Submit button
#   - Wrong answers show an error message
#
# What is actually happening:
#   - The maths question is completely fake
#   - Typing the date of birth in DD/MM/YYYY
#     format and pressing Submit opens the real vault
#   - Wrong answers (not the DOB) count as attempts
#   - After MAX_WRONG attempts the screen locks
#     and shows a fake crash screen
#
# The deception works because:
#   - The question looks legitimate and simple
#   - Nobody would guess to type a date instead
#   - The error messages look like wrong math answers
# -----------------------------------------------

import sys
import re
import random
from pathlib import Path

# Adjust path to find core modules if running from this file
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QGraphicsOpacityEffect, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation
from PyQt6.QtGui import QFont

# Mocking crypto for standalone execution if not found
try:
    from src.core.crypto import verify_value, hash_value
except ImportError:
    import hashlib
    import os
    def hash_value(val):
        salt = os.urandom(16).hex()
        h = hashlib.sha256((val + salt).encode()).hexdigest()
        return h, salt
    def verify_value(val, h, salt):
        return hashlib.sha256((val + salt).encode()).hexdigest() == h

# -----------------------------------------------
# DIMENSIONS
# -----------------------------------------------
WIN_W = 1100
WIN_H = 720

# -----------------------------------------------
# HOW MANY WRONG ANSWERS BEFORE LOCKOUT
# -----------------------------------------------
MAX_WRONG = 4

# -----------------------------------------------
# COLOURS  (dark mode - same palette as the vault)
# -----------------------------------------------
C_BG        = "#060912"
C_PANEL     = "#04060E"
C_CARD      = "#080C18"
C_INPUT     = "#050810"
C_TITLEBAR  = "#030508"
C_BORDER    = "#0E1830"
C_BCARD     = "#112040"
C_FOCUS     = "#38C8FF"
C_CYAN      = "#38C8FF"
C_CYAN_H    = "#60D8FF"
C_CYAN_DIM  = "#0A1E30"
C_WHITE     = "#E0F4FF"
C_MID       = "#7AB8D8"
C_DIM       = "#2A4A62"
# C_GHOST was too dim for some UI elements
C_GHOST     = "#0E1E2E" 
C_RED       = "#FF3A1A"
C_RED_BG    = "#1A0500"
C_GREEN     = "#00CC66"
C_AMBER     = "#FF8800"

# -----------------------------------------------
# BUTTON STYLES
# -----------------------------------------------
BTN_PRIMARY = (
    f"QPushButton{{"
    f"  background-color:{C_CYAN};"
    f"  color:#000000;"
    f"  border:none;"
    f"  font-size:14px;"
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
    f"}}"
)

BTN_GHOST = (
    f"QPushButton{{"
    f"  background-color:transparent;"
    f"  color:{C_DIM};"
    f"  border:1px solid {C_BCARD};"
    f"  font-size:13px;"
    f"  font-family:'Consolas','Courier New',monospace;"
    f"}}"
    f"QPushButton:hover{{"
    f"  color:{C_CYAN};"
    f"  border:1px solid {C_CYAN};"
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
        font-size: 22px;
        font-family: 'Consolas','Courier New',monospace;
        padding: 12px 20px;
        border-radius: 0px;
        letter-spacing: 3px;
    }}
    QLineEdit:focus {{
        border: 1px solid {C_FOCUS};
        border-bottom: 2px solid {C_CYAN};
    }}
"""


# -----------------------------------------------
# BODMAS QUESTION GENERATOR
# -----------------------------------------------
class BodmasQuestion:
    """
    Generates a simple BODMAS-style maths question.
    Simplified to look trivial so users try solving it first.
    """

    TEMPLATES = [
        "{a} + {b} - {c}",
        "{a} × {b} + {c}",
        "({a} + {b}) × {c}",
        "{a} + {b} + {c}",
        "{a} - {b} + {c}",
        "({a} × {b}) - {c}",
        "{a} + {b} ÷ {e}",
    ]

    @classmethod
    def generate(cls) -> tuple:
        template = random.choice(cls.TEMPLATES)
        nums = {
            'a': random.randint(5, 25),
            'b': random.randint(2, 12),
            'c': random.randint(1, 10),
            'e': random.choice([2, 4, 5]), # Ensuring easy division
        }
        question = template.format(**nums)

        instructions = [
            "Evaluate the expression.",
            "Solve the arithmetic challenge.",
            "Calculate the result.",
            "Evaluate the basic expression.",
        ]
        instruction = random.choice(instructions)

        return question, instruction


# -----------------------------------------------
# FAKE CRASH SCREEN
# -----------------------------------------------
class FakeCrashScreen(QWidget):
    """
    Shown after MAX_WRONG wrong answers.
    Looks like a genuine application crash.
    """

    restart_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color:{C_BG};")
        self._build()

    def _build(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(80, 100, 80, 80)
        v.setSpacing(0)
        v.setAlignment(Qt.AlignmentFlag.AlignTop)

        header = QLabel("SHURAKSHA  //  CRITICAL_ERROR  [0xC0000005]")
        header.setStyleSheet(
            f"color:{C_RED};font-size:12px;font-weight:bold;"
            f"font-family:'Consolas','Courier New',monospace;"
            f"letter-spacing:2px;"
        )
        v.addWidget(header)

        v.addSpacing(32)

        title = QLabel("Application\nEncountered an\nUnexpected Error")
        title.setStyleSheet(
            f"color:{C_WHITE};font-size:38px;font-weight:bold;"
            f"line-height:1.3;"
        )
        v.addWidget(title)

        v.addSpacing(28)

        ul = QFrame()
        ul.setFixedSize(60, 2)
        ul.setStyleSheet(f"background:{C_RED};border:none;")
        v.addWidget(ul)

        v.addSpacing(28)

        details = [
            "> Exception code:   0xC0000005  ACCESS_VIOLATION",
            "> Fault address:    0x00007FF8A3C2D190",
            "> Module:           shuraksha_core.dll",
            "> Stack trace:      [0x0001]  vault_auth.verify()",
            ">                   [0x0002]  session_manager.open()",
            ">                   [0x0003]  security_layer.check()",
        ]

        for line in details:
            lbl = QLabel(line)
            lbl.setStyleSheet(
                f"color:{C_DIM};font-size:12px;"
                f"font-family:'Consolas','Courier New',monospace;"
            )
            v.addWidget(lbl)
            v.addSpacing(4)

        v.addSpacing(40)

        h = QHBoxLayout()
        h.setSpacing(16)

        restart_btn = QPushButton("[ RESTART APPLICATION ]")
        restart_btn.setFixedSize(240, 46)
        restart_btn.setStyleSheet(BTN_PRIMARY)
        restart_btn.clicked.connect(self.restart_requested.emit)
        h.addWidget(restart_btn)

        report_btn = QPushButton("[ SEND ERROR REPORT ]")
        report_btn.setFixedSize(200, 46)
        report_btn.setStyleSheet(BTN_GHOST)
        h.addWidget(report_btn)

        h.addStretch()
        v.addLayout(h)

        v.addStretch()

        for line in [
            "> dumping_crash_report . . . done",
            "> saving_session_state . . . done",
            "> notifying_error_handler . . . done",
        ]:
            lbl = QLabel(line)
            lbl.setStyleSheet(
                f"color:{C_GHOST};font-size:11px;"
                f"font-family:'Consolas','Courier New',monospace;"
            )
            v.addWidget(lbl)


# -----------------------------------------------
# BODMAS SCREEN
# -----------------------------------------------
class BodmasScreen(QMainWindow):
    """
    The fake maths challenge screen.
    The real key is typing the DOB in DD/MM/YYYY format.
    """

    vault_access_granted = pyqtSignal()
    back_to_light        = pyqtSignal()

    def __init__(self, dob_hash: str, dob_salt: str, parent=None):
        super().__init__(parent)

        self.dob_hash  = dob_hash
        self.dob_salt  = dob_salt
        self.wrong     = 0
        self.question, self.instruction = BodmasQuestion.generate()

        self.setWindowTitle("Shuraksha")
        self.setFixedSize(WIN_W, WIN_H)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self._drag_pos = None

        self.setStyleSheet(GLOBAL_STYLE)
        self._build()

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
        self.stack.addWidget(self._build_bodmas_form())
        crash = FakeCrashScreen()
        crash.restart_requested.connect(self._restart)
        self.stack.addWidget(crash)
        v.addWidget(self.stack)

    def _build_titlebar(self):
        bar = QWidget()
        bar.setFixedHeight(42)
        bar.setStyleSheet(f"background:{C_TITLEBAR};")

        h = QHBoxLayout(bar)
        h.setContentsMargins(24, 0, 24, 0)

        h.addWidget(self._mono("[  SHR  ]", C_CYAN, 11, bold=True))
        h.addWidget(self._mono("  //  ", C_GHOST, 11))
        h.addWidget(self._mono("SECURITY VERIFICATION", C_DIM, 11))
        h.addStretch()

        back_btn = QPushButton("[ BACK TO LIGHT MODE ]")
        back_btn.setStyleSheet(
            f"QPushButton{{background:transparent;color:{C_DIM};"
            f"border:none;font-size:11px;"
            f"font-family:'Consolas','Courier New',monospace;}}"
            f"QPushButton:hover{{color:{C_AMBER};}}"
        )
        back_btn.clicked.connect(self.back_to_light.emit)
        h.addWidget(back_btn)

        return bar

    def _build_bodmas_form(self):
        widget = QWidget()
        h = QHBoxLayout(widget)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        h.addWidget(self._build_form_panel(), stretch=3)
        h.addWidget(self._build_info_panel(), stretch=2)

        return widget

    def _build_form_panel(self):
        panel = QWidget()
        v = QVBoxLayout(panel)
        v.setContentsMargins(64, 56, 48, 48)
        v.setSpacing(0)

        v.addWidget(self._mono("//  SECURITY_VERIFICATION  REQUIRED", C_CYAN, 11, bold=True))
        v.addSpacing(8)

        title = QLabel("Vault Access Challenge")
        title.setStyleSheet(f"color:{C_WHITE};font-size:26px;font-weight:bold;")
        v.addWidget(title)

        ul = QFrame()
        ul.setFixedSize(52, 2)
        ul.setStyleSheet(f"background:{C_CYAN};border:none;")
        v.addWidget(ul)
        v.addSpacing(10)

        v.addWidget(self._mono("Solve the expression to verify your identity.", C_MID, 13))
        v.addSpacing(36)

        q_frame = QFrame()
        q_frame.setObjectName("qcard")
        q_frame.setStyleSheet(
            f"QFrame#qcard{{ background:{C_CARD}; border:1px solid {C_BCARD}; border-left:3px solid {C_CYAN}; }}"
        )
        q_lay = QVBoxLayout(q_frame)
        q_lay.setContentsMargins(28, 22, 28, 22)
        q_lay.setSpacing(10)

        q_lay.addWidget(self._mono(self.instruction, C_MID, 12))
        q_lbl = QLabel(self.question)
        q_lbl.setStyleSheet(f"color:{C_WHITE};font-size:22px;font-weight:bold;font-family:'Consolas','Courier New',monospace;")
        q_lbl.setWordWrap(True)
        q_lay.addWidget(q_lbl)

        v.addWidget(q_frame)
        v.addSpacing(28)

        v.addWidget(self._mono("// ENTER ANSWER", C_MID, 12))
        v.addSpacing(8)

        self.answer_input = QLineEdit()
        self.answer_input.setPlaceholderText("type_answer_here")
        self.answer_input.setFixedHeight(58)
        self.answer_input.returnPressed.connect(self._submit)
        v.addWidget(self.answer_input)
        v.addSpacing(10)

        self.feedback_lbl = QLabel("")
        self.feedback_lbl.setStyleSheet(f"color:{C_RED};font-size:12px;font-family:'Consolas','Courier New',monospace;")
        self.feedback_lbl.setFixedHeight(20)
        v.addWidget(self.feedback_lbl)
        v.addSpacing(20)

        self.submit_btn = QPushButton("SUBMIT ANSWER  >>")
        self.submit_btn.setFixedHeight(54)
        self.submit_btn.setStyleSheet(BTN_PRIMARY)
        self.submit_btn.clicked.connect(self._submit)
        v.addWidget(self.submit_btn)
        v.addSpacing(22)

        dots_row = QHBoxLayout()
        dots_row.setSpacing(8)
        dots_row.addWidget(self._mono("// ATTEMPTS:", C_DIM, 11))

        self.attempt_dots = []
        for _ in range(MAX_WRONG):
            dot = QLabel("●")
            dot.setStyleSheet(f"color:{C_CYAN};font-size:16px;")
            self.attempt_dots.append(dot)
            dots_row.addWidget(dot)

        dots_row.addStretch()
        v.addLayout(dots_row)
        v.addStretch()

        return panel

    def _build_info_panel(self):
        panel = QWidget()
        panel.setStyleSheet(f"background:{C_PANEL}; border-left:1px solid {C_BORDER};")

        v = QVBoxLayout(panel)
        v.setContentsMargins(36, 56, 36, 48)
        v.setSpacing(0)

        v.addWidget(self._mono("//  SYSTEM_STATUS", C_CYAN, 10, bold=True))
        v.addSpacing(20)

        status_items = [
            ("VAULT_STATE",       "LOCKED",     C_RED),
            ("AUTH_LEVEL",        "LEVEL_2",    C_AMBER),
            ("ENCRYPTION",        "AES-256-GCM",C_CYAN),
            ("SESSION_ID",        self._fake_session(), C_DIM),
            ("TIMESTAMP",         self._fake_timestamp(), C_DIM),
            ("ATTEMPT_LOG",       "ACTIVE",     C_AMBER),
            ("INTRUSION_DETECT",  "ENABLED",    C_GREEN),
        ]

        for key, val, col in status_items:
            row = QHBoxLayout()
            k = self._mono(key, C_DIM, 11)
            k.setFixedWidth(160)
            row.addWidget(k)
            row.addWidget(self._mono(val, col, 11, bold=True))
            row.addStretch()
            v.addLayout(row)
            v.addSpacing(12)

        v.addSpacing(20)
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background:{C_BORDER};border:none;")
        v.addWidget(div)
        v.addSpacing(20)

        v.addWidget(self._mono("//  SESSION_TIMEOUT", C_DIM, 10, bold=True))
        v.addSpacing(8)

        self.timer_lbl = QLabel("04:59")
        self.timer_lbl.setStyleSheet(f"color:{C_AMBER};font-size:32px;font-weight:bold;font-family:'Consolas';")
        v.addWidget(self.timer_lbl)

        v.addWidget(self._mono("Session expires. Re-authentication required.", C_DIM, 11, wrap=True))

        self.countdown = 299
        self.tick_timer = QTimer(self)
        self.tick_timer.timeout.connect(self._tick_timer)
        self.tick_timer.start(1000)

        v.addSpacing(28)
        div2 = QFrame()
        div2.setFixedHeight(1)
        div2.setStyleSheet(f"background:{C_BORDER};border:none;")
        v.addWidget(div2)
        v.addSpacing(20)

        v.addWidget(self._mono("//  VERIFICATION_RULES", C_DIM, 10, bold=True))
        v.addSpacing(10)

        rules = [
            "Apply standard BODMAS/PEMDAS rules.",
            "Integer answers only. No decimals.",
            "Negative results are valid.",
            "Maximum 4 failed attempts permitted.",
            "Session locks on repeated failure.",
        ]
        for rule in rules:
            # CHANGED: Using C_WHITE for maximum readability as requested
            r_lbl = QLabel(f"  >  {rule}")
            r_lbl.setStyleSheet(
                f"color:{C_WHITE};font-size:11px;"
                f"font-family:'Consolas','Courier New',monospace;"
            )
            r_lbl.setWordWrap(True)
            v.addWidget(r_lbl)
            v.addSpacing(4)

        v.addStretch()
        return panel

    def _mono(self, text, color=C_WHITE, size=12, bold=False, wrap=False):
        l = QLabel(text)
        weight = "font-weight:bold;" if bold else ""
        l.setStyleSheet(f"color:{color};font-size:{size}px;font-family:'Consolas';{weight}")
        if wrap: l.setWordWrap(True)
        return l

    def _fake_session(self) -> str:
        return "".join(random.choices("0123456789ABCDEF", k=8))

    def _fake_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")

    def _tick_timer(self):
        self.countdown -= 1
        if self.countdown < 0: self.countdown = 299
        m, s = self.countdown // 60, self.countdown % 60
        self.timer_lbl.setText(f"{m:02d}:{s:02d}")
        colour = C_AMBER if self.countdown > 120 else ("#FF6600" if self.countdown > 30 else C_RED)
        self.timer_lbl.setStyleSheet(f"color:{colour};font-size:32px;font-weight:bold;font-family:'Consolas';")

    def _submit(self):
        answer = self.answer_input.text().strip()
        if not answer:
            self.feedback_lbl.setText("// ERROR: answer field is empty.")
            return

        if re.match(r'^\d{2}/\d{2}/\d{4}$', answer):
            try:
                correct = verify_value(answer, self.dob_hash, self.dob_salt)
            except:
                correct = False

            if correct:
                self.tick_timer.stop()
                self.vault_access_granted.emit()
            else:
                self._wrong_attempt("// ERROR: verification failed.")
        else:
            self._wrong_attempt(f"// ERROR: incorrect. Expected integer. Got: {answer[:8]}")

    def _wrong_attempt(self, message: str):
        self.wrong += 1
        self.answer_input.clear()
        for i, dot in enumerate(self.attempt_dots):
            if i < self.wrong: dot.setStyleSheet(f"color:{C_RED};font-size:16px;")

        if self.wrong >= MAX_WRONG:
            self.tick_timer.stop()
            self.stack.setCurrentIndex(1)
        else:
            rem = MAX_WRONG - self.wrong
            self.feedback_lbl.setText(f"{message} [ {rem} attempt{'s' if rem != 1 else ''} remaining ]")

    def _restart(self):
        self.wrong = 0
        self.question, self.instruction = BodmasQuestion.generate()
        self.countdown = 299
        for dot in self.attempt_dots: dot.setStyleSheet(f"color:{C_CYAN};font-size:16px;")
        self.feedback_lbl.setText("")
        self.answer_input.clear()
        self.tick_timer.start(1000)
        self.stack.setCurrentIndex(0)

    def mousePressEvent(self, event):
        if event.position().y() < 44: self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self._drag_pos:
            self.move(self.pos() + event.globalPosition().toPoint() - self._drag_pos)
            self._drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    test_dob = "01/01/2000"
    t_hash, t_salt = hash_value(test_dob)
    window = BodmasScreen(dob_hash=t_hash, dob_salt=t_salt)
    window.vault_access_granted.connect(lambda: (print("ACCESS GRANTED"), app.quit()))
    window.show()
    print(f"Test DOB: {test_dob}")
    sys.exit(app.exec())