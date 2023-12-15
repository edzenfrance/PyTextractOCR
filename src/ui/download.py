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

        self.download_worker = None
        self.threads = []

        # Dependency Injection for settings method, injects an instance of SettingsUI class into this class
        self.settings_instance = settings_instance

        self.github_tessdata_best_url = "https://raw.githubusercontent.com/tesseract-ocr/tessdata_best/main/"

    def start_download_worker(self, language, destination, file_name):
        url = f'{self.github_tessdata_best_url}{file_name}'
        self.settings_instance.toggle_download_button_progress_bar(language, True)

        self.download_worker = DownloadWorker(url, str(destination), file_name, language)
        self.download_worker.progress_signal.connect(self.settings_instance.update_progress_bar)
        self.download_worker.error_signal.connect(self.download_failed)
        self.download_worker.finished.connect(self.thread_finished)
        self.download_worker.start()
        self.threads.append(self.download_worker)

    def download_failed(self, language):
        logger.error(f"Downloading '{language}' language failed")
        self.settings_instance.toggle_download_button_progress_bar(language, False)

    def thread_finished(self):
        for self.download_worker in self.threads:
            if not self.download_worker.isRunning():
                self.threads.remove(self.download_worker)
                logger.info(f"Running Threads: {self.threads}")
                del self.download_worker


class DownloadWorker(QThread):
    progress_signal = Signal(str, int)
    error_signal = Signal(str)

    def __init__(self, url, destination, filename, language):
        super().__init__()

        self.url = url
        self.destination = destination
        self.filename = filename
        self.language = language

        self.file_size = self.get_file_size()
        self.headers = {'Range': f'bytes={self.file_size}-'}

    def get_file_size(self):
        try:
            return Path(self.destination).stat().st_size
        except FileNotFoundError:
            return 0

    def run(self):
        try:
            logger.info(f"Downloading '{self.language}' language from github: {self.url}")

            with requests.get(self.url, headers=self.headers, stream=True, timeout=30) as response:
                response.raise_for_status()
                remaining_size = int(response.headers.get('content-length', 0))
                downloaded_size = self.file_size
                total_size = downloaded_size + remaining_size
                logger.info(f"Destination: {self.destination} - Downloaded: {downloaded_size} - Remaining: {remaining_size} - Total: {total_size}")

                mode = 'ab' if response.status_code == 206 else 'wb'
                with open(self.destination, mode) as file:
                    for chunk in response.iter_content(chunk_size=1024):
                        downloaded_size = self.write_to_file(file, chunk, downloaded_size, total_size)

                logger.success(f"Downloading '{self.language}' language completed")
                self.rename_temp_file()
        except (ConnectionError, TimeoutError, requests.exceptions.RequestException) as e:
            error_type = "Connection error" if isinstance(e, ConnectionError) else (
                "Timeout error" if isinstance(e, TimeoutError) else "Request error")
            logger.error(f"{error_type}: {e}")
            self.error_signal.emit(self.language)

    def write_to_file(self, file, data, downloaded_size, total_size):
        file.write(data)
        downloaded_size += len(data)
        progress_percentage = int(downloaded_size / total_size * 100)
        self.progress_signal.emit(self.language, progress_percentage)
        return downloaded_size  # Return the value so that run can track it correctly

    def rename_temp_file(self):
        tessdata_folder = Path('./tessdata')
        current_file_path = tessdata_folder / f'{self.filename}.tmp'
        new_file_path = tessdata_folder / self.filename
        try:
            shutil.move(current_file_path, new_file_path)
            logger.success(f"The file '{self.filename}.tmp' has been renamed to '{self.filename}'.")
        except Exception as e:
            logger.error(f"Failed to rename the file '{self.filename}.tmp': {e}")
