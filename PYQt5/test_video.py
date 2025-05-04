from PyQt5.QtWidgets import QApplication, QMainWindow
from video_player import VideoPlayer
import sys
import os

class VideoPlayerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Player")
        
        # Get path to v.mp4
        current_dir = os.path.dirname(os.path.abspath(__file__))
        video_path = os.path.join(current_dir, 'v.mp4')
        
        # Create and set up video player
        self.video_player = VideoPlayer(video_path)
        self.setCentralWidget(self.video_player)
        
        # Set window size
        self.resize(800, 600)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = VideoPlayerWindow()
    window.show()
    sys.exit(app.exec_())