# Third-party libraries
from loguru import logger
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMessageBox

# Source
from src.ui.asset_manager import app_icon


def show_message_box(msg_type, title, text):
    logger.info(f"Showing message box type '{msg_type}'")
    msg_type_dict = {
        "NoIcon": QMessageBox.NoIcon,
        "Information": QMessageBox.Information,
        "Warning": QMessageBox.Warning,
        "Critical": QMessageBox.Critical,
        "Question": QMessageBox.Question
    }
    msgbox = QMessageBox(msg_type_dict[msg_type], title, text)
    msgbox.setWindowIcon(QIcon(app_icon))

    if msg_type == 'Question':
        msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)

    msgbox.setWindowFlags(msgbox.windowFlags() | Qt.WindowStaysOnTopHint)
    return_value = msgbox.exec()

    if return_value == QMessageBox.Yes:
        return 'Yes'
    else:
        return 'No'
