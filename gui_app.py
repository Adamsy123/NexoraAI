import sys
import os
import math
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QFrame, QSystemTrayIcon, QMenu
)
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QPixmap, QIcon

# Import your existing AssistantCore backend
from main import AssistantCore

class AssistantWorker(QThread):
    status_updated = pyqtSignal(str, str)  # (status_text, state_type)

    def __init__(self, core):
        super().__init__()
        self.core = core

    def run(self):
        self.status_updated.emit(f"✨ {self.core.assistant_name} is online and ready.", "idle")
        
        while self.core.running:
            try:
                self.status_updated.emit("🎙️ NEXORA IS LISTENING...", "listening")
                audio_file = self.core.record_audio()
                if not audio_file:
                    continue
                
                self.status_updated.emit("📝 TRANSCRIBING AUDIO...", "thinking")
                user_text = self.core.transcribe_audio(audio_file)
                if not user_text.strip():
                    continue
                
                self.status_updated.emit(f"🤖 THINKING: \"{user_text}\"", "thinking")
                reply_text = self.core.get_gpt_response(user_text)
                
                self.status_updated.emit(f"🗣️ NEXORA IS SPEAKING...", "speaking")
                self.core.speak_response(reply_text)
                
                self.status_updated.emit(f"✨ {reply_text}", "idle")
            except Exception as e:
                self.status_updated.emit(f"❌ ERROR: {str(e)}", "error")

class WaveformVisualizer(QWidget):
    """Custom animated HUD waveform / audio visualizer widget."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(90)
        self.phase = 0.0
        self.state = "idle"
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_wave)
        self.timer.start(30)

    def set_state(self, state):
        self.state = state

    def update_wave(self):
        self.phase += 0.15
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        mid_y = height / 2

        # Draw glowing background HUD panel
        painter.setPen(QPen(QColor(0, 245, 255, 100), 1.5))
        painter.setBrush(QBrush(QColor(5, 10, 25, 200)))
        painter.drawRoundedRect(0, 0, width, height, 12, 12)

        if self.state == "speaking":
            color = QColor(0, 255, 204, 230)
            amp_multiplier = 30.0
        elif self.state == "listening":
            color = QColor(255, 0, 128, 230)
            amp_multiplier = 22.0
        elif self.state == "thinking":
            color = QColor(0, 180, 255, 200)
            amp_multiplier = 12.0
        else:
            color = QColor(0, 245, 255, 100)
            amp_multiplier = 5.0

        for wave_idx in range(3):
            alpha = int(255 - (wave_idx * 60))
            wave_color = QColor(color.red(), color.green(), color.blue(), max(alpha, 50))
            painter.setPen(QPen(wave_color, 2 - 0.4 * wave_idx))
            
            points = []
            for x in range(0, width, 4):
                frequency = 0.03 + (wave_idx * 0.01)
                y = mid_y + (math.sin(x * frequency + self.phase + wave_idx) * math.cos((x * frequency + self.phase + wave_idx) * 0.5)) * amp_multiplier
                points.append((x, y))
            
            for i in range(len(points) - 1):
                painter.drawLine(int(points[i][0]), int(points[i][1]), int(points[i+1][0]), int(points[i+1][1]))

class NexoraWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.assistant_core = AssistantCore()
        self.assistant_core.assistant_name = "Nexora"
        
        self.init_ui()
        self.init_system_tray()
        self.start_assistant_thread()

    def init_ui(self):
        self.setWindowTitle("Nexora - Advanced AI Assistant")
        self.setFixedSize(740, 620)

        # Set application icon if available
        if os.path.exists("nexora_avatar.jfif"):
            self.setWindowIcon(QIcon("nexora_avatar.jfif"))

        self.setStyleSheet("""
            QMainWindow {
                background-color: #080b12;
            }
            QLabel {
                color: #c0d8ff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00f5ff, stop:1 #0077ff);
                color: #050811;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
                padding: 10px 20px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background-color: #00ffff;
            }
            QFrame#card {
                background-color: #0d1322;
                border: 1px solid #00f5ff55;
                border-radius: 14px;
            }
        """)

        central_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        # Title Header
        self.title_label = QLabel("NEXORA AI // NEURAL INTERFACE")
        self.title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("color: #00f5ff; letter-spacing: 2px;")
        main_layout.addWidget(self.title_label)

        # Central Robotic Card
        card_frame = QFrame()
        card_frame.setObjectName("card")
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(15, 15, 15, 15)
        card_layout.setSpacing(10)

        # Robot Visual / Avatar Image Header
        self.avatar_label = QLabel()
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        avatar_path = None
        for filename in ["nexora_avatar.png", "nexora_avatar.jpg", "nexora_avatar.jpeg", "nexora_avatar.jfif"]:
            if os.path.exists(filename):
                avatar_path = filename
                break

        if avatar_path:
            pixmap = QPixmap(avatar_path).scaled(640, 220, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.avatar_label.setPixmap(pixmap)
        else:
            self.avatar_label.setText("[ Place 'nexora_avatar.jfif' in root directory ]")
            self.avatar_label.setStyleSheet("color: #00f5ff; font-style: italic;")
        card_layout.addWidget(self.avatar_label)

        # Status Banner
        self.status_label = QLabel("INITIALIZING NEURAL CORE...")
        self.status_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #00ffcc;")
        card_layout.addWidget(self.status_label)

        # Live Animated Audio Visualizer
        self.visualizer = WaveformVisualizer()
        card_layout.addWidget(self.visualizer)

        # Dialogue / Speech Box
        self.dialogue_label = QLabel("Hello owner! I am Nexora, ready to assist. You can ask me to open apps, check your system status, or take a screenshot.")
        self.dialogue_label.setFont(QFont("Segoe UI", 11))
        self.dialogue_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dialogue_label.setWordWrap(True)
        self.dialogue_label.setStyleSheet("color: #e0f0ff; background-color: #050811; padding: 12px; border-radius: 8px; border: 1px solid #1a2942;")
        card_layout.addWidget(self.dialogue_label)

        card_frame.setLayout(card_layout)
        main_layout.addWidget(card_frame)

        # Bottom Control Layout
        bottom_layout = QHBoxLayout()
        bottom_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.exit_btn = QPushButton("SHUT DOWN NEXORA")
        self.exit_btn.clicked.connect(self.close)
        bottom_layout.addWidget(self.exit_btn)

        main_layout.addLayout(bottom_layout)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def init_system_tray(self):
        """Creates a system tray icon with a menu to restore or quit Nexora."""
        icon_file = "nexora_avatar.jfif" if os.path.exists("nexora_avatar.jfif") else "nexora_avatar.png"
        self.tray_icon = QSystemTrayIcon(QIcon(icon_file), self)
        
        tray_menu = QMenu()
        restore_action = tray_menu.addAction("Open Nexora HUD")
        restore_action.triggered.connect(self.showNormal)
        
        quit_action = tray_menu.addAction("Shut Down")
        quit_action.triggered.connect(self.close)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def start_assistant_thread(self):
        self.worker = AssistantWorker(self.assistant_core)
        self.worker.status_updated.connect(self.update_ui_state)
        self.worker.start()

    def update_ui_state(self, message, state):
        self.status_label.setText(message)
        self.visualizer.set_state(state)
        
        if state == "idle" or state == "speaking":
            clean_msg = message.replace("✨ ", "").replace("🗣️ ", "")
            self.dialogue_label.setText(clean_msg)

    def closeEvent(self, event):
        self.assistant_core.running = False
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NexoraWindow()
    window.show()
    sys.exit(app.exec())