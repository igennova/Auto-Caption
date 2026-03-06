import sys
import os
import tempfile
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
                             QProgressBar, QLabel, QFileDialog, QHeaderView, QMessageBox,
                             QComboBox, QSpinBox, QGroupBox, QSplitter)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont

from whisper_engine import transcribe_video, segments_to_srt
from srt_editor import parse_srt, save_srt, create_karaoke_srt
from ffmpeg_engine import burn_subtitles, preview_subtitles, extract_thumbnail

class TranscriptionThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path

    def run(self):
        try:
            segments = transcribe_video(self.video_path, model_size="small")
            srt_content = segments_to_srt(segments)
            self.finished.emit(srt_content)
        except Exception as e:
            self.error.emit(str(e))

class ExportThread(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, video_path, srt_path, output_path, font=None, size=None, color=None, margin_v=None, alignment=2):
        super().__init__()
        self.video_path = video_path
        self.srt_path = srt_path
        self.output_path = output_path
        self.font = font
        self.size = size
        self.color = color
        self.margin_v = margin_v
        self.alignment = alignment

    def run(self):
        try:
            burn_subtitles(self.video_path, self.srt_path, self.output_path, self.font, self.size, self.color, self.margin_v, self.alignment)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class ThumbnailThread(QThread):
    finished = pyqtSignal(str)
    
    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path
        
    def run(self):
        temp_dir = tempfile.gettempdir()
        thumb_path = os.path.join(temp_dir, "thumb.jpg")
        try:
            extract_thumbnail(self.video_path, thumb_path)
            self.finished.emit(thumb_path)
        except Exception:
            self.finished.emit("")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auto Caption MVP -> Pro")
        self.setMinimumSize(1000, 700)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
            }
            QLabel {
                color: #FFFFFF;
                font-family: 'Helvetica Neue', Arial, sans-serif;
                font-size: 14px;
            }
            QGroupBox {
                border: 1px solid #333333;
                border-radius: 8px;
                margin-top: 20px;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #2D63ED;
                color: white;
                border-radius: 6px;
                padding: 10px 15px;
                font-size: 14px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #1A4BCC;
            }
            QPushButton:disabled {
                background-color: #333333;
                color: #777777;
            }
            QPushButton#exportBtn {
                background-color: #E63946;
            }
            QPushButton#exportBtn:hover {
                background-color: #B22B36;
            }
            QPushButton#generateBtn {
                background-color: #2A9D8F;
            }
            QPushButton#generateBtn:hover {
                background-color: #1E6E64;
            }
            QTableWidget {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #333333;
                border-radius: 8px;
                gridline-color: #333333;
                selection-background-color: #2D63ED;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #252525;
                color: #FFFFFF;
                padding: 5px;
                border: 1px solid #333333;
                font-weight: bold;
            }
            QProgressBar {
                border: 1px solid #333333;
                border-radius: 4px;
                text-align: center;
                background-color: #1E1E1E;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #2D63ED;
                border-radius: 4px;
            }
        """)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.splitter)
        
        self.left_panel = QWidget()
        self.left_panel.setMinimumWidth(350)
        self.left_layout = QVBoxLayout(self.left_panel)
        self.left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.left_layout.setContentsMargins(20, 20, 20, 20)
        self.left_layout.setSpacing(15)

        self.thumbnail_label = QLabel("No Video Selected")
        self.thumbnail_label.setMinimumSize(320, 180)
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setStyleSheet("background-color: #000000; border-radius: 8px; border: 1px solid #333;")
        self.left_layout.addWidget(self.thumbnail_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.import_btn = QPushButton("📂 Import Video")
        self.generate_btn = QPushButton("✨ Generate Captions (Whisper)")
        self.generate_btn.setObjectName("generateBtn")
        self.generate_btn.setEnabled(False)
        
        self.left_layout.addWidget(self.import_btn)
        self.left_layout.addWidget(self.generate_btn)
        
        self.status_label = QLabel("Awaiting Import...")
        self.status_label.setStyleSheet("color: #AAAAAA; font-size: 12px; margin-top: 5px;")
        self.left_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        self.left_layout.addWidget(self.progress_bar)
        
        self.style_group = QGroupBox("🎨 Caption Styling")
        self.style_layout = QVBoxLayout()

        row1 = QHBoxLayout()
        self.font_combo = QComboBox()
        fonts = [
            "Impact", "Arial", "Helvetica", "Courier New", "Times New Roman",
            "Verdana", "Tahoma", "Trebuchet MS", "Futura", "Avenir Next",
            "Chalkboard SE", "Comic Sans MS"
        ]
        self.font_combo.addItems(fonts)
        

        
        self.size_spin = QSpinBox()
        self.size_spin.setRange(10, 100)
        self.size_spin.setValue(24)
        row1.addWidget(QLabel("Font:"))
        row1.addWidget(self.font_combo)
        row1.addWidget(QLabel("Size:"))
        row1.addWidget(self.size_spin)
        
        row2 = QHBoxLayout()
        self.color_combo = QComboBox()
        self.color_combo.addItem("Yellow", "&H0000FFFF")
        self.color_combo.addItem("White", "&H00FFFFFF")
        self.color_combo.addItem("Red", "&H000000FF")
        self.color_combo.addItem("Green", "&H0000FF00")
        self.color_combo.addItem("Blue", "&H00FF0000")
        self.margin_spin = QSpinBox()
        self.margin_spin.setRange(0, 500)
        self.margin_spin.setValue(40)
        
        self.align_combo = QComboBox()
        self.align_combo.addItem("Bottom", 2)
        self.align_combo.addItem("Top", 8)
        self.align_combo.addItem("Middle", 5)
        
        row2.addWidget(QLabel("Color:"))
        row2.addWidget(self.color_combo)
        row2.addWidget(QLabel("Position:"))
        row2.addWidget(self.align_combo)
        row2.addWidget(QLabel("Margin V:"))
        row2.addWidget(self.margin_spin)

        row3 = QHBoxLayout()
        self.karaoke_combo = QComboBox()
        self.karaoke_combo.addItem("None", None)
        self.karaoke_combo.addItem("Pink", "#FF00FF")
        self.karaoke_combo.addItem("Yellow", "#FFFF00")
        self.karaoke_combo.addItem("Green", "#00FF00")
        self.karaoke_combo.addItem("Red", "#FF0000")
        
        row3.addWidget(QLabel("Highlight/Karaoke:"))
        row3.addWidget(self.karaoke_combo)
        row3.addStretch()

        self.style_layout.addLayout(row1)
        self.style_layout.addLayout(row2)
        self.style_layout.addLayout(row3)
        self.style_group.setLayout(self.style_layout)
        self.left_layout.addWidget(self.style_group)
        
        self.left_layout.addStretch()

        self.export_group = QGroupBox("🎬 Export Actions")
        self.export_layout = QVBoxLayout()
        self.save_srt_btn = QPushButton("💾 Save .SRT File")
        self.preview_btn = QPushButton("▶️ Preview Video")
        self.export_btn = QPushButton("🔥 Export Final Video")
        self.export_btn.setObjectName("exportBtn")
        
        self.export_layout.addWidget(self.save_srt_btn)
        self.export_layout.addWidget(self.preview_btn)
        self.export_layout.addWidget(self.export_btn)
        self.export_group.setLayout(self.export_layout)
        self.left_layout.addWidget(self.export_group)

        self.splitter.addWidget(self.left_panel)
        
        self.caption_table = QTableWidget(0, 3)
        self.caption_table.setHorizontalHeaderLabels(["Start", "End", "Caption Text"])
        self.caption_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.caption_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.caption_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.caption_table.verticalHeader().setVisible(False)
        
        self.splitter.addWidget(self.caption_table)
        
        self.splitter.setSizes([500, 500])
        

        self.import_btn.clicked.connect(self.import_video)
        self.generate_btn.clicked.connect(self.generate_captions)
        self.save_srt_btn.clicked.connect(self.save_srt_action)
        self.preview_btn.clicked.connect(self.preview_video)
        self.export_btn.clicked.connect(self.export_video)


        self.video_path = None
        self.current_srt_path = None
        self.transcription_thread = None
        self.export_thread = None
        self.thumb_thread = None
        
    def import_video(self):
        file_dialog = QFileDialog()
        video_file, _ = file_dialog.getOpenFileName(self, "Open Video", "", "Video Files (*.mp4 *.mkv *.avi *.mov)")
        if video_file:
            self.video_path = video_file
            self.status_label.setText(f"Loaded: {os.path.basename(self.video_path)}")

            self.caption_table.setRowCount(0)
            self.current_srt_path = None
            self.generate_btn.setEnabled(True)
            self.thumbnail_label.setText("Loading Preview...")
            
            self.thumb_thread = ThumbnailThread(self.video_path)
            self.thumb_thread.finished.connect(self.on_thumbnail_ready)
            self.thumb_thread.start()
            
    def on_thumbnail_ready(self, thumb_path):
        if thumb_path and os.path.exists(thumb_path):
            pixmap = QPixmap(thumb_path)
            self.thumbnail_label.setPixmap(pixmap.scaled(
                320, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.thumbnail_label.setText("Could not load preview")
            
    def generate_captions(self):
        if not self.video_path:
            return
            
        self.status_label.setText("🧠 Listening to Audio... (This may take a minute)")
        self.progress_bar.setVisible(True)
        self.generate_btn.setEnabled(False)
        self.import_btn.setEnabled(False)
        
        self.transcription_thread = TranscriptionThread(self.video_path)
        self.transcription_thread.finished.connect(self.on_transcription_finished)
        self.transcription_thread.error.connect(self.on_transcription_error)
        self.transcription_thread.start()

    def on_transcription_finished(self, srt_content):
        self.progress_bar.setVisible(False)
        self.generate_btn.setEnabled(True)
        self.import_btn.setEnabled(True)
        self.status_label.setText("✅ Transcription complete. You can now edit text on the right.")
        
        subtitles = parse_srt(srt_content)
        self.load_table(subtitles)

    def on_transcription_error(self, error_msg):
        self.progress_bar.setVisible(False)
        self.generate_btn.setEnabled(True)
        self.import_btn.setEnabled(True)
        self.status_label.setText("❌ Error generating captions.")
        QMessageBox.critical(self, "Error", f"Failed to generate captions:\n{error_msg}")

    def load_table(self, subtitles):
        self.caption_table.setRowCount(0)
        for i, sub in enumerate(subtitles):
            self.caption_table.insertRow(i)
            self.caption_table.setItem(i, 0, QTableWidgetItem(sub['start']))
            self.caption_table.setItem(i, 1, QTableWidgetItem(sub['end']))
            self.caption_table.setItem(i, 2, QTableWidgetItem(sub['text']))

    def get_subtitles_from_table(self):
        subtitles = []
        for row in range(self.caption_table.rowCount()):
            subtitles.append({
                "index": str(row + 1),
                "start": self.caption_table.item(row, 0).text(),
                "end": self.caption_table.item(row, 1).text(),
                "text": self.caption_table.item(row, 2).text()
            })
        return subtitles
        
    def save_srt_action(self):
        if self.caption_table.rowCount() == 0:
            QMessageBox.warning(self, "Error", "No captions generated yet.")
            return
            
        file_dialog = QFileDialog()
        srt_file, _ = file_dialog.getSaveFileName(self, "Save SRT", "", "SRT Files (*.srt)")
        if srt_file:
            subs = self.get_subtitles_from_table()
            save_srt(subs, srt_file)
            self.current_srt_path = srt_file
            self.status_label.setText(f"✅ Saved SRT: {os.path.basename(srt_file)}")
            
    def get_escaped_srt(self):
        """ Ensure Table -> Temp File -> Correct Path happens smoothly. """
        base_dir = os.path.dirname(self.video_path)
        self.current_srt_path = os.path.join(base_dir, "temp.srt")
        subs = self.get_subtitles_from_table()
        
        highlight_color = self.karaoke_combo.currentData()
        if highlight_color:
            create_karaoke_srt(subs, self.current_srt_path, highlight_color)
        else:
            save_srt(subs, self.current_srt_path)
            
        escaped_srt = self.current_srt_path.replace("\\", "/").replace(":", "\\:")
        return escaped_srt

    def preview_video(self):
        if not self.video_path or self.caption_table.rowCount() == 0:
            QMessageBox.warning(self, "Error", "Import video and generate captions first.")
            return
            
        escaped_srt = self.get_escaped_srt()
        font = self.font_combo.currentText()
        size = self.size_spin.value()
        color = self.color_combo.currentData()
        margin_v = self.margin_spin.value()
        alignment = self.align_combo.currentData()
        
        self.status_label.setText("▶️ Opening preview player...")
        preview_subtitles(
            self.video_path, escaped_srt,
            font, size, color, margin_v, alignment
        )
        
    def export_video(self):
        if not self.video_path or self.caption_table.rowCount() == 0:
            QMessageBox.warning(self, "Error", "Import video and generate captions first.")
            return

        escaped_srt = self.get_escaped_srt()
        
        file_dialog = QFileDialog()
        output_file, _ = file_dialog.getSaveFileName(self, "Export Video", "", "Video Files (*.mp4)")
        if output_file:
            self.status_label.setText("⏳ Exporting video with burned-in captions. Please wait...")
            self.progress_bar.setVisible(True)
            self.export_btn.setEnabled(False)
            
            self.export_thread = ExportThread(
                self.video_path, escaped_srt, output_file,
                self.font_combo.currentText(),
                self.size_spin.value(),
                self.color_combo.currentData(),
                self.margin_spin.value(),
                self.align_combo.currentData()
            )
            self.export_thread.finished.connect(self.on_export_finished)
            self.export_thread.error.connect(self.on_export_error)
            self.export_thread.start()

    def on_export_finished(self):
        self.progress_bar.setVisible(False)
        self.export_btn.setEnabled(True)
        self.status_label.setText("✅ Video exported successfully.")
        QMessageBox.information(self, "Success", "Video exported successfully!")

    def on_export_error(self, error_msg):
        self.progress_bar.setVisible(False)
        self.export_btn.setEnabled(True)
        self.status_label.setText("❌ Error exporting video.")
        QMessageBox.critical(self, "Error", f"Failed to export video:\n{error_msg}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
