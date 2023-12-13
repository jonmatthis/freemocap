import logging
import multiprocessing
from pathlib import Path
import numpy as np

from freemocap.core_processes.detecting_things_in_2d_images.mediapipe_stuff.mediapipe_skeleton_detector import (
    MediaPipeSkeletonDetector,
)

from freemocap.core_processes.detecting_things_in_2d_images.mediapipe_stuff.process_folder_of_videos import (
    process_folder_of_videos
)

from freemocap.data_layer.recording_models.post_processing_parameter_models import (
    MediapipeParametersModel,
    ProcessingParameterModel,
)
from freemocap.system.logging.queue_logger import DirectQueueHandler
from freemocap.system.logging.configure_logging import log_view_logging_format_string
from freemocap.system.paths_and_filenames.file_and_folder_names import RAW_DATA_FOLDER_NAME

from skelly_tracker.trackers.mediapipe_tracker.mediapipe_holistic_tracker import MediapipeHolisticTracker

logger = logging.getLogger(__name__)


def get_image_data(
    processing_parameters: ProcessingParameterModel,
    kill_event: multiprocessing.Event,
    queue: multiprocessing.Queue,
    use_tqdm: bool,
) -> np.ndarray:
    if queue:
        handler = DirectQueueHandler(queue)
        handler.setFormatter(logging.Formatter(fmt=log_view_logging_format_string, datefmt="%Y-%m-%dT%H:%M:%S"))
        logger.addHandler(handler)

    if processing_parameters.mediapipe_parameters_model.skip_2d_image_tracking:
        logger.info(
            f"Skipping 2d skeleton detection and loading data from: {processing_parameters.recording_info_model.mediapipe_2d_data_npy_file_path}"
        )
        try:
            image_data_numCams_numFrames_numTrackedPts_XYZ = np.load(
                processing_parameters.recording_info_model.mediapipe_2d_data_npy_file_path
            )
        except Exception as e:
            logger.error(e)
            logger.error("Failed to load 2D data, cannot continue processing", exc_info=True)
            return
    else:
        logger.info("Detecting 2d skeletons...")
        # 2d skeleton detection
        image_data_numCams_numFrames_numTrackedPts_XYZ = run_image_tracking(
            tracking_params=processing_parameters.mediapipe_parameters_model,
            synchronized_videos_folder_path=processing_parameters.recording_info_model.synchronized_videos_folder_path,
            output_data_folder_path=Path(processing_parameters.recording_info_model.output_data_folder_path)
            / RAW_DATA_FOLDER_NAME,
            kill_event=kill_event,
            use_tqdm=use_tqdm,
        )

    return image_data_numCams_numFrames_numTrackedPts_XYZ


def run_image_tracking(
    tracking_params: MediapipeParametersModel,
    synchronized_videos_folder_path: Path,
    output_data_folder_path: Path,
    kill_event: multiprocessing.Event = None,
    use_tqdm: bool = True,
):
#     mediapipe_skeleton_detector = MediaPipeSkeletonDetector(
#         parameter_model=tracking_params,
#         use_tqdm=use_tqdm,
#     )

    # mediapipe_tracker = MediapipeHolisticTracker(
    #     model_complexity=tracking_params.mediapipe_model_complexity,
    #     min_detection_confidence=tracking_params.min_detection_confidence,
    #     min_tracking_confidence=tracking_params.min_tracking_confidence,
    #     static_image_mode=tracking_params.static_image_mode,
    # )

    # tracker_type = 'MediapipeHolisticTracker'
    tracker_type = 'YOLOMediapipeComboTracker'

    mediapipe_image_data_numCams_numFrames_numTrackedPts_XYZ = process_folder_of_videos(
        tracker_type = tracker_type,
        tracking_params=tracking_params,
        synchronized_video_path=synchronized_videos_folder_path,
        output_path=output_data_folder_path,
        annotated_video_path=None,
        use_multiprocessing=tracking_params.use_multiprocessing,
    )
        
    
    # mediapipe_image_data_numCams_numFrames_numTrackedPts_XYZ = (
    #     mediapipe_skeleton_detector.process_folder_full_of_videos(
    #         path_to_folder_of_videos_to_process=synchronized_videos_folder_path,
    #         output_data_folder_path=output_data_folder_path,
    #         kill_event=kill_event,
    #         use_multiprocessing=tracking_params.use_multiprocessing,
    #     )
    # )

    return mediapipe_image_data_numCams_numFrames_numTrackedPts_XYZ
