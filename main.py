import sys
from src.ui.main import SystemTrayApp


if __name__ == "__main__":
    app = SystemTrayApp()
    app.setQuitOnLastWindowClosed(False)
    sys.exit(app.exec())
