import logging
from pathlib import Path
from typing import List, Union

from PyQt6.QtCore import pyqtSignal, QFileSystemWatcher
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget
from pyqtgraph.parametertree import Parameter, ParameterTree

from freemocap.core_processes.session_processing_parameter_models.session_processing_parameter_models import (
    SessionInfoModel,
)
from freemocap.core_processes.session_processing_parameter_models.session_recording_info.recording_info_model import (
    RecordingInfoModel,
)

logger = logging.getLogger(__name__)


class ActiveSessionWidget(QWidget):
    new_active_recording_selected_signal = pyqtSignal(str)

    def __init__(
        self,
        active_session_info: SessionInfoModel,
        parent: QWidget = None,
    ):
        super().__init__(parent=parent)
        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._active_session_info = active_session_info
        self._active_session_directory_watcher = self._create_active_session_directory_watcher()

        self._active_session_tree_view = ActiveSessionTreeView(parent=self)
        self._layout.addWidget(self._active_session_tree_view)

        self.set_active_session(session_folder_path=self._active_session_info.session_folder_path)

    @property
    def active_session_info(self):
        return self._active_session_info

    @property
    def active_recording_info(self):
        return self._active_session_info.active_recording_info

    def get_active_session_info(self):
        return self._active_session_info

    def get_active_recording_info(self):
        # this is redundant to the `active_recording_info` property,
        # but it will be more intuitive to send this down as a callable
        # rather than relying on 'pass-by-reference' magic lol
        return self._active_session_info.active_recording_info

    def set_active_session(self, session_folder_path: Union[str, Path]):
        if not self._active_session_info.session_folder_path == session_folder_path:
            logger.info(f"Setting active session to {session_folder_path}")
            self._active_session_info = SessionInfoModel(session_folder_path=session_folder_path)

        self._active_session_tree_view.setup_parameter_tree(session_info_model=self._active_session_info)

        self._update_file_watch_path(session_folder_path=self._active_session_info.session_folder_path)

    def set_active_recording(
        self,
        recording_folder_path: Union[str, Path],
    ):

        logger.info(f"Setting active recording to {recording_folder_path}")
        self._active_session_info.set_recording_info(str(recording_folder_path))

        assert str(self._active_session_info.active_recording_info.path) == str(
            recording_folder_path
        ), "Failed to set active recording info somehow?"

        self.new_active_recording_selected_signal.emit(str(recording_folder_path))

    def _create_active_session_directory_watcher(self):

        active_session_directory_watcher = QFileSystemWatcher()
        active_session_directory_watcher.directoryChanged.connect(self._handle_directory_changed)
        return active_session_directory_watcher

    def _update_file_watch_path(self, session_folder_path: Union[str, Path]):
        logger.debug(f"Updating file watch path to: {session_folder_path}")

        if self._active_session_directory_watcher.directories():
            logger.debug(f"Removing path from watch list: {self._active_session_directory_watcher.directories()}")

        self._active_session_directory_watcher.removePaths(self._active_session_directory_watcher.directories())
        self._active_session_directory_watcher.addPath(session_folder_path)

    def _handle_directory_changed(self, path: str):
        logger.info(f"Directory changed: {path} - Updating Parameter Tree")
        self._active_session_tree_view.setup_parameter_tree(self._active_session_info)


class ActiveSessionTreeView(ParameterTree):
    def __init__(self, parent=None):
        super().__init__(parent=parent, showHeader=False)

        self.doubleClicked.connect(self._handle_double_click_event)

    def setup_parameter_tree(
        self,
        session_info_model: SessionInfoModel,
    ):
        self.clear()

        available_recordings = self._get_available_recordings(session_info_model=session_info_model)

        self.setParameters(
            self._create_parameter_tree(
                session_info_model=session_info_model,
                available_recordings=available_recordings,
            ),
        )

    def update_active_recording_name(self, active_recording_folder_path: Union[str, Path]):
        self._clear_active_recording_name()
        for recording_parameter in self._recording_parameter_trees_list:
            if recording_parameter.child("Path").value() == active_recording_folder_path:
                recording_parameter.setName(f"Recording Name: {Path(active_recording_folder_path).name} (Active)")
                self._active_session_info.set_recording_info(
                    recording_folder_path=active_recording_folder_path,
                    calibration_toml_path=recording_parameter.child("Calibration TOML").value(),
                )

    def _clear_active_recording_name(self):
        for recording_parameter in self._recording_parameter_trees_list:
            recording_parameter.setName(f"Recording Name: {Path(recording_parameter.child('Path').value()).name}")

    def _create_parameter_tree(
        self,
        session_info_model: SessionInfoModel,
        available_recordings: List[RecordingInfoModel],
    ) -> Parameter:

        if len(available_recordings) > 0 and session_info_model.active_recording_info is None:
            session_info_model.set_recording_info(recording_folder_path=available_recordings[-1])

        active_session_parameter = Parameter.create(
            name="Session Name: " + Path(session_info_model.session_folder_path).name,
            type="group",
            children=[
                dict(
                    name="Path",
                    type="str",
                    value=session_info_model.session_folder_path,
                    readonly=True,
                ),
                self._create_recording_parameter_group(
                    available_recordings=available_recordings,
                ),
            ],
        )

        return active_session_parameter

    def _get_available_recordings(self, session_info_model: SessionInfoModel) -> List[Union[str, Path]]:
        try:
            return [
                recording for recording in Path(session_info_model.session_folder_path).iterdir() if recording.is_dir()
            ]
        except Exception as e:
            logger.error(e)
            return []

    def _create_recording_parameter_group(self, available_recordings: List[Union[str, Path]]):

        if len(available_recordings) == 0:
            self._recording_parameter_trees_list = Parameter.create(
                name="No Recordings Found - Either select one in the `File View` window or Record/Import new videos to continue \U0001F4AB",
                type="group",
                readonly=True,
            )
        else:
            self._recording_parameter_trees_list = [
                self._create_recording_status_parameter_tree(RecordingInfoModel(recording_path))
                for recording_path in available_recordings
            ]
        return Parameter.create(
            name="Available Recordings",
            type="group",
            collapsed=True,
            children=self._recording_parameter_trees_list,
        )

    def _create_recording_status_parameter_tree(self, recording_info_model: RecordingInfoModel):
        parameter_group = Parameter.create(
            name=f"Recording Name: {recording_info_model.name}",
            type="group",
            readonly=True,
            children=[
                dict(
                    name="Path",
                    type="str",
                    value=recording_info_model.path,
                    readonly=True,
                ),
                dict(
                    name="Calibration TOML",
                    type="str",
                    value=recording_info_model.calibration_toml_file_path,
                    readonly=True,
                ),
                dict(
                    name="Status",
                    type="group",
                    readonly=True,
                    children=[
                        dict(
                            name="Synchronized Videos Recorded",
                            type="str",
                            value=recording_info_model.synchronized_videos_status_check,
                            readonly=True,
                        ),
                        dict(
                            name="2D data exists?",
                            type="str",
                            value=recording_info_model.data2d_status_check,
                            readonly=True,
                        ),
                        dict(
                            name="3D data exists?",
                            type="str",
                            value=recording_info_model.data3d_status_check,
                            readonly=True,
                        ),
                        dict(
                            name="Center-of-Mass data exists?",
                            type="str",
                            value=recording_info_model.center_of_mass_data_status_check,
                            readonly=True,
                        ),
                    ],
                ),
            ],
        )

        return parameter_group

    def _handle_double_click_event(self, a0: QMouseEvent) -> None:
        parameter_item = self.itemFromIndex(self.currentIndex())[0]
        logger.info(f"Double clicked on Parameter Item named: {parameter_item.param.name()}")
        parent = parameter_item
        while parent is not None:
            if "Recording Name:" in parent.param.name():
                logger.info(f"Found Recording Name: {parent.param.name()}")
                self.parent().set_active_recording(parent.param.child("Path").value())
                break
            else:
                parent = parent.parent()


if __name__ == "__main__":
    import sys
    from freemocap.configuration.paths_and_files_names import create_new_session_folder

    app = QApplication(sys.argv)
    active_session_widget = ActiveSessionWidget(
        active_session_info=SessionInfoModel(session_folder_path=create_new_session_folder())
    )
    active_session_widget.show()
    sys.exit(app.exec())
