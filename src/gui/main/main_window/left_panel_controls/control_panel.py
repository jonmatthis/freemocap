from PyQt6.QtWidgets import (
    QFrame,
    QStackedLayout,
    QVBoxLayout,
    QTabWidget,
    QLabel,
    QToolBox,
)
from pyqtgraph.parametertree import ParameterTree, Parameter

from src.cameras.detection.cam_singleton import get_or_create_cams
from src.config.webcam_config import WebcamConfig
from src.gui.icis_conference_main.state.app_state import APP_STATE
from src.gui.main.main_window.left_panel_controls.toolbox_widgets.calibrate_capture_volume_panel import (
    CalibrateCaptureVolumePanel,
)
from src.gui.main.main_window.left_panel_controls.toolbox_widgets.camera_setup_control_panel import (
    CameraSetupControlPanel,
)
from src.gui.main.main_window.left_panel_controls.toolbox_widgets.create_new_session_panel import (
    CreateNewSessionPanel,
)
from src.gui.main.main_window.left_panel_controls.toolbox_widgets.welcome_tab import (
    SelectWorkflowScreen,
)
from src.gui.main.qt_utils.clear_layout import clear_layout


class ControlPanel:
    def __init__(self):
        self._frame = QFrame()
        self._frame.setFrameShape(QFrame.Shape.StyledPanel)
        self._layout = QVBoxLayout()

        self._select_workflow_screen = SelectWorkflowScreen()
        self._select_workflow_screen.start_new_session_button.clicked.connect(
            self._start_standard_workflow
        )

        self._create_new_session_panel = CreateNewSessionPanel()
        self._camera_setup_control_panel = CameraSetupControlPanel()
        self._calibrate_capture_volume_panel = CalibrateCaptureVolumePanel()

        self._layout.addWidget(self._select_workflow_screen)
        self._frame.setLayout(self._layout)

    @property
    def frame(self):
        return self._frame

    @property
    def select_workflow_screen(self):
        return self._select_workflow_screen

    @property
    def camera_setup_control_panel(self):
        return self._camera_setup_control_panel

    @property
    def create_new_session_panel(self):
        return self._create_new_session_panel

    @property
    def calibrate_capture_volume_panel(self):
        return self._calibrate_capture_volume_panel

    @property
    def toolbox_widget(self):
        return self._toolbox_widget

    def _start_standard_workflow(self):
        clear_layout(self._layout)
        self._create_toolbox_widget()

    def _create_toolbox_widget(self):
        self._toolbox_widget = QToolBox()

        self._toolbox_widget.addItem(
            self._create_new_session_panel, "Create New Session"
        )

        self._toolbox_widget.addItem(self._camera_setup_control_panel, "Camera Setup")

        self._toolbox_widget.addItem(
            self._calibrate_capture_volume_panel, "Calibrate Capture Volume"
        )

        self._toolbox_widget.addItem(
            QLabel("Record FreeMoCap Session"), "Record Synchronized Videos"
        )
        self._toolbox_widget.addItem(QLabel("Process Data"), "Process Data")

        self._toolbox_widget.addItem(
            QLabel("View Motion Capture Data"), "View Motion Capture Data"
        )

        self._layout.addWidget(self._toolbox_widget)

    def update_camera_configs(self):
        self._camera_setup_control_panel.update_camera_configs()
