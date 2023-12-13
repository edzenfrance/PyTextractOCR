# Standard libraries
import shutil
import socket
from pathlib import Path
from urllib import request, error

# Third-party libraries
import requests
from loguru import logger
from PySide6.QtCore import QThread, Signal, QObject, QTimer


class DownloadTrainedData:
    def __init__(self, settings_instance):
        super().__init__()

        self.download_thread = None
        self.check_internet_thread = None
        self.language_name = None

        # Dependency Injection for settings method, injects an instance of SettingsUI class into this class
        self.settings_instance = settings_instance

        self.github_tessdata_best_link = "https://raw.githubusercontent.com/tesseract-ocr/tessdata_best/main/"

    def start_download(self, language_name, download_destination, file_name):

        # Check if the internet checking thread is running
        if self.check_internet_thread is not None and self.check_internet_thread.isRunning():
            logger.warning("Internet checking thread is already running")
            return

        # Check if the download thread is running
        if self.download_thread is not None and self.download_thread.isRunning():
            logger.warning("Download thread is already running")
            return

        self.language_name = language_name
        download_url = f'{self.github_tessdata_best_link}{file_name}'

        self.settings_instance.toggle_download_button_progress_bar(self.language_name, True)

        self.download_thread = DownloadThread(download_url, str(download_destination), file_name)
        self.download_thread.progress_signal.connect(self.settings_instance.update_progress_bar)
        self.download_thread.error_signal.connect(self.handle_display_and_cleanup)
        self.download_thread.finished.connect(self.handle_display_and_cleanup)
        self.download_thread.start()

        self.check_internet_worker = InternetCheckWorker(self.download_thread)
        self.check_internet_thread = QThread()
        self.check_internet_worker.moveToThread(self.check_internet_thread)
        self.check_internet_thread.started.connect(self.check_internet_worker.start_checking)
        self.check_internet_worker.no_internet_signal.connect(self.handle_display_and_cleanup)
        self.check_internet_thread.start()

    def handle_display_and_cleanup(self):
        self.settings_instance.toggle_download_button_progress_bar(self.language_name, False)
        self.cleanup_check_internet_thread()

    def cleanup_check_internet_thread(self):
        if self.check_internet_thread is not None:
            logger.info("Cleanup internet check worker thread")
            self.check_internet_thread.quit()
            self.check_internet_thread.wait()
            self.check_internet_thread = None

            self.download_thread.terminate()
            self.download_thread.wait()
            self.download_thread = None


class DownloadThread(QThread):
    progress_signal = Signal(int)
    error_signal = Signal()

    def __init__(self, url, destination, filename):
        super().__init__()

        self.url = url
        self.destination = destination
        self.filename = filename
        self._stop_event = False

    def run(self):
        try:
            logger.info(f"Downloading file using requests: {self.url}")
            with requests.get(self.url, stream=True) as response:
                response.raise_for_status()  # Status code 200 = successful
                total_size = int(response.headers.get('content-length', 0))
                downloaded_size = 0

                with open(self.destination, 'wb') as file:
                    for data in response.iter_content(chunk_size=1024):
                        if self._stop_event:
                            break
                        file.write(data)
                        downloaded_size += len(data)
                        progress_percentage = int(downloaded_size / total_size * 100)
                        self.progress_signal.emit(progress_percentage)

            logger.success(f"Download successful")
            self.rename_downloaded_file()
        except (ConnectionError, TimeoutError, requests.exceptions.RequestException) as e:
            error_type = "Connection error" if isinstance(e, ConnectionError) else (
                "Timeout error" if isinstance(e, TimeoutError) else "Request error")
            logger.error(f"{error_type}: {e}")
            self.stop_download()
            self.error_signal.emit()

    def is_internet_available(self):
        try:
            logger.info("Checking internet connection")
            request.urlopen("http://www.google.com", timeout=5)
            return True
        except (error.URLError, socket.timeout) as e:
            logger.error(f"Internet connection error: {e}")
            return False

    def rename_downloaded_file(self):
        tessdata_folder = Path('./tessdata')
        current_file_path = tessdata_folder / f'{self.filename}.tmp'
        new_file_path = tessdata_folder / self.filename
        try:
            shutil.move(current_file_path, new_file_path)
            logger.info(f"The file '{current_file_path}' has been renamed to '{new_file_path}'.")
        except Exception as e:
            logger.error(f"Failed to rename the file {current_file_path}: {e}")
        self.stop_download()

    def stop_download(self):
        self._stop_event = True  # Flag to stop the download thread
        if self.isRunning():
            logger.info(f"Cleanup download thread")
            self.quit()  # Quit download thread
            self.wait()


class InternetCheckWorker(QObject):
    no_internet_signal = Signal()

    def __init__(self, download_thread):
        super().__init__()

        self.download_thread = download_thread

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_internet_connection)

    def start_checking(self):
        self.timer.start(1000)

    def stop_checking(self):
        self.timer.stop()

    def check_internet_connection(self):
        if not self.download_thread._stop_event:
            if not self.download_thread.is_internet_available():
                self.no_internet_signal.emit()
                self.stop_checking()
