import signal
import sys
from pathlib import Path

from PyQt6.QtCore import QProcess, Qt, QTimer
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

if getattr(sys, "_MEIPASS", None):
    ASSETS_DIR = Path(sys._MEIPASS) / "assets"
else:
    ASSETS_DIR = Path(__file__).parent / "assets"

DURATIONS = [
    ("Forever", None),
    ("1 Hour", 3600),
    ("3 Hours", 10800),
    ("5 Hours", 18000),
    ("8 Hours", 28800),
    ("24 Hours", 86400),
]



def _format_remaining(seconds: int) -> str:
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"Remaining: {h}h {m:02d}m {s:02d}s"


class CaffeinateApp:
    def __init__(self):
        self.process: QProcess | None = None
        self.remaining: int | None = None
        self.active_action: QAction | None = None

        self.icon_idle = QIcon(str(ASSETS_DIR / "logo_off.png"))
        self.icon_active = QIcon(str(ASSETS_DIR / "logo_on.png"))

        self.tray = QSystemTrayIcon()
        self.tray.setIcon(self.icon_idle)

        self.menu = QMenu()
        self.status_action = self.menu.addAction(self.icon_idle, "Idle")
        self.status_action.setEnabled(False)
        self.menu.addSeparator()

        self.duration_actions: list[QAction] = []
        for label, seconds in DURATIONS:
            action = self.menu.addAction(f"\u25CB {label}")
            action.setCheckable(True)
            action.setData(seconds)
            action.triggered.connect(lambda checked, a=action: self._on_toggle(a, checked))
            self.duration_actions.append(action)

        self.menu.addSeparator()
        quit_action = self.menu.addAction("Quit")
        quit_action.triggered.connect(self._quit)

        self.tray.setContextMenu(self.menu)
        self.tray.show()

        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)

        # Start with 24 Hours on by default
        default_action = self.duration_actions[-1]
        default_action.setChecked(True)
        self._on_toggle(default_action, True)

    def _on_toggle(self, action: QAction, checked: bool):
        # Stop process/timer without resetting UI (we'll update it below)
        self.timer.stop()
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.terminate()
            self.process.waitForFinished(3000)
        self.process = None
        self.remaining = None

        if not checked:
            self.active_action = None
            self._reset_ui()
            return

        for a in self.duration_actions:
            if a is not action:
                a.setChecked(False)

        self.active_action = action
        self._update_action_icons()
        seconds = action.data()

        self.process = QProcess()
        self.process.finished.connect(self._on_process_finished)

        args = ["-dis"]
        if seconds is not None:
            args.extend(["-t", str(seconds)])
            self.remaining = seconds
            self.status_action.setIcon(self.icon_active)
            self.status_action.setText(_format_remaining(seconds))
            self.timer.start()
        else:
            self.remaining = None
            self.status_action.setIcon(self.icon_active)
            self.status_action.setText("Active (Forever)")

        self.process.start("/usr/bin/caffeinate", args)
        self.tray.setIcon(self.icon_active)

    def _update_action_icons(self):
        for i, (label, _seconds) in enumerate(DURATIONS):
            a = self.duration_actions[i]
            prefix = "\u25CF" if a.isChecked() else "\u25CB"
            a.setText(f"{prefix} {label}")

    def _stop_caffeinate(self):
        self.timer.stop()
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.terminate()
            self.process.waitForFinished(3000)
        self.process = None
        self.remaining = None
        self._reset_ui()

    def _reset_ui(self):
        self.tray.setIcon(self.icon_idle)
        self.status_action.setIcon(self.icon_idle)
        self.status_action.setText("Idle")
        if self.active_action:
            self.active_action.setChecked(False)
            self.active_action = None
        self._update_action_icons()

    def _on_process_finished(self):
        self.timer.stop()
        self.process = None
        self.remaining = None
        self._reset_ui()

    def _tick(self):
        if self.remaining is not None and self.remaining > 0:
            self.remaining -= 1
            self.status_action.setText(_format_remaining(self.remaining))
            if self.remaining <= 0:
                self.timer.stop()

    def _quit(self):
        self._stop_caffeinate()
        QApplication.quit()


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    _caffeinate = CaffeinateApp()  # noqa: F841

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
