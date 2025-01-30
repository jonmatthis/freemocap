from typing import Dict

from pydantic import BaseModel, Field
from skellycam import CameraId

from freemocap.pipelines.calibration_pipeline.calibration_camera_node_output_data import CalibrationCameraNodeOutputData

MultiFrameNumber = int
class TargetViewByCamera(BaseModel):
    multi_frame_number: MultiFrameNumber
    views_by_camera: dict[CameraId, CalibrationCameraNodeOutputData] = Field(description="Key: CameraId of cameras that can see the target, Value: CameraNodeOutputData from that camera")

    @property
    def cameras_that_can_see_target(self) -> list[CameraId]:
        return [camera_id for camera_id, camera_node_output in self.views_by_camera.items() if camera_node_output.can_see_target]

    @property
    def multiple_cameras_can_see_target(self) -> bool:
        return len(self.cameras_that_can_see_target) > 1


class SharedViewAccumulator(BaseModel):
    """
    Keeps track of the data feeds from each camera, and keeps track of the frames where each can see the calibration target,
    and counts the number of shared views each camera has with each other camera (i.e. frames where both cameras can see the target)
    """
    camera_ids: list[CameraId]
    shared_views_by_frame: dict[MultiFrameNumber, TargetViewByCamera]


    @classmethod
    def create(cls, camera_ids: list[CameraId]):
        return cls(camera_ids=camera_ids, shared_views_by_frame={})


    @property
    def shared_view_count_by_camera(self) -> dict[CameraId, int]:
        shared_view_count_by_camera = {camera_id: 0 for camera_id in self.camera_ids}
        for shared_view_by_frame in self.shared_views_by_frame.values():
            if shared_view_by_frame.multiple_cameras_can_see_target:
                for camera_id in shared_view_by_frame.cameras_that_can_see_target:
                    shared_view_count_by_camera[camera_id] += 1
        return shared_view_count_by_camera

    @property
    def shared_target_views(self) -> list[TargetViewByCamera]:
        return [shared_view_by_frame for shared_view_by_frame in self.shared_views_by_frame.values() if shared_view_by_frame.multiple_cameras_can_see_target]

    def receive_camera_node_output(self, multi_frame_number: int,
                                   camera_node_output: dict[CameraId, CalibrationCameraNodeOutputData]):
        cameras_that_can_see_target = {camera_id: camera_node_output for camera_id, camera_node_output in camera_node_output.items() if camera_node_output.can_see_target}
        self.shared_views_by_frame[multi_frame_number] = TargetViewByCamera(multi_frame_number=multi_frame_number, views_by_camera=cameras_that_can_see_target)

    def all_cameras_have_min_shared_views(self, min_shared_views: int) -> bool:
        return all(shared_views >= min_shared_views for shared_views in self.shared_view_count_by_camera.values())

