import logging
import multiprocessing
from pathlib import Path

from PyQt6.QtCore import pyqtSignal, QThread

from freemocap.core_processes.process_motion_capture_videos.process_recording_folder import (
    process_recording_folder,


logger = logging.getLogger(__name__)


class ProcessMotionCaptureDataThreadWorker(QThread):
    finished = pyqtSignal()
    in_progress = pyqtSignal(str)

    def __init__(self, post_processing_parameters: PostProcessingParameterModel,
                 kill_event: multiprocessing.Event, parent=None):
        super().__init__()
        self._post_processing_parameters = post_processing_parameters
        self._kill_event = kill_event

        self._queue = multiprocessing.Queue()

        self._process = multiprocessing.Process(target=process_recording_folder,
                                                args=(self._post_processing_parameters,
                                                      self._kill_event,
                                                      self._queue))


    def run(self):
        logger.info(
            f"Beginning processing of motion capture data with parameters: {self._post_processing_parameters.__dict__}"
        )
        self._kill_event.clear()

        recording_info_dict = self._post_processing_parameters.dict(exclude={'recording_info_model'})
        Path(self._post_processing_parameters.recording_info_model.output_data_folder_path).mkdir(parents=True, exist_ok=True)


        save_dictionary_to_json(
            save_path=self._post_processing_parameters.recording_info_model.output_data_folder_path,
            file_name=RECORDING_PARAMETERS_JSON_FILE_NAME,
            dictionary=recording_info_dict,
        )

        try:
            self._process.start()
            while self._process.is_alive():
                time.sleep(0.01)
                if self._queue.empty():
                    continue
                else:
                    message = self._queue.get()
                    self.in_progress.emit(message)

            while not self._queue.empty():
                message = self._queue.get()
                self.in_progress.emit(message)

        except Exception as e:
            logger.error(f"Error processing motion capture data: {str(e)}")

        logger.info("Finished processing session folder!")

        self.finished.emit()
