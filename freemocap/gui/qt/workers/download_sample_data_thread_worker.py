import logging
import threading
from pathlib import Path
from typing import Union

from PyQt6.QtCore import pyqtSignal, QThread

from freemocap.tests.utilities.load_sample_data import load_sample_data
from freemocap.system.paths_and_files_names import FIGSHARE_SAMPLE_DATA_ZIP_FILE_URL

logger = logging.getLogger(__name__)


class DownloadSampleDataThreadWorker(QThread):
    finished = pyqtSignal()
    in_progress = pyqtSignal(str)

    def __init__(
        self,
        kill_thread_event: threading.Event,
    ):
        super().__init__()
        logger.info(
            f"Initializing download sample data thread worker"
        )
        self._kill_thread_event = kill_thread_event

        self._work_done = False

    @property
    def work_done(self):
        return self._work_done

    def _emit_in_progress_data(self, message: str):
        self.in_progress.emit(message)

    def run(self):
        logger.info("Downloading sample data")

        try:
            self.sample_data_path = load_sample_data(sample_data_zip_file_url=FIGSHARE_SAMPLE_DATA_ZIP_FILE_URL)


        except Exception as e:
            logger.exception("Something went wrong while downloading sample data")
            logger.exception(e)

        self.finished.emit()
        self._work_done = True

        logger.info("Sample data successfully downloaded")

