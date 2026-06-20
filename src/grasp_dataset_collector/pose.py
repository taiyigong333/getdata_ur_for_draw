from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class TCPPose:
    x: float
    y: float
    z: float
    rx: float
    ry: float
    rz: float

    def to_annotation(self) -> dict[str, dict[str, float]]:
        return {
            "position": {
                "x": round(self.x, 6),
                "y": round(self.y, 6),
                "z": round(self.z, 6),
            },
            "orientation": {
                "rx": round(self.rx, 6),
                "ry": round(self.ry, 6),
                "rz": round(self.rz, 6),
            },
        }


class PoseReader(Protocol):
    def start(self) -> None:
        ...

    def read_tcp_pose(self) -> TCPPose:
        ...

    def close(self) -> None:
        ...


class RTDEPoseReader:
    def __init__(self, host: str, port: int = 30004) -> None:
        self.host = host
        self.port = port
        self._receiver = None

    def start(self) -> None:
        try:
            from rtde_receive import RTDEReceiveInterface
        except ImportError as exc:
            raise RuntimeError("ur-rtde is not installed. Run `pip install -r requirements.txt`.") from exc

        self._receiver = RTDEReceiveInterface(self.host, self.port)

    def read_tcp_pose(self) -> TCPPose:
        if self._receiver is None:
            raise RuntimeError("RTDEPoseReader has not been started.")

        pose = self._receiver.getActualTCPPose()
        if len(pose) != 6:
            raise RuntimeError(f"RTDE returned an invalid TCP pose length: {len(pose)}")

        x, y, z, rx, ry, rz = [float(v) for v in pose]
        return TCPPose(x=x, y=y, z=z, rx=rx, ry=ry, rz=rz)

    def close(self) -> None:
        self._receiver = None


class MockPoseReader:
    def start(self) -> None:
        pass

    def read_tcp_pose(self) -> TCPPose:
        t = time.time()
        return TCPPose(
            x=0.35 + math.sin(t) * 0.005,
            y=-0.12,
            z=0.21,
            rx=0.0,
            ry=90.0,
            rz=0.0,
        )

    def close(self) -> None:
        pass


def build_pose_reader(config: dict) -> PoseReader:
    robot_config = config["robot"]
    robot_type = robot_config.get("type", "rtde")
    if robot_type == "rtde":
        return RTDEPoseReader(
            host=robot_config["rtde_host"],
            port=int(robot_config.get("rtde_port", 30004)),
        )
    if robot_type == "mock":
        return MockPoseReader()
    raise ValueError(f"Unsupported robot.type: {robot_type}")
