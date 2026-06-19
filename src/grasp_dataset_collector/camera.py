from __future__ import annotations

import datetime as dt
from typing import Protocol

import numpy as np


class Camera(Protocol):
    def start(self) -> None:
        ...

    def read_color_frame(self) -> np.ndarray:
        ...

    def close(self) -> None:
        ...


class RealSenseCamera:
    def __init__(self, width: int, height: int, fps: int) -> None:
        self.width = width
        self.height = height
        self.fps = fps
        self._pipeline = None

    def start(self) -> None:
        try:
            import pyrealsense2 as rs
        except ImportError as exc:
            raise RuntimeError("未安装 pyrealsense2，请先执行 `pip install -r requirements.txt`。") from exc

        self._rs = rs
        self._pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.color, self.width, self.height, rs.format.bgr8, self.fps)
        self._pipeline.start(config)

    def read_color_frame(self) -> np.ndarray:
        if self._pipeline is None:
            raise RuntimeError("RealSenseCamera 尚未启动。")

        frames = self._pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        if not color_frame:
            raise RuntimeError("未读取到 RealSense 彩色帧。")
        return np.asanyarray(color_frame.get_data())

    def close(self) -> None:
        if self._pipeline is not None:
            self._pipeline.stop()
            self._pipeline = None


class MockCamera:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self._counter = 0

    def start(self) -> None:
        pass

    def read_color_frame(self) -> np.ndarray:
        self._counter += 1
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        frame[:, :, 0] = 48
        frame[:, :, 1] = 48
        frame[:, :, 2] = 48
        x0 = 80 + (self._counter * 4) % max(1, self.width - 240)
        y0 = self.height // 2 - 80
        frame[y0 : y0 + 160, x0 : x0 + 160] = (230, 230, 230)

        timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _put_text(frame, f"MOCK CAMERA {timestamp}", (24, 42))
        _put_text(frame, f"frame={self._counter}", (24, 82))
        return frame

    def close(self) -> None:
        pass


def build_camera(config: dict) -> Camera:
    camera_config = config["camera"]
    camera_type = camera_config.get("type", "realsense")
    width = int(camera_config.get("width", 1280))
    height = int(camera_config.get("height", 720))
    fps = int(camera_config.get("fps", 30))

    if camera_type == "realsense":
        return RealSenseCamera(width=width, height=height, fps=fps)
    if camera_type == "mock":
        return MockCamera(width=width, height=height)
    raise ValueError(f"不支持的 camera.type: {camera_type}")


def _put_text(frame: np.ndarray, text: str, origin: tuple[int, int]) -> None:
    try:
        import cv2
    except ImportError:
        return

    cv2.putText(
        frame,
        text,
        origin,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
