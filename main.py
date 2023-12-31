# Third-party library
from PySide6.QtWidgets import QApplication

# Source
from src.ui.main import MainUI

if __name__ == "__main__":
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    dialog = MainUI()
    dialog.show()
    app.exec()
