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
    def __init__(self, host: str, port: int = 30004, orientation_input: str = "rotation_vector_rad") -> None:
        self.host = host
        self.port = port
        self.orientation_input = orientation_input
        self._receiver = None

    def start(self) -> None:
        try:
            from rtde_receive import RTDEReceiveInterface
        except ImportError as exc:
            raise RuntimeError("未安装 ur-rtde，请先执行 `pip install -r requirements.txt`。") from exc

        self._receiver = RTDEReceiveInterface(self.host, self.port)

    def read_tcp_pose(self) -> TCPPose:
        if self._receiver is None:
            raise RuntimeError("RTDEPoseReader 尚未启动。")

        pose = self._receiver.getActualTCPPose()
        if len(pose) != 6:
            raise RuntimeError(f"RTDE 返回的 TCP 位姿长度异常: {len(pose)}")

        x, y, z, rx, ry, rz = [float(v) for v in pose]
        if self.orientation_input == "rotation_vector_rad":
            rx, ry, rz = rotation_vector_to_fixed_xyz_euler_deg(rx, ry, rz)
        elif self.orientation_input == "euler_degree":
            pass
        else:
            raise ValueError(f"不支持的 orientation_input: {self.orientation_input}")

        return TCPPose(x=x, y=y, z=z, rx=rx, ry=ry, rz=rz)

    def close(self) -> None:
        # ur_rtde 的接收接口通常无需显式关闭；保留方法便于统一生命周期。
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
            orientation_input=robot_config.get("orientation_input", "rotation_vector_rad"),
        )
    if robot_type == "mock":
        return MockPoseReader()
    raise ValueError(f"不支持的 robot.type: {robot_type}")


def rotation_vector_to_fixed_xyz_euler_deg(rx: float, ry: float, rz: float) -> tuple[float, float, float]:
    matrix = _rotation_vector_to_matrix(rx, ry, rz)

    # 固定轴 XYZ 欧拉角：R = Rz(gamma) * Ry(beta) * Rx(alpha)。
    sy = -matrix[2][0]
    sy = max(-1.0, min(1.0, sy))
    beta = math.asin(sy)
    cos_beta = math.cos(beta)

    if abs(cos_beta) > 1e-8:
        alpha = math.atan2(matrix[2][1], matrix[2][2])
        gamma = math.atan2(matrix[1][0], matrix[0][0])
    else:
        # 万向节锁附近 rz 不唯一，固定 rz=0 以保证输出稳定。
        alpha = math.atan2(-matrix[1][2], matrix[1][1])
        gamma = 0.0

    return tuple(math.degrees(v) for v in (alpha, beta, gamma))


def _rotation_vector_to_matrix(rx: float, ry: float, rz: float) -> list[list[float]]:
    theta = math.sqrt(rx * rx + ry * ry + rz * rz)
    if theta < 1e-12:
        return [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ]

    kx, ky, kz = rx / theta, ry / theta, rz / theta
    c = math.cos(theta)
    s = math.sin(theta)
    v = 1.0 - c

    return [
        [kx * kx * v + c, kx * ky * v - kz * s, kx * kz * v + ky * s],
        [ky * kx * v + kz * s, ky * ky * v + c, ky * kz * v - kx * s],
        [kz * kx * v - ky * s, kz * ky * v + kx * s, kz * kz * v + c],
    ]
