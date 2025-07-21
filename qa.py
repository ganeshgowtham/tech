import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QFileDialog, QLabel, QSlider, QScrollArea, QFrame,
                             QLineEdit, QGridLayout, QComboBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen
from moviepy import VideoFileClip, concatenate_videoclips
from pathlib import Path

class ClickableLabel(QLabel):
    """A custom QLabel that emits a signal when clicked"""
    clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.timestamp = 0  # Store the timestamp this label represents
        self.progress = 0  # Progress indicator (0-1)
        self.setMinimumHeight(90)  # Ensure room for progress bar
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
        
    def paintEvent(self, event):
        super().paintEvent(event)
        if self.progress > 0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Draw progress line
            pen = QPen(Qt.green, 2)
            painter.setPen(pen)
            x = int(self.width() * self.progress)
            painter.drawLine(x, 0, x, self.height())

class VideoEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Movie Editor")
        self.setGeometry(100, 100, 1200, 700)
        self.current_video = None
        self.video_clip = None
        self.current_frame = 0
        self.playing = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.edits = []  # List of (type, start_sec, end_sec, speed) tuples
        self.init_ui()

    def init_ui(self):
        # Set dark theme for the entire application
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QScrollArea {
                background-color: #2b2b2b;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #3d3d3d;
                background: #2b2b2b;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #4d4d4d;
                border: 1px solid #5d5d5d;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #5d5d5d;
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Left panel (video and timeline)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        main_layout.addWidget(left_panel, stretch=7)

        # Right panel (cut list)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        main_layout.addWidget(right_panel, stretch=3)

        # Video panel
        # Create a fixed-size container for the video
        video_container = QWidget()
        video_container.setFixedSize(640, 480)
        video_container_layout = QVBoxLayout(video_container)
        video_container_layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
        """)
        video_container_layout.addWidget(self.video_label)
        video_controls = QHBoxLayout()
        self.load_button = QPushButton("📁 Load Video")
        self.play_button = QPushButton("▶️ Play")
        self.skip_back_button = QPushButton("⏪ -10s")
        self.skip_forward_button = QPushButton("⏩ +10s")
        
        # Style the video control buttons
        button_style = """
            QPushButton {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px 10px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border: 1px solid #4d4d4d;
            }
            QPushButton:pressed {
                background-color: #1e1e1e;
            }
            QPushButton:disabled {
                background-color: #1e1e1e;
                color: #666666;
            }
        """
        self.load_button.setStyleSheet(button_style)
        self.play_button.setStyleSheet(button_style)
        self.skip_back_button.setStyleSheet(button_style)
        self.skip_forward_button.setStyleSheet(button_style)
        
        video_controls.addWidget(self.load_button)
        video_controls.addWidget(self.play_button)
        video_controls.addWidget(self.skip_back_button)
        video_controls.addWidget(self.skip_forward_button)
        
        # Add time display
        self.time_display = QLabel("00:00")
        self.time_display.setStyleSheet("""
            QLabel {
                color: white;
                background-color: #2b2b2b;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px 10px;
                min-width: 60px;
            }
        """)
        video_controls.addWidget(self.time_display)
        
        self.time_slider = QSlider(Qt.Horizontal)
        self.status_label = QLabel("No video loaded")
        
        # Add video container to layout with centering
        video_container_wrapper = QWidget()
        video_container_wrapper_layout = QHBoxLayout(video_container_wrapper)
        video_container_wrapper_layout.addStretch()
        video_container_wrapper_layout.addWidget(video_container)
        video_container_wrapper_layout.addStretch()
        
        left_layout.addWidget(video_container_wrapper)
        left_layout.addWidget(self.time_slider)
        left_layout.addLayout(video_controls)
        left_layout.addWidget(self.status_label)

        # Timeline panel
        timeline_label = QLabel("Video Timeline Frames")
        left_layout.addWidget(timeline_label)
        self.timeline_scroll = QScrollArea()
        self.timeline_scroll.setWidgetResizable(True)
        self.timeline_panel = QWidget()
        self.timeline_layout = QHBoxLayout(self.timeline_panel)
        self.timeline_scroll.setWidget(self.timeline_panel)
        left_layout.addWidget(self.timeline_scroll)

        # Cut list panel
        cut_list_label = QLabel("Cut List")
        right_layout.addWidget(cut_list_label)
        
        # Add cut controls
        edit_input_panel = QWidget()
        edit_input_layout = QGridLayout(edit_input_panel)
        
        # Operation type selection
        operation_label = QLabel("✂️ Operation:")
        self.operation_combo = QComboBox()
        self.operation_combo.addItems(["✂️ Cut", "⚡ Speed Up", "🐢 Slow Down"])
        self.operation_combo.setStyleSheet("""
            QComboBox {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
            }
            QComboBox:hover {
                border: 1px solid #4d4d4d;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
            }
        """)
        edit_input_layout.addWidget(operation_label, 0, 0)
        edit_input_layout.addWidget(self.operation_combo, 0, 1)
        
        from_label = QLabel("🕐 From (MM:SS):")
        self.from_time = QLineEdit()
        self.from_time.setPlaceholderText("00:00")
        self.from_time.setToolTip("Enter time in MM:SS format (e.g., 01:30 for 1 minute 30 seconds)")
        self.from_time.textChanged.connect(self.validate_time_input)
        self.from_time.setStyleSheet("""
            QLineEdit {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
            }
            QLineEdit:focus {
                border: 1px solid #4d4d4d;
            }
        """)
        
        to_label = QLabel("🕐 To (MM:SS):")
        self.to_time = QLineEdit()
        self.to_time.setPlaceholderText("00:00")
        self.to_time.setToolTip("Enter time in MM:SS format (e.g., 02:45 for 2 minutes 45 seconds)")
        self.to_time.textChanged.connect(self.validate_time_input)
        self.to_time.setStyleSheet("""
            QLineEdit {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
            }
            QLineEdit:focus {
                border: 1px solid #4d4d4d;
            }
        """)
        
        edit_input_layout.addWidget(from_label, 1, 0)
        edit_input_layout.addWidget(self.from_time, 1, 1)
        edit_input_layout.addWidget(to_label, 2, 0)
        edit_input_layout.addWidget(self.to_time, 2, 1)
        
        # Speed input for speed modifications
        self.speed_label = QLabel("⚡ Speed Factor:")
        self.speed_label.setObjectName("speed_label")
        self.speed_combo = QComboBox()
        self.speed_combo.setStyleSheet("""
            QComboBox {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
            }
            QComboBox:hover {
                border: 1px solid #4d4d4d;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
            }
        """)
        # Will update options based on operation type
        self.speed_combo.setVisible(False)
        edit_input_layout.addWidget(self.speed_label, 3, 0)
        edit_input_layout.addWidget(self.speed_combo, 3, 1)
        
        self.add_edit_button = QPushButton("➕ Add Edit")
        self.add_edit_button.setStyleSheet("""
            QPushButton {
                background-color: #2b5b2b;
                color: white;
                border: 1px solid #3d5d3d;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3d6b3d;
            }
            QPushButton:pressed {
                background-color: #1e4e1e;
            }
            QPushButton:disabled {
                background-color: #1e1e1e;
                color: #666666;
            }
        """)
        edit_input_layout.addWidget(self.add_edit_button, 4, 0, 1, 2)
        right_layout.addWidget(edit_input_panel)
        
        # Connect operation type change to update UI
        self.operation_combo.currentTextChanged.connect(self.update_speed_input_visibility)
        
        # Cut list
        self.cut_list_widget = QScrollArea()
        self.cut_list_widget.setWidgetResizable(True)
        self.cut_list_panel = QWidget()
        self.cut_list_layout = QVBoxLayout(self.cut_list_panel)
        self.cut_list_layout.setAlignment(Qt.AlignTop)  # Align all items to top
        self.cut_list_widget.setWidget(self.cut_list_panel)
        right_layout.addWidget(self.cut_list_widget)
        
        # Save final video section
        save_section = QWidget()
        save_layout = QVBoxLayout(save_section)
        
        self.save_final_button = QPushButton("💾 Save Final Video")
        self.save_final_button.setEnabled(False)
        self.save_final_button.setStyleSheet("""
            QPushButton {
                background-color: #2b2b5b;
                color: white;
                border: 1px solid #3d3d6d;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #3d3d6b;
            }
            QPushButton:pressed {
                background-color: #1e1e4e;
            }
            QPushButton:disabled {
                background-color: #1e1e1e;
                color: #666666;
            }
        """)
        save_layout.addWidget(self.save_final_button)
        
        self.progress_label = QLabel()
        self.progress_label.setWordWrap(True)
        self.progress_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-style: italic;
                padding: 5px;
                background-color: #1e1e1e;
                border-radius: 4px;
            }
        """)
        save_layout.addWidget(self.progress_label)
        
        right_layout.addWidget(save_section)

        # Connections
        self.load_button.clicked.connect(self.load_video)
        self.play_button.clicked.connect(self.play_pause)
        self.skip_back_button.clicked.connect(self.skip_back)
        self.skip_forward_button.clicked.connect(self.skip_forward)
        self.time_slider.sliderMoved.connect(self.set_position)
        self.add_edit_button.clicked.connect(self.add_edit)
        self.save_final_button.clicked.connect(self.save_final_video)
        
        # Initial button states
        self.play_button.setEnabled(False)
        self.skip_back_button.setEnabled(False)
        self.skip_forward_button.setEnabled(False)
        self.add_edit_button.setEnabled(False)
        self.update_speed_input_visibility()

    # Removed duplicate load_video method

    def update_frame(self):
        if self.video_clip is not None:
            try:
                frame_time = max(0, min(self.current_frame / 1000.0, self.video_clip.duration))
                frame = self.video_clip.get_frame(frame_time)
                if frame is None:
                    raise ValueError("Could not get frame")
                    
                # Convert frame to RGB if necessary
                if len(frame.shape) == 2:  # Grayscale
                    frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
                elif frame.shape[2] == 4:  # RGBA
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2RGB)
                    
                height, width = frame.shape[:2]
                bytes_per_line = 3 * width
                q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(q_img)
                
                # Calculate scaling to fit within the 640x480 container while maintaining aspect ratio
                container_size = self.video_label.parent().size()
                scaled_pixmap = pixmap.scaled(
                    container_size.width(),
                    container_size.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.video_label.setPixmap(scaled_pixmap)
                self.time_slider.setValue(self.current_frame)
                
                # Update time display and highlighted frame
                current_time = self.current_frame / 1000.0
                minutes = int(current_time // 60)
                seconds = int(current_time % 60)
                self.time_display.setText(f"{minutes:02d}:{seconds:02d}")
                self.update_highlighted_frame(current_time)
                
                if self.playing:
                    self.current_frame += 33  # Approximately 30 fps
                    if self.current_frame >= int(self.video_clip.duration * 1000):
                        self.playing = False
                        self.play_button.setText("Play")
                        self.timer.stop()
                    else:
                        # Scroll timeline while playing
                        self.scroll_timeline_to_current_time()
            except:
                self.playing = False
                self.play_button.setText("Play")
                self.timer.stop()

    def play_pause(self):
        self.playing = not self.playing
        if self.playing:
            self.play_button.setText("Pause")
            self.timer.start(33)  # Approximately 30 fps
        else:
            self.play_button.setText("Play")
            self.timer.stop()

    def skip_back(self):
        self.current_frame = max(0, self.current_frame - 10000)  # 10 seconds
        self.update_frame()

    def skip_forward(self):
        self.current_frame = min(int(self.video_clip.duration * 1000), self.current_frame + 10000)
        self.update_frame()

    def set_position(self, position):
        self.current_frame = position
        self.update_frame()
        self.scroll_timeline_to_current_time()

    def scroll_timeline_to_current_time(self):
        if not self.video_clip:
            return
            
        # Calculate the position in the timeline
        current_time = self.current_frame / 1000.0  # Convert to seconds
        total_width = self.timeline_panel.width()
        duration = self.video_clip.duration
        
        # Calculate scroll position based on current time
        scroll_position = int((current_time / duration) * total_width)
        
        # Center the current frame in the scroll area
        viewport_width = self.timeline_scroll.viewport().width()
        scroll_position = max(0, scroll_position - (viewport_width // 2))
        
        # Scroll horizontally to the calculated position
        self.timeline_scroll.horizontalScrollBar().setValue(scroll_position)
        
        # Update the time display
        minutes = int(current_time // 60)
        seconds = int(current_time % 60)
        self.time_display.setText(f"{minutes:02d}:{seconds:02d}")
        
        # Update highlighted frame in timeline
        self.update_highlighted_frame(current_time)
        
    def update_highlighted_frame(self, current_time):
        # Find the closest frame in timeline
        interval = 5  # Same interval as in populate_timeline
        
        # Update all frames
        for i in range(self.timeline_layout.count()):
            container = self.timeline_layout.itemAt(i).widget()
            if container:
                frame_label = container.layout().itemAt(0).widget()
                if isinstance(frame_label, ClickableLabel) and hasattr(frame_label, 'timestamp'):
                    frame_time = frame_label.timestamp
                    
                    # Calculate progress within this frame's interval
                    if frame_time <= current_time < frame_time + interval:
                        progress = (current_time - frame_time) / interval
                        frame_label.progress = progress
                        frame_label.setStyleSheet("""
                            QLabel {
                                background-color: #2b2b2b;
                                border: 2px solid #00ff00;
                                border-radius: 4px;
                            }
                        """)
                    else:
                        frame_label.progress = 0
                        frame_label.setStyleSheet("""
                            QLabel {
                                background-color: #2b2b2b;
                                border: 1px solid #3d3d3d;
                                border-radius: 4px;
                            }
                            QLabel:hover {
                                border: 1px solid #6d6d6d;
                            }
                        """)
                    frame_label.update()  # Force repaint

    def populate_timeline(self):
        # Clear previous frames
        for i in reversed(range(self.timeline_layout.count())):
            widget = self.timeline_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Add actual video frames every 5 seconds
        duration = self.video_clip.duration
        interval = 5  # 5 seconds between frames
        
        # Calculate exact number of frames needed
        num_frames = int(duration // interval)  # Integer division to get complete intervals
        remaining_time = duration % interval
        
        # Only add extra frame if remaining time is significant (more than 0.5 seconds)
        if remaining_time > 0.5:
            num_frames += 1
        
        for i in range(num_frames):
            # Special handling for first and last frames
            if i == 0:
                time = 0  # First frame at exactly 0
            elif i == num_frames - 1:
                # For last frame, use either the last complete interval or actual end
                time = min(i * interval, max(0, duration - 0.03))  # Small offset from end
            else:
                time = i * interval
                
            # Create frame preview with proper error handling
            frame = self.video_clip.get_frame(time)
            
            # Ensure frame is not None and has valid dimensions
            if frame is None or frame.size == 0:
                continue  # Skip this frame
            
            # Convert frame to RGB if necessary
            if len(frame.shape) == 2:  # Grayscale
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
            elif frame.shape[2] == 4:  # RGBA
                frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2RGB)
            elif frame.shape[2] == 3:  # Already RGB
                pass
            else:
                continue  # Skip invalid frame format
            
            height, width = frame.shape[:2]
            if height == 0 or width == 0:
                continue  # Skip invalid dimensions
            # Calculate aspect ratio and target dimensions
            target_width = 120
            target_height = 90
            aspect_ratio = width / height
            
            # Adjust dimensions to maintain aspect ratio
            if aspect_ratio > target_width / target_height:
                # Width-constrained
                new_width = target_width
                new_height = int(target_width / aspect_ratio)
            else:
                # Height-constrained
                new_height = target_height
                new_width = int(target_height * aspect_ratio)
                
            bytes_per_line = 3 * width
            q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
            frame_pixmap = QPixmap.fromImage(q_img)
            
            # Create container widget for frame and timestamp
            container = QWidget()
            container_layout = QVBoxLayout(container)
            
            # Frame preview
            frame_label = ClickableLabel()  # Using custom ClickableLabel instead of QLabel
            frame_label.setFixedSize(120, 90)
            frame_label.setPixmap(frame_pixmap.scaled(
                new_width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
            # Center the pixmap in the label
            frame_label.setAlignment(Qt.AlignCenter)
            frame_label.setStyleSheet("""
                QLabel {
                    background-color: #2b2b2b;
                    border: 1px solid #3d3d3d;
                    border-radius: 4px;
                }
                QLabel:hover {
                    border: 1px solid #6d6d6d;
                }
            """)
            # Store the timestamp in the label and connect click handler
            frame_label.timestamp = time
            frame_label.clicked.connect(self.timeline_frame_clicked)
            
            # Timestamp label
            time_label = QLabel(f"{int(time//60):02d}:{int(time%60):02d}")
            time_label.setAlignment(Qt.AlignCenter)
            
            # Add Cut button
            add_cut_button = QPushButton("✂️ Add Cut")
            add_cut_button.setStyleSheet("""
                QPushButton {
                    background-color: #2b2b2b;
                    color: white;
                    border: 1px solid #3d3d3d;
                    border-radius: 4px;
                    padding: 3px;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #3d3d3d;
                    border: 1px solid #4d4d4d;
                }
            """)
            add_cut_button.clicked.connect(lambda checked, t=time: self.add_cut_at_time(t))
            
            container_layout.addWidget(frame_label)
            container_layout.addWidget(time_label)
            container_layout.addWidget(add_cut_button)
            container_layout.setSpacing(2)
            container_layout.setContentsMargins(2, 2, 2, 2)
            
            self.timeline_layout.addWidget(container)

    def timeline_frame_clicked(self):
        """Handler for when a frame in the timeline is clicked"""
        frame_label = self.sender()  # Get the label that was clicked
        if hasattr(frame_label, 'timestamp'):
            # Convert timestamp to milliseconds for current_frame
            self.current_frame = int(frame_label.timestamp * 1000)
            self.update_frame()
            # Update slider position
            self.time_slider.setValue(self.current_frame)
            
    def parse_time(self, time_str):
        try:
            minutes, seconds = map(int, time_str.split(':'))
            if minutes < 0 or seconds < 0 or seconds >= 60:
                return None
            return minutes * 60 + seconds
        except (ValueError, TypeError):
            return None
            
    def validate_time_input(self):
        sender = self.sender()
        text = sender.text()
        
        # Allow empty input
        if not text:
            sender.setStyleSheet("")
            return
            
        # Check format
        if len(text) > 5:  # Max length for MM:SS
            sender.setText(text[:5])
            return
            
        # Auto-add colon after minutes
        if len(text) == 2 and text.isdigit() and ":" not in text:
            sender.setText(text + ":")
            return
            
        # Validate format and values
        try:
            if ":" in text:
                minutes, seconds = map(str, text.split(':'))
                if len(seconds) > 2:  # Limit seconds to 2 digits
                    sender.setText(f"{minutes}:{seconds[:2]}")
                    return
                    
                if len(minutes) > 2:  # Limit minutes to 2 digits
                    sender.setText(f"{minutes[:2]}:{seconds}")
                    return
                    
                # Validate values if both parts are complete
                if len(minutes) == 2 and len(seconds) == 2:
                    if self.parse_time(text) is None:
                        sender.setStyleSheet("background-color: #FFE4E1;")  # Light red for invalid
                        return
            
            # Valid input
            sender.setStyleSheet("")
            
        except (ValueError, IndexError):
            sender.setStyleSheet("background-color: #FFE4E1;")  # Light red for invalid

    def update_speed_input_visibility(self, operation_type=None):
        if operation_type is None:
            operation_type = self.operation_combo.currentText()
            
        show_speed = "Speed Up" in operation_type or "Slow Down" in operation_type
        self.speed_label.setVisible(show_speed)
        self.speed_combo.setVisible(show_speed)
        
        # Update speed options based on operation
        self.speed_combo.clear()
        if operation_type == "Speed Up":
            # Increase speed from 1.5x to 4.0x with 0.5 increments
            speeds = [f"{speed:.1f}x" for speed in [1.5, 2.0, 2.5, 3.0, 3.5, 4.0]]
            self.speed_combo.addItems(speeds)
        elif operation_type == "Slow Down":
            # Decrease speed from 0.8x to 0.3x with 0.5 decrements
            speeds = [f"{speed:.1f}x" for speed in [0.8, 0.7, 0.6, 0.5, 0.4, 0.3]]
            self.speed_combo.addItems(speeds)

    def add_edit(self):
        from_time = self.parse_time(self.from_time.text())
        to_time = self.parse_time(self.to_time.text())
        operation = self.operation_combo.currentText()
        
        if from_time is None or to_time is None:
            self.status_label.setText("Invalid time format. Use MM:SS")
            return
            
        if from_time >= to_time:
            self.status_label.setText("End time must be after start time")
            return
            
        if to_time > self.video_clip.duration:
            self.status_label.setText("End time exceeds video duration")
            return

        speed = 1.0
        if "Speed Up" in operation or "Slow Down" in operation:  # Check if operation contains these strings
            if not self.speed_combo.currentText():
                self.status_label.setText("Please select a speed factor")
                return
            try:
                # Remove the 'x' and convert to float
                speed = float(self.speed_combo.currentText().rstrip('x'))
                if "Speed Up" in operation:
                    # Speed up values are already correct (e.g., 2.0 means 2x faster)
                    pass
                else:  # Slow Down
                    # Speed down values are already correct fractions (e.g., 0.5 means half speed)
                    pass
            except ValueError:
                self.status_label.setText("Invalid speed factor")
                return

        self.edits.append((operation, from_time, to_time, speed))
        self.update_edit_list()
        self.save_final_button.setEnabled(True)
        self.from_time.clear()
        self.to_time.clear()
        if operation in ["Speed Up", "Slow Down"]:
            self.speed_combo.setCurrentIndex(0)  # Reset to first option
        
        msg = f"Added {operation.lower()}: {from_time//60:02d}:{from_time%60:02d} - {to_time//60:02d}:{to_time%60:02d}"
        if operation in ["Speed Up", "Slow Down"]:
            msg += f" (speed: {speed:.1f}x)"
        self.status_label.setText(msg)

    def update_edit_list(self):
        # Clear existing edits
        for i in reversed(range(self.cut_list_layout.count())):
            widget = self.cut_list_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # Add edit entries
        for i, (op_type, start, end, speed) in enumerate(sorted(self.edits, key=lambda x: x[1])):
            edit_widget = QWidget()
            edit_layout = QHBoxLayout(edit_widget)
            edit_layout.setAlignment(Qt.AlignTop)  # Align contents to top
            
            time_text = f"{op_type} {i+1}: {start//60:02d}:{start%60:02d} - {end//60:02d}:{end%60:02d}"
            if "Speed Up" in op_type or "Slow Down" in op_type:
                time_text += f" ({speed:.1f}x)"
            edit_label = QLabel(time_text)
            edit_label.setStyleSheet("""
                QLabel {
                    color: white;
                    background-color: #2b2b2b;
                    border: 1px solid #3d3d3d;
                    border-radius: 4px;
                    padding: 5px;
                }
            """)
            edit_layout.addWidget(edit_label)
            
            delete_button = QPushButton("×")
            delete_button.setFixedSize(20, 20)
            delete_button.clicked.connect(lambda checked, idx=i: self.delete_edit(idx))
            edit_layout.addWidget(delete_button)
            
            self.cut_list_layout.addWidget(edit_widget)

    def delete_edit(self, index):
        if 0 <= index < len(self.edits):
            self.edits.pop(index)
            self.update_edit_list()
            if not self.edits:
                self.save_final_button.setEnabled(False)
            # Update the UI state
            self.from_time.clear()
            self.to_time.clear()
            if self.operation_combo.currentText() in ["Speed Up", "Slow Down"]:
                self.speed_combo.setCurrentIndex(0)

    def save_final_video(self):
        if not self.edits or not self.video_clip:
            return

        output_path, _ = QFileDialog.getSaveFileName(self, "Save Final Video", "", "Video Files (*.mp4)")
        if not output_path:
            return

        # Disable UI controls during save
        self.save_final_button.setEnabled(False)
        self.add_edit_button.setEnabled(False)
        QApplication.processEvents()  # Update UI

        try:
            self.progress_label.setText("Preparing video segments...")
            QApplication.processEvents()
            
            # Sort edits by start time
            sorted_edits = sorted(self.edits, key=lambda x: x[1])
            segments = []
            last_end = 0
            
            # Process each edit
            for i, (op_type, start, end, speed) in enumerate(sorted_edits, 1):
                self.progress_label.setText(
                    f"Processing edit {i}/{len(sorted_edits)}: "
                    f"{op_type} from {start//60:02d}:{start%60:02d} to {end//60:02d}:{end%60:02d}"
                )
                QApplication.processEvents()
                
                # Add segment before the edit if there's a gap
                if last_end < start:
                    segments.append(self.video_clip.subclipped(float(last_end), float(start)))
                
                # Process the edited segment
                if op_type == "Cut":
                    self.progress_label.setText(f"Applying cut {i}/{len(sorted_edits)}...")
                    QApplication.processEvents()
                else:
                    # For speed modifications
                    self.progress_label.setText(
                        f"Applying {op_type.lower()} {i}/{len(sorted_edits)} "
                        f"(speed: {speed:.1f}x)..."
                    )
                    QApplication.processEvents()
                    clip = self.video_clip.subclipped(float(start), float(end))
                    if op_type in ["Speed Up", "Slow Down"]:
                        clip = clip.speedx(speed)
                    segments.append(clip)
                
                last_end = end
            
            # Add final segment if needed
            if last_end < self.video_clip.duration:
                self.progress_label.setText("Processing final segment...")
                QApplication.processEvents()
                segments.append(self.video_clip.subclipped(float(last_end), float(self.video_clip.duration)))
            
            if segments:
                self.progress_label.setText("Combining video segments...")
                QApplication.processEvents()
                final_clip = concatenate_videoclips(segments)
                
                try:
                    self.progress_label.setText("Encoding final video (this may take a while)...")
                    self.status_label.setText("Saving video... Please wait.")
                    QApplication.processEvents()
                    
                    self.progress_label.setText("Encoding final video (this may take a while)...")
                    QApplication.processEvents()
                    
                    final_clip.write_videofile(
                        output_path,
                        codec='libx264',
                        audio_codec='aac'  # Ensure audio compatibility
                    )
                    
                    self.status_label.setText(f"Saved final video as: {Path(output_path).name}")
                    self.progress_label.setText("Video saved successfully! ✓")
                finally:
                    self.progress_label.setText("Cleaning up temporary files...")
                    QApplication.processEvents()
                    final_clip.close()
                    # Clean up segment clips
                    for clip in segments:
                        if clip != self.video_clip:  # Don't close the main clip
                            clip.close()
            
        except Exception as e:
            self.status_label.setText(f"Error saving video: {str(e)}")
            self.progress_label.setText(f"Error: {str(e)}")
        finally:
            # Re-enable UI controls
            self.save_final_button.setEnabled(True)
            self.add_edit_button.setEnabled(True)
            QApplication.processEvents()

    def load_video(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mkv *.webm)")
        if filename:
            try:
                if self.video_clip is not None:
                    self.video_clip.close()
                self.current_video = filename
                self.video_clip = VideoFileClip(filename)
                self.current_frame = 0
                self.edits = []
                self.time_slider.setRange(0, int(self.video_clip.duration * 1000))
            except Exception as e:
                self.status_label.setText(f"Error loading video: {str(e)}")
                self.video_clip = None
                self.current_video = None
                return
            
            # Enable controls
            self.play_button.setEnabled(True)
            self.skip_back_button.setEnabled(True)
            self.skip_forward_button.setEnabled(True)
            self.add_edit_button.setEnabled(True)
            self.save_final_button.setEnabled(False)
            
            self.status_label.setText(f"Loaded: {Path(filename).name}")
            self.update_frame()
            self.populate_timeline()
            self.update_edit_list()

    def closeEvent(self, event):
        if self.video_clip:
            self.video_clip.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    editor = VideoEditor()
    editor.show()
    sys.exit(app.exec_())
