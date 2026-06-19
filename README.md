# 固定视角夹取成功数据采集工具

本项目用于采集机械臂夹取成功数据。每个 sample 包含夹取前固定视角图片、夹取成功后的固定视角图片、成功时刻 TCP 位姿、自然语言指令和补充元数据。

## 项目结构

```text
.
├── configs/
│   ├── default.json          # 实机采集配置模板
│   └── mock.json             # 无硬件验证配置
├── docs/
│   └── HANDOFF.md            # 项目交接与后续注意事项
├── src/
│   └── grasp_dataset_collector/
│       ├── camera.py         # RealSense / mock 摄像头
│       ├── cli.py            # 采集入口
│       ├── config.py         # 配置读取
│       ├── dataset.py        # 数据集写入
│       └── pose.py           # RTDE / mock TCP 读取
├── need.md
├── requirements.txt
└── README.md
```

## 安装

建议使用 Python 3.10+。

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

实机采集需要安装并连接：

- Intel RealSense 摄像头及驱动。
- 可通过 RTDE 读取的 UR 机械臂控制器网络。

## 配置

复制或修改 `configs/default.json`：

- `dataset_root`：数据集输出目录。
- `camera`：RealSense 分辨率、帧率和预览窗口名称。
- `robot.rtde_host`：机械臂控制器 IP。
- `sample_defaults`：除实时图像、TCP、时间戳之外的静态标注字段。

如果一次实验有不同任务、物体或语言指令，建议为每批实验单独保存一个 config。

完整字段说明见 [docs/CONFIG.md](docs/CONFIG.md)。

## 运行

实机采集：

```bash
python -m grasp_dataset_collector --config configs/default.json
```

无硬件验证流程：

```bash
python -m grasp_dataset_collector --config configs/mock.json
```

不显示预览、用命令行输入控制：

```bash
python -m grasp_dataset_collector --config configs/mock.json --no-preview
```

## 采集按键

- `1`：采集或重置当前 sample 的 `before.png`。多次按会覆盖初始图，并清空当前 sample 已采集的 after。
- `2`：采集夹取成功图 `after_XX.png`，同时读取实时 TCP 和时间戳。
- `n`：完成当前 sample，写入 `annotation.json`，并切换到下一个 sample。
- `q` 或 `Esc`：退出程序。

## 输出数据结构

```text
grasp_success_dataset/
├── dataset_metadata.json
└── samples/
    └── sample_00001/
        ├── images/
        │   ├── before.png
        │   └── after_01.png
        └── annotation.json
```

`annotation.json` 示例字段：

```json
{
  "sample_id": "sample_00001",
  "language_instruction": "夹取桌面上的方形白色塑料工件",
  "image_paths": {
    "before": "images/before.png",
    "after_list": ["images/after_01.png"]
  },
  "grasp_success_tcp_pose": {
    "position": {"x": 0.352, "y": -0.124, "z": 0.215},
    "orientation": {"rx": 0.0, "ry": 90.0, "rz": 0.0}
  },
  "extra_meta": {
    "object_type": "方形塑料工件",
    "capture_timestamp": "2026-06-19 10:23:45",
    "arm_model": "UR7e",
    "tcp_set": [0.0, 0.0, 0.15]
  }
}
```

## Git 管理建议

代码、配置模板和文档纳入 Git；采集得到的 `grasp_success_dataset/` 默认不提交。若需要版本化数据，建议单独使用 DVC、Git LFS 或独立数据盘快照管理。
