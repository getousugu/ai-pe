from PyQt5.QtCore import QObject, pyqtSignal, QTimer

class ReminderManager(QObject):
    # UIに通知を表示させるためのシグナル
    notify_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.timers = []

    def set_reminder(self, message, seconds):
        print(f"[Reminder] Setting reminder: {message} in {seconds}s")
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self._trigger_reminder(message, timer))
        timer.start(int(seconds * 1000))
        self.timers.append(timer)
        return f"リマインダーを設定しました: 「{message}」({seconds}秒後)"

    def _trigger_reminder(self, message, timer):
        self.notify_signal.emit(f"【リマインダー】\n{message}")
        if timer in self.timers:
            self.timers.remove(timer)
