from __future__ import annotations

import datetime as dt
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from .pose import TCPPose


SAMPLE_PATTERN = re.compile(r"^sample_(\d{5})$")


@dataclass
class AfterCapture:
    path: str
    tcp_pose: TCPPose
    timestamp: str


@dataclass
class SampleSession:
    sample_id: str
    sample_dir: Path
    image_dir: Path
    before_path: str | None = None
    after_captures: list[AfterCapture] = field(default_factory=list)

    @property
    def annotation_path(self) -> Path:
        return self.sample_dir / "annotation.json"


class DatasetWriter:
    def __init__(self, dataset_root: str | Path, metadata: dict[str, Any], sample_defaults: dict[str, Any]) -> None:
        self.dataset_root = Path(dataset_root)
        self.samples_dir = self.dataset_root / "samples"
        self.metadata = metadata
        self.sample_defaults = sample_defaults
        self._current: SampleSession | None = None

    def prepare(self) -> None:
        self.samples_dir.mkdir(parents=True, exist_ok=True)
        metadata_path = self.dataset_root / "dataset_metadata.json"
        if not metadata_path.exists():
            _write_json(metadata_path, self.metadata)

    def open_next_sample(self) -> SampleSession:
        next_index = self._next_sample_index()
        sample_id = f"sample_{next_index:05d}"
        sample_dir = self.samples_dir / sample_id
        image_dir = sample_dir / "images"
        image_dir.mkdir(parents=True, exist_ok=False)
        self._current = SampleSession(sample_id=sample_id, sample_dir=sample_dir, image_dir=image_dir)
        return self._current

    def save_before(self, frame: np.ndarray) -> SampleSession:
        session = self._require_current()
        path = session.image_dir / "before.png"
        _write_image(path, frame)
        session.before_path = "images/before.png"
        # before 代表当前样本起点，多次按 1 时清空已拍的成功图，避免混入上一轮状态。
        for capture in session.after_captures:
            old_path = session.sample_dir / capture.path
            if old_path.exists():
                old_path.unlink()
        session.after_captures.clear()
        return session

    def save_after(self, frame: np.ndarray, tcp_pose: TCPPose, timestamp: str) -> SampleSession:
        session = self._require_current()
        after_index = len(session.after_captures) + 1
        relative_path = f"images/after_{after_index:02d}.png"
        _write_image(session.sample_dir / relative_path, frame)
        session.after_captures.append(AfterCapture(path=relative_path, tcp_pose=tcp_pose, timestamp=timestamp))
        return session

    def finalize_current(self) -> Path:
        session = self._require_current()
        if session.before_path is None:
            raise RuntimeError("当前 sample 缺少 before.png，请先按 1 采集初始固定视角图片。")
        if not session.after_captures:
            raise RuntimeError("当前 sample 缺少 after 图片，请先按 2 采集成功图片和 TCP。")

        last_success = session.after_captures[-1]
        extra_meta = {
            "object_type": self.sample_defaults.get("object_type", "unknown"),
            "capture_timestamp": last_success.timestamp,
            "arm_model": self.sample_defaults.get("arm_model", "unknown"),
            "tcp_set": self.sample_defaults.get("tcp_set", []),
            "after_captures": [
                {
                    "path": capture.path,
                    "capture_timestamp": capture.timestamp,
                    "tcp_pose": capture.tcp_pose.to_annotation(),
                }
                for capture in session.after_captures
            ],
        }

        annotation = {
            "sample_id": session.sample_id,
            "language_instruction": self.sample_defaults.get("language_instruction", ""),
            "image_paths": {
                "before": session.before_path,
                "after_list": [capture.path for capture in session.after_captures],
            },
            "grasp_success_tcp_pose": last_success.tcp_pose.to_annotation(),
            "extra_meta": extra_meta,
        }
        _write_json(session.annotation_path, annotation)
        self._current = None
        return session.annotation_path

    def _require_current(self) -> SampleSession:
        if self._current is None:
            return self.open_next_sample()
        return self._current

    def _next_sample_index(self) -> int:
        max_index = 0
        if self.samples_dir.exists():
            for child in self.samples_dir.iterdir():
                if child.is_dir():
                    match = SAMPLE_PATTERN.match(child.name)
                    if match:
                        max_index = max(max_index, int(match.group(1)))
        return max_index + 1


def current_timestamp() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _write_image(path: Path, frame: np.ndarray) -> None:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("未安装 opencv-python，请先执行 `pip install -r requirements.txt`。") from exc

    path.parent.mkdir(parents=True, exist_ok=True)
    success = cv2.imwrite(str(path), frame)
    if not success:
        raise RuntimeError(f"图片写入失败: {path}")
