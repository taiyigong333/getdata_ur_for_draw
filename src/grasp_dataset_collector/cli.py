from __future__ import annotations

import argparse
from pathlib import Path

from .camera import build_camera
from .config import load_config
from .dataset import DatasetWriter, current_timestamp
from .pose import build_pose_reader


def main() -> int:
    parser = argparse.ArgumentParser(description="固定视角夹取成功数据采集工具")
    parser.add_argument("--config", default="configs/default.json", help="采集配置 JSON 路径")
    parser.add_argument("--no-preview", action="store_true", help="不显示摄像头预览，仅按固定流程采集")
    args = parser.parse_args()

    config = load_config(args.config)
    writer = DatasetWriter(
        dataset_root=config["dataset_root"],
        metadata=config["dataset_metadata"],
        sample_defaults=config["sample_defaults"],
    )
    camera = build_camera(config)
    pose_reader = build_pose_reader(config)

    writer.prepare()
    camera.start()
    pose_reader.start()

    preview_window = config["camera"].get("preview_window", "grasp dataset collector")
    print("采集工具已启动。按 1 采集/重置 before，按 2 采集 after+TCP，按 n 完成当前 sample，按 q 退出。")

    try:
        if args.no_preview:
            return _run_without_preview(writer, camera, pose_reader)
        return _run_with_preview(writer, camera, pose_reader, preview_window)
    finally:
        pose_reader.close()
        camera.close()
        _close_preview_windows()


def _run_with_preview(writer: DatasetWriter, camera, pose_reader, preview_window: str) -> int:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("预览模式需要 opencv-python，请先执行 `pip install -r requirements.txt`。") from exc

    while True:
        frame = camera.read_color_frame()
        cv2.imshow(preview_window, frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("1"):
            session = writer.save_before(frame)
            print(f"[{session.sample_id}] 已保存 before.png；该 sample 的 after 记录已重置。")
        elif key == ord("2"):
            timestamp = current_timestamp()
            tcp_pose = pose_reader.read_tcp_pose()
            session = writer.save_after(frame, tcp_pose=tcp_pose, timestamp=timestamp)
            print(f"[{session.sample_id}] 已保存 after_{len(session.after_captures):02d}.png 和实时 TCP。")
        elif key in (ord("n"), ord("N")):
            try:
                annotation_path = writer.finalize_current()
                print(f"当前 sample 已完成: {annotation_path}")
            except RuntimeError as exc:
                print(f"无法完成当前 sample: {exc}")
        elif key in (ord("q"), ord("Q"), 27):
            return 0


def _run_without_preview(writer: DatasetWriter, camera, pose_reader) -> int:
    print("无预览模式：输入 1/2/n/q 后回车。")
    while True:
        command = input("> ").strip().lower()
        frame = camera.read_color_frame()

        if command == "1":
            session = writer.save_before(frame)
            print(f"[{session.sample_id}] 已保存 before.png；该 sample 的 after 记录已重置。")
        elif command == "2":
            timestamp = current_timestamp()
            tcp_pose = pose_reader.read_tcp_pose()
            session = writer.save_after(frame, tcp_pose=tcp_pose, timestamp=timestamp)
            print(f"[{session.sample_id}] 已保存 after_{len(session.after_captures):02d}.png 和实时 TCP。")
        elif command == "n":
            try:
                annotation_path = writer.finalize_current()
                print(f"当前 sample 已完成: {annotation_path}")
            except RuntimeError as exc:
                print(f"无法完成当前 sample: {exc}")
        elif command == "q":
            return 0
        else:
            print("未知命令，请输入 1、2、n 或 q。")


def _close_preview_windows() -> None:
    try:
        import cv2
    except ImportError:
        return
    try:
        cv2.destroyAllWindows()
    except cv2.error:
        # 部分 headless OpenCV 构建没有 HighGUI，采集数据已写盘时不应因清理窗口失败退出。
        return


if __name__ == "__main__":
    raise SystemExit(main())
