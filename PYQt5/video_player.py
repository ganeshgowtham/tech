from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QHBoxLayout, 
                          QSizePolicy, QSlider, QLabel, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
import cv2
import os
from datetime import timedelta

class VideoPlayer(QWidget):
    def __init__(self, video_path, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)
        self.video_path = video_path
        self.is_fullscreen = False
        
        # Set widget style
        self.setStyleSheet("""
            QWidget {
                background-color: #1A1C1E;
                color: #E4E7EB;
            }
            QPushButton {
                background-color: #2D3135;
                border: 1px solid #404346;
                border-radius: 16px;
                color: #E4E7EB;
                font-size: 14px;
                min-width: 32px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #363A3D;
                border-color: #2662D9;
            }
            QSlider::groove:horizontal {
                border: 1px solid #404346;
                height: 8px;
                background: #2D3135;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #2662D9;
                border: 1px solid #2662D9;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #1D4BA3;
            }
            QLabel {
                color: #E4E7EB;
                padding: 8px;
                border-radius: 4px;
            }
        """)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Create status label
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.hide()
        
        # Create video display label
        self.video_label = QLabel()
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: #000000;
                border-radius: 8px;
                padding: 0px;
            }
        """)
        
        # Double click for fullscreen
        self.video_label.mouseDoubleClickEvent = self.toggle_fullscreen
        
        # Create controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        
        # Play/Pause button
        self.play_button = QPushButton("▶")
        self.play_button.setFixedSize(32, 32)
        self.play_button.clicked.connect(self.play_pause)
        
        # Time display label
        self.time_label = QLabel("0:00 / 0:00")
        self.time_label.setFixedWidth(100)
        self.time_label.setAlignment(Qt.AlignCenter)
        
        # Slider for video position
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self.set_position)
        
        # Volume control
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.setStyleSheet("""
            QSlider { margin-right: 10px; }
        """)
        
        # Volume icon
        self.volume_button = QPushButton("🔊")
        self.volume_button.setFixedSize(32, 32)
        self.volume_button.clicked.connect(self.toggle_mute)
        
        # Fullscreen button
        self.fullscreen_button = QPushButton("⛶")
        self.fullscreen_button.setFixedSize(32, 32)
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        
        # Add widgets to controls layout
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.time_label)
        controls_layout.addWidget(self.position_slider)
        controls_layout.addWidget(self.volume_button)
        controls_layout.addWidget(self.volume_slider)
        controls_layout.addWidget(self.fullscreen_button)
        
        # Create a frame for controls
        self.controls_widget = QWidget()
        self.controls_widget.setLayout(controls_layout)
        self.controls_widget.setStyleSheet("""
            QWidget {
                background-color: #2D3135;
                border-radius: 8px;
                padding: 5px;
            }
        """)
        
        # Add widgets to main layout
        layout.addWidget(self.status_label)
        layout.addWidget(self.video_label)
        layout.addWidget(self.controls_widget)
        
        # Initialize video capture
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.is_playing = False
        self.total_frames = 0
        self.current_frame = 0
        self.fps = 0
        
        # Load video
        self.load_video()
    
    def load_video(self):
        """Load and attempt to play the video file"""
        if not os.path.exists(self.video_path):
            self.show_error(f"Video file not found: {self.video_path}")
            return
            
        try:
            self.show_status("Loading video...")
            self.cap = cv2.VideoCapture(self.video_path)
            
            if not self.cap.isOpened():
                raise Exception("Failed to open video file")
            
            # Get video properties
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.position_slider.setRange(0, self.total_frames)
            
            # Update time label
            total_seconds = int(self.total_frames / self.fps)
            total_time = str(timedelta(seconds=total_seconds))
            self.time_label.setText(f"0:00 / {total_time}")
            
            # Set up timer for frame updates
            self.timer.setInterval(int(1000/self.fps))
            
            # Load first frame
            self.update_frame()
            self.show_status("Ready to play")
            
        except Exception as e:
            self.show_error(f"Failed to load video: {str(e)}")
    
    def update_frame(self):
        """Update the current frame"""
        if self.cap is None:
            return
            
        ret, frame = self.cap.read()
        if ret:
            # Convert frame from BGR to RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            
            # Scale frame to fit label while maintaining aspect ratio
            label_size = self.video_label.size()
            scale = min(label_size.width() / w, label_size.height() / h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            
            # Use INTER_CUBIC for better quality
            frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
            
            # Convert frame to QImage and display
            bytes_per_line = ch * new_w
            qt_image = QImage(frame.data, new_w, new_h, bytes_per_line, QImage.Format_RGB888)
            self.video_label.setPixmap(QPixmap.fromImage(qt_image))
            
            # Update position and time
            self.current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            self.position_slider.setValue(self.current_frame)
            
            current_seconds = int(self.current_frame / self.fps)
            total_seconds = int(self.total_frames / self.fps)
            current_time = str(timedelta(seconds=current_seconds))
            total_time = str(timedelta(seconds=total_seconds))
            self.time_label.setText(f"{current_time} / {total_time}")
            
        else:
            # Video ended
            self.timer.stop()
            self.is_playing = False
            self.play_button.setText("▶")
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.current_frame = 0
            self.update_frame()  # Show first frame
    
    def play_pause(self):
        """Toggle play/pause"""
        if self.cap is None:
            return
            
        if self.is_playing:
            self.timer.stop()
            self.play_button.setText("▶")
        else:
            self.timer.start()
            self.play_button.setText("⏸")
            
        self.is_playing = not self.is_playing
    
    def set_position(self, position):
        """Set video position"""
        if self.cap is None:
            return
            
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, position)
        self.update_frame()
    
    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode"""
        if self.is_fullscreen:
            self.showNormal()
            self.controls_widget.show()
            self.fullscreen_button.setText("⛶")
        else:
            self.showFullScreen()
            self.controls_widget.hide()
            self.fullscreen_button.setText("⟱")
        self.is_fullscreen = not self.is_fullscreen
    
    def toggle_mute(self):
        """Toggle mute state"""
        if self.volume_slider.value() > 0:
            self.volume_slider.setValue(0)
            self.volume_button.setText("🔇")
        else:
            self.volume_slider.setValue(100)
            self.volume_button.setText("🔊")
    
    def show_error(self, message):
        """Show error in both status label and message box"""
        self.show_status(f"Error: {message}")
        QMessageBox.critical(self, "Error", message)
    
    def show_status(self, message):
        """Show status message in label"""
        self.status_label.setText(message)
        self.status_label.show()
    
    def closeEvent(self, event):
        """Clean up resources when closing"""
        self.timer.stop()
        if self.cap is not None:
            self.cap.release()
        super().closeEvent(event)