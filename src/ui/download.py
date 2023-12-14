# Standard libraries
import shutil
from pathlib import Path

# Third-party libraries
import requests
from loguru import logger
from PySide6.QtCore import QThread, Signal


class DownloadTrainedData:
    def __init__(self, settings_instance):
        super().__init__()

        self.download_thread = None
        self.language_name = None
        self.thread_is_running = False

        # Dependency Injection for settings method, injects an instance of SettingsUI class into this class
        self.settings_instance = settings_instance

        self.github_tessdata_best_link = "https://raw.githubusercontent.com/tesseract-ocr/tessdata_best/main/"

    def check_download_thread(self):
        # Check if the download thread is running
        self.thread_is_running = False
        if self.download_thread is not None and self.download_thread.isRunning():
            logger.warning("Download thread is already running")
            self.thread_is_running = True
            return

    def start_download_thread(self, download_destination, file_name):
        self.check_download_thread()

        download_url = f'{self.github_tessdata_best_link}{file_name}'
        self.settings_instance.toggle_download_button_progress_bar(True)

        self.download_thread = DownloadThread(download_url, str(download_destination), file_name)
        self.download_thread.progress_signal.connect(self.settings_instance.update_progress_bar)
        self.download_thread.error_signal.connect(self.update_settings_element)
        self.download_thread.finished.connect(self.cleanup_download_thread)
        self.download_thread.start()

    def update_settings_element(self):
        logger.error("Updating settings element")
        self.settings_instance.toggle_download_button_progress_bar(False)
        self.cleanup_download_thread()

    def cleanup_download_thread(self):
        if self.download_thread is not None:
            logger.info("Cleanup download thread")
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
            with requests.get(self.url, stream=True, timeout=10) as response:
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
