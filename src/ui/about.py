# Third-party Library
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtGui import QPixmap, QIcon

# Custom Library
from src.ui.asset_manager import app_icon, about_image


class AboutUI(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("About PyTextractOCR")
        self.setWindowIcon(QIcon(app_icon))
        self.setFixedSize(300, 160)

        image_label = QLabel(self)
        pixmap = QPixmap(about_image)
        resized_pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)  # Resize QPixmap
        image_label.setPixmap(resized_pixmap)

        text_layout = QVBoxLayout()

        pytex_label = QLabel("PyTextractOCR")
        version_label = QLabel("Version: 1.0")
        about_label = QLabel("Author: Edzen France")
        text_layout.addSpacing(10)  # Add space
        text_layout.addWidget(pytex_label)
        text_layout.addWidget(version_label)
        text_layout.addWidget(about_label)
        text_layout.addSpacing(100)  # Add space

        button_layout = QHBoxLayout()
        button_layout.addStretch(1)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.close)
        button_layout.addWidget(ok_button)

        text_layout.addLayout(button_layout)

        # Create QHBoxLayout and add QVBoxLayout and QLabel to it
        layout = QHBoxLayout()
        layout.addWidget(image_label)
        layout.addLayout(text_layout)

        self.setLayout(layout)
