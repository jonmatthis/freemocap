import logging
import multiprocessing
from pathlib import Path
from typing import Union

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDockWidget, QLabel, QMainWindow
from skellycam import (
    SkellyCamControllerWidget,
    SkellyCamParameterTreeWidget,
    SkellyCamViewerWidget,
)
from skellycam.qt_gui.widgets.qt_directory_view_widget import QtDirectoryViewWidget

from freemocap.configuration.paths_and_files_names import (
    create_new_session_folder,
    get_css_stylesheet_path,
    get_freemocap_data_folder_path,
)
from freemocap.core_processes.session_processing_parameter_models.session_processing_parameter_models import (
    SessionProcessingParameterModel,
)
from freemocap.qt_gui.main_window.central_tab_widget import CentralTabWidget
from freemocap.qt_gui.main_window.control_panel_dock_widget import (
    ControlPanelDockWidget,
)
from freemocap.qt_gui.style_sheet.css_file_watcher import CSSFileWatcher
from freemocap.qt_gui.style_sheet.set_css_style_sheet import apply_css_style_sheet
from freemocap.qt_gui.sub_widgets.calibration_control_panel import (
    CalibrationControlPanel,
)
from freemocap.qt_gui.sub_widgets.process_mocap_data_panel.process_motion_capture_data_panel import (
    ProcessMotionCaptureDataPanel,
)
from freemocap.qt_gui.sub_widgets.welcome_tab_widget import (
    WelcomeCreateOrLoadNewSessionPanel,
)
from freemocap.qt_gui.utilities.save_most_recent_recording_path_as_toml import (
    save_most_recent_recording_path_as_toml,
)

logger = logging.getLogger(__name__)


class QtGUIMainWindow(QMainWindow):
    def __init__(
        self,
        session_path: Union[str, Path] = None,
        session_process_parameter_model: SessionProcessingParameterModel = SessionProcessingParameterModel(),
        freemocap_data_folder: Union[str, Path] = None,
        parent=None,
    ):

        logger.info("Initializing QtGUIMainWindow")
        super().__init__(parent=parent)
        self.setGeometry(100, 100, 1600, 900)

        self._css_file_watcher = self._set_up_stylesheet()

        if session_path is None:
            self._session_path = Path(create_new_session_folder())
        else:
            self._session_path = Path(session_path)

        self._session_process_parameter_model = session_process_parameter_model

        if freemocap_data_folder is None:
            self._freemocap_data_folder = get_freemocap_data_folder_path()
        else:
            self._freemocap_data_folder = freemocap_data_folder

        self.setWindowTitle("freemocap \U0001F480 \U00002728")

        self._central_tab_widget = self._create_center_tab_widget()
        self.setCentralWidget(self._central_tab_widget)

        self._control_panel_dock_widget = self._create_control_panel_dock_widget()
        self.addDockWidget(
            Qt.DockWidgetArea.LeftDockWidgetArea, self._control_panel_dock_widget
        )

        self._directory_view_dock_widget = self._create_directory_view_dock_widget()
        self.addDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea, self._directory_view_dock_widget
        )

        self._connect_signals_to_slots()

    def _connect_signals_to_slots(self):
        self._welcome_to_freemocap_widget.quick_start_button.clicked.connect(
            self._handle_quick_start_button_clicked
        )

        self._camera_view_widget.videos_saved_signal.connect(
            save_most_recent_recording_path_as_toml
        )

    def _handle_quick_start_button_clicked(self):
        self._central_tab_widget.set_welcome_tab_enabled(False)
        self._central_tab_widget.set_camera_view_tab_enabled(True)
        self._central_tab_widget.setCurrentIndex(1)

        self._camera_view_widget.connect_to_cameras()

    def _set_up_stylesheet(self):
        apply_css_style_sheet(self, get_css_stylesheet_path())

        css_file_watcher = CSSFileWatcher(
            path_to_css_file=get_css_stylesheet_path(), parent=self
        )

        return css_file_watcher

    def _create_center_tab_widget(self):
        self._camera_view_widget = SkellyCamViewerWidget(
            parent=self, session_folder_path=self._session_path
        )
        self._camera_controller_widget = SkellyCamControllerWidget(
            camera_viewer_widget=self._camera_view_widget,
            parent=self,
        )

        self._welcome_to_freemocap_widget = WelcomeCreateOrLoadNewSessionPanel()
        self._visualize_data_widget = QLabel("Visualize Data")

        center_tab_widget = CentralTabWidget(
            parent=self,
            camera_view_widget=self._camera_view_widget,
            camera_controller_widget=self._camera_controller_widget,
            welcome_to_freemocap_widget=self._welcome_to_freemocap_widget,
            visualize_data_widget=self._visualize_data_widget,
        )

        center_tab_widget.set_welcome_tab_enabled(True)
        center_tab_widget.set_camera_view_tab_enabled(False)
        center_tab_widget.set_visualize_data_tab_enabled(False)

        return center_tab_widget

    def _create_control_panel_dock_widget(self):
        self._camera_configuration_parameter_tree_widget = SkellyCamParameterTreeWidget(
            self._camera_view_widget
        )
        self._calibration_control_panel = CalibrationControlPanel()
        self._process_motion_capture_data_panel = ProcessMotionCaptureDataPanel(
            session_processing_parameters=self._session_process_parameter_model
        )

        left_side_control_panel_dock_widget = ControlPanelDockWidget(
            camera_configuration_parameter_tree_widget=self._camera_configuration_parameter_tree_widget,
            calibration_control_panel=self._calibration_control_panel,
            process_motion_capture_data_panel=self._process_motion_capture_data_panel,
            visualize_data_widget=QLabel("Visualize Data"),
            parent=self,
        )

        return left_side_control_panel_dock_widget

    def _create_directory_view_dock_widget(self):
        directory_view_dock_widget = QDockWidget("Directory View", self)
        self._qt_directory_view_widget = QtDirectoryViewWidget(
            folder_path=self._freemocap_data_folder
        )
        directory_view_dock_widget.setWidget(self._qt_directory_view_widget)

        return directory_view_dock_widget

    def closeEvent(self, a0) -> None:
        if not any(Path(self._session_path).iterdir()):
            logger.info(f"Session folder: {self._session_path} is empty, removing it")
            Path(self._session_path).rmdir()

        try:
            self._camera_view_widget.close()
        except Exception as e:
            logger.error(f"Error while closing the viewer widget: {e}")
        super().closeEvent(a0)


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    main_window = QtGUIMainWindow()
    main_window.show()
    app.exec()
    for process in multiprocessing.active_children():
        logger.info(f"Terminating process: {process}")
        process.terminate()
    sys.exit()
