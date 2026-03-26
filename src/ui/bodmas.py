# Shuraksha - BODMAS Screen


import sys
import re
import random
import operator
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

from src.core.crypto import verify_value


# SETTINGS

MAX_WRONG = 4

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
C_GREEN    = "#00CC66"
C_AMBER    = "#FF8800"

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

# BODMAS QUESTION GENERATOR
# Generates a question AND stores the correct answer.

class BodmasQuestion:
    """
    Generates a random BODMAS arithmetic question
    and computes the correct integer answer.

    The correct math answer opens the second fake vault.
    The date of birth opens the real vault.
    """

    def __init__(self):
        self.question    = ""
        self.instruction = ""
        self.answer      = 0
        self._generate()

    def _generate(self):
        """Generate a question and compute its answer."""
        a = random.randint(12, 50)
        b = random.randint(3,  15)
        c = random.randint(2,  12)
        d = random.randint(10, 40)
        e = random.randint(2,  9)

        # Pick a template and compute its real answer
        # We use simple integer arithmetic to avoid
        # floating point confusion
        choice = random.randint(1, 5)

        if choice == 1:
            # (a + b) x c - d
            ans = (a + b) * c - d
            q   = f"( {a} + {b} ) x {c} - {d}"
        elif choice == 2:
            # a x c + b x d
            ans = a * c + b * d
            q   = f"{a} x {c} + {b} x {d}"
        elif choice == 3:
            # (a - b) x c + d
            ans = (a - b) * c + d
            q   = f"( {a} - {b} ) x {c} + {d}"
        elif choice == 4:
            # a x b - c x e + d
            ans = a * b - c * e + d
            q   = f"{a} x {b} - {c} x {e} + {d}"
        else:
            # (a + b + c) x e - d
            ans = (a + b + c) * e - d
            q   = f"( {a} + {b} + {c} ) x {e} - {d}"

        self.question = q
        self.answer   = ans

        instructions = [
            "Evaluate the expression using BODMAS rules.",
            "Solve using standard order of operations.",
            "Apply BODMAS to simplify the expression.",
            "Calculate the result. Integer answers only.",
        ]
        self.instruction = random.choice(instructions)



# FAKE CRASH SCREEN

class FakeCrashScreen(QWidget):

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

        header = QLabel(
            "SHURAKSHA  //  CRITICAL_ERROR  [0xC0000005]"
        )
        header.setStyleSheet(
            f"color:{C_RED};font-size:12px;font-weight:bold;"
            f"font-family:'Consolas','Courier New',monospace;"
            f"letter-spacing:2px;background:transparent;"
        )
        v.addWidget(header)
        v.addSpacing(32)

        title = QLabel("Application\nEncountered an\nUnexpected Error")
        title.setStyleSheet(
            f"color:{C_WHITE};font-size:38px;font-weight:bold;"
            f"background:transparent;"
        )
        v.addWidget(title)
        v.addSpacing(28)

        ul = QFrame()
        ul.setFixedSize(60, 2)
        ul.setStyleSheet(f"background:{C_RED};border:none;")
        v.addWidget(ul)
        v.addSpacing(28)

        for line in [
            "> Exception code:   0xC0000005  ACCESS_VIOLATION",
            "> Fault address:    0x00007FF8A3C2D190",
            "> Module:           shuraksha_core.dll",
            "> Stack trace:      [0x0001]  vault_auth.verify()",
            ">                   [0x0002]  session_manager.open()",
        ]:
            lbl = QLabel(line)
            lbl.setStyleSheet(
                f"color:{C_DIM};font-size:12px;"
                f"font-family:'Consolas','Courier New',monospace;"
                f"background:transparent;"
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
                f"background:transparent;"
            )
            v.addWidget(lbl)


# BODMAS SCREEN

class BodmasScreen(QMainWindow):
    """
    The fake BODMAS challenge screen.

    Three outcomes:
        1. User types correct DOB in DD/MM/YYYY format
           -> vault_access_granted emitted (opens real vault)
        2. User types the correct math answer
           -> fake_vault_access emitted (opens second fake vault)
        3. User types wrong answer
           -> wrong attempt recorded, lockout after MAX_WRONG
    """

    vault_access_granted = pyqtSignal()
    fake_vault_access    = pyqtSignal()
    back_to_light        = pyqtSignal()

    def __init__(self, dob_hash: str, dob_salt: str,
                 parent=None):
        super().__init__(parent)

        self.dob_hash    = dob_hash
        self.dob_salt    = dob_salt
        self.wrong       = 0

        # Generate a question and store the correct answer
        self.bodmas      = BodmasQuestion()

        self.setWindowTitle("Shuraksha")
        self.setFixedSize(1100, 720)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self._drag_pos = None

        self.setStyleSheet(GLOBAL_STYLE)
        self._build()


# LAYOUT


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
        self.stack.addWidget(self._build_bodmas_form())  # 0
        crash = FakeCrashScreen()
        crash.restart_requested.connect(self._restart)
        self.stack.addWidget(crash)                      # 1
        v.addWidget(self.stack)

    def _build_titlebar(self):
        bar = QWidget()
        bar.setFixedHeight(42)
        bar.setStyleSheet(f"background:{C_TITLEBAR};")

        h = QHBoxLayout(bar)
        h.setContentsMargins(24, 0, 24, 0)

        for text, color in [
            ("[  SHR  ]", C_CYAN),
            ("  //  ",    C_GHOST),
            ("SECURITY VERIFICATION", C_DIM),
        ]:
            lbl = QLabel(text)
            lbl.setStyleSheet(
                f"color:{color};font-size:11px;"
                f"font-family:'Consolas','Courier New',monospace;"
                f"background:transparent;"
            )
            h.addWidget(lbl)

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
        h      = QHBoxLayout(widget)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        h.addWidget(self._build_form_panel(), stretch=3)
        h.addWidget(self._build_info_panel(), stretch=2)

        return widget

    def _build_form_panel(self):
        panel = QWidget()
        panel.setStyleSheet(f"background:{C_BG};")

        v = QVBoxLayout(panel)
        v.setContentsMargins(64, 56, 48, 48)
        v.setSpacing(0)

        # Header
        badge = QLabel("//  SECURITY_VERIFICATION  REQUIRED")
        badge.setStyleSheet(
            f"color:{C_CYAN};font-size:11px;font-weight:bold;"
            f"font-family:'Consolas','Courier New',monospace;"
            f"background:transparent;"
        )
        v.addWidget(badge)
        v.addSpacing(8)

        title = QLabel("Vault Access Challenge")
        title.setStyleSheet(
            f"color:{C_WHITE};font-size:26px;font-weight:bold;"
            f"background:transparent;"
        )
        v.addWidget(title)

        ul = QFrame()
        ul.setFixedSize(52, 2)
        ul.setStyleSheet(f"background:{C_CYAN};border:none;")
        v.addWidget(ul)
        v.addSpacing(10)

        sub = QLabel("Solve the expression to verify your identity.")
        sub.setStyleSheet(
            f"color:{C_MID};font-size:13px;background:transparent;"
        )
        v.addWidget(sub)
        v.addSpacing(36)

        # Question card
        q_frame = QFrame()
        q_frame.setObjectName("qcard")
        q_frame.setStyleSheet(
            "QFrame#qcard{"
            f"  background:{C_CARD};"
            f"  border:1px solid {C_BCARD};"
            f"  border-left:3px solid {C_CYAN};"
            "}"
            "QFrame#qcard QLabel{"
            "  border:none;background:transparent;"
            "}"
        )
        ql = QVBoxLayout(q_frame)
        ql.setContentsMargins(28, 22, 28, 22)
        ql.setSpacing(10)

        instr = QLabel(self.bodmas.instruction)
        instr.setStyleSheet(
            f"color:{C_MID};font-size:12px;"
            f"font-family:'Consolas','Courier New',monospace;"
            f"background:transparent;"
        )
        ql.addWidget(instr)

        q_lbl = QLabel(self.bodmas.question)
        q_lbl.setStyleSheet(
            f"color:{C_WHITE};font-size:22px;font-weight:bold;"
            f"font-family:'Consolas','Courier New',monospace;"
            f"background:transparent;"
        )
        q_lbl.setWordWrap(True)
        ql.addWidget(q_lbl)

        v.addWidget(q_frame)
        v.addSpacing(28)

        # Answer input
        ans_lbl = QLabel("// ENTER ANSWER")
        ans_lbl.setStyleSheet(
            f"color:{C_MID};font-size:12px;"
            f"font-family:'Consolas','Courier New',monospace;"
            f"background:transparent;"
        )
        v.addWidget(ans_lbl)
        v.addSpacing(8)

        self.answer_input = QLineEdit()
        self.answer_input.setPlaceholderText("type_answer_here")
        self.answer_input.setFixedHeight(58)
        self.answer_input.returnPressed.connect(self._submit)
        v.addWidget(self.answer_input)
        v.addSpacing(10)

        # Feedback label
        self.feedback_lbl = QLabel("")
        self.feedback_lbl.setStyleSheet(
            f"color:{C_RED};font-size:12px;"
            f"font-family:'Consolas','Courier New',monospace;"
            f"background:transparent;"
        )
        self.feedback_lbl.setFixedHeight(20)
        v.addWidget(self.feedback_lbl)
        v.addSpacing(20)

        # Submit button
        self.submit_btn = QPushButton("SUBMIT ANSWER  >>")
        self.submit_btn.setFixedHeight(54)
        self.submit_btn.setStyleSheet(BTN_PRIMARY)
        self.submit_btn.clicked.connect(self._submit)
        v.addWidget(self.submit_btn)
        v.addSpacing(22)

        # Attempt dots
        dots_row = QHBoxLayout()
        dots_row.setSpacing(8)

        dots_lbl = QLabel("// ATTEMPTS:")
        dots_lbl.setStyleSheet(
            f"color:{C_DIM};font-size:11px;"
            f"font-family:'Consolas','Courier New',monospace;"
            f"background:transparent;"
        )
        dots_row.addWidget(dots_lbl)

        self.attempt_dots = []
        for _ in range(MAX_WRONG):
            dot = QLabel("●")
            dot.setStyleSheet(
                f"color:{C_CYAN};font-size:16px;"
                f"background:transparent;"
            )
            self.attempt_dots.append(dot)
            dots_row.addWidget(dot)

        dots_row.addStretch()
        v.addLayout(dots_row)
        v.addStretch()

        return panel

    def _build_info_panel(self):
        panel = QWidget()
        panel.setStyleSheet(
            f"background:{C_PANEL};"
            f"border-left:1px solid {C_BORDER};"
        )

        v = QVBoxLayout(panel)
        v.setContentsMargins(36, 56, 36, 48)
        v.setSpacing(0)

        def mono(text, color, size=11, bold=False):
            l = QLabel(text)
            w = "font-weight:bold;" if bold else ""
            l.setStyleSheet(
                f"color:{color};font-size:{size}px;"
                f"font-family:'Consolas','Courier New',monospace;"
                f"{w}background:transparent;"
            )
            return l

        v.addWidget(mono("//  SYSTEM_STATUS", C_CYAN, 10, bold=True))
        v.addSpacing(20)

        status_items = [
            ("VAULT_STATE",      "LOCKED",      C_RED),
            ("AUTH_LEVEL",       "LEVEL_2",     C_AMBER),
            ("ENCRYPTION",       "AES-256-GCM", C_CYAN),
            ("INTRUSION_DETECT", "ENABLED",     C_GREEN),
        ]

        for key, val, col in status_items:
            row = QHBoxLayout()
            row.setSpacing(0)

            k = mono(key, C_DIM, 11)
            k.setFixedWidth(160)
            row.addWidget(k)

            v_lbl = mono(val, col, 11, bold=True)
            row.addWidget(v_lbl)
            row.addStretch()

            v.addLayout(row)
            v.addSpacing(12)

        v.addSpacing(20)

        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background:{C_BORDER};border:none;")
        v.addWidget(div)
        v.addSpacing(20)

        v.addWidget(mono("//  SESSION_TIMEOUT", C_DIM, 10, bold=True))
        v.addSpacing(8)

        self.timer_lbl = QLabel("04:59")
        self.timer_lbl.setStyleSheet(
            f"color:{C_AMBER};font-size:32px;font-weight:bold;"
            f"font-family:'Consolas','Courier New',monospace;"
            f"background:transparent;"
        )
        v.addWidget(self.timer_lbl)

        v.addWidget(mono(
            "Session expires. Re-authentication required.",
            C_DIM, 11, bold=False
        ))

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

        v.addWidget(mono(
            "//  VERIFICATION_RULES", C_DIM, 10, bold=True
        ))
        v.addSpacing(10)

        rules = [
            "Apply standard BODMAS rules.",
            "Integer answers only. No decimals.",
            "Negative results are valid.",
            "Maximum 4 failed attempts permitted.",
            "Session locks on repeated failure.",
        ]
        for rule in rules:
            r = QLabel(f"  >  {rule}")
            r.setStyleSheet(
                f"color:{C_GHOST};font-size:11px;"
                f"font-family:'Consolas','Courier New',monospace;"
                f"background:transparent;"
            )
            r.setWordWrap(True)
            v.addWidget(r)
            v.addSpacing(4)

        v.addStretch()
        return panel


# TIMER


    def _tick_timer(self):
        self.countdown -= 1
        if self.countdown < 0:
            self.countdown = 299

        m = self.countdown // 60
        s = self.countdown % 60
        self.timer_lbl.setText(f"{m:02d}:{s:02d}")

        if self.countdown > 120:
            colour = C_AMBER
        elif self.countdown > 30:
            colour = "#FF6600"
        else:
            colour = C_RED

        self.timer_lbl.setStyleSheet(
            f"color:{colour};font-size:32px;font-weight:bold;"
            f"font-family:'Consolas','Courier New',monospace;"
            f"background:transparent;"
        )


# SUBMISSION LOGIC
   

    def _submit(self):
        """
        Three possible outcomes when Submit is pressed:

        1. Input matches DD/MM/YYYY date format AND
           matches the stored DOB hash
           -> emit vault_access_granted (REAL vault)

        2. Input is a number AND matches the correct
           math answer for the displayed question
           -> emit fake_vault_access (SECOND fake vault)

        3. Input is wrong (neither correct DOB nor
           correct math answer)
           -> wrong attempt, lockout after MAX_WRONG
        """
        answer = self.answer_input.text().strip()

        if not answer:
            self.feedback_lbl.setText(
                "// ERROR: answer field is empty."
            )
            return

        # ---- Check if input is a date (DD/MM/YYYY) ----
        if re.match(r'^\d{2}/\d{2}/\d{4}$', answer):
            try:
                correct_dob = verify_value(
                    answer, self.dob_hash, self.dob_salt
                )
            except Exception:
                correct_dob = False

            if correct_dob:
                # REAL vault opens
                self.tick_timer.stop()
                self.vault_access_granted.emit()
                return
            else:
                # Wrong date entered
                self._wrong_attempt(
                    "// ERROR: verification failed."
                )
                return

        # ---- Check if input is the correct math answer ----
        try:
            numeric_input = int(answer.strip())
            if numeric_input == self.bodmas.answer:
                # SECOND fake vault opens
                self.tick_timer.stop()
                self.fake_vault_access.emit()
                return
            else:
                # Wrong math answer
                self._wrong_attempt(
                    f"// ERROR: incorrect.  "
                    f"Expected integer. Got: {answer[:8]}"
                )
        except ValueError:
            # Not a number and not a date
            self._wrong_attempt(
                f"// ERROR: invalid input format."
            )

    def _wrong_attempt(self, message: str):
        self.wrong += 1
        self.answer_input.clear()

        for i, dot in enumerate(self.attempt_dots):
            if i < self.wrong:
                dot.setStyleSheet(
                    f"color:{C_RED};font-size:16px;"
                    f"background:transparent;"
                )

        if self.wrong >= MAX_WRONG:
            self.tick_timer.stop()
            self.stack.setCurrentIndex(1)
        else:
            remaining = MAX_WRONG - self.wrong
            self.feedback_lbl.setText(
                f"{message}  "
                f"[ {remaining} attempt"
                f"{'s' if remaining != 1 else ''} remaining ]"
            )

    def _restart(self):
        self.wrong   = 0
        self.bodmas  = BodmasQuestion()
        self.countdown = 299

        for dot in self.attempt_dots:
            dot.setStyleSheet(
                f"color:{C_CYAN};font-size:16px;"
                f"background:transparent;"
            )

        self.feedback_lbl.setText("")
        self.answer_input.clear()
        self.tick_timer.start(1000)
        self.stack.setCurrentIndex(0)


# WINDOW DRAG


    def mousePressEvent(self, event):
        if event.position().y() < 44:
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



# ENTRY POINT

if __name__ == '__main__':
    from src.core.crypto import hash_value

    test_dob         = "01/01/2000"
    test_hash, test_salt = hash_value(test_dob)

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = BodmasScreen(
        dob_hash=test_hash,
        dob_salt=test_salt
    )

    def on_real():
        print("REAL VAULT ACCESS GRANTED")
        app.quit()

    def on_fake():
        print("FAKE VAULT 2 ACCESS GRANTED")
        app.quit()

    window.vault_access_granted.connect(on_real)
    window.fake_vault_access.connect(on_fake)
    window.show()

    q = BodmasQuestion()
    print(f"Test DOB:   {test_dob}")
    print(f"Question:   {q.question}")
    print(f"Math answer: {q.answer}")

    sys.exit(app.exec())