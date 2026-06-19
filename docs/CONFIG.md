# Config 编写说明

采集程序通过 JSON config 控制数据输出位置、摄像头、RTDE 读取方式和样本静态标注。实时字段不应写在 config 中，包括图片、TCP 位姿和采集时间戳；这些字段会在按键采集时自动生成。

## 最小结构

一个 config 必须包含 5 个顶层字段：

```json
{
  "dataset_root": "grasp_success_dataset",
  "dataset_metadata": {},
  "camera": {},
  "robot": {},
  "sample_defaults": {}
}
```

字段用途：

- `dataset_root`：数据集输出根目录。
- `dataset_metadata`：写入 `dataset_metadata.json` 的全局数据集说明。
- `camera`：摄像头来源、分辨率、帧率和预览窗口设置。
- `robot`：TCP 读取来源和 RTDE 连接设置。
- `sample_defaults`：每个 sample 共用的静态标注字段。

## dataset_root

```json
"dataset_root": "grasp_success_dataset"
```

建议每次正式实验使用独立输出目录，例如：

```json
"dataset_root": "data/2026_06_19_white_blocks"
```

注意：默认 `.gitignore` 会忽略 `grasp_success_dataset/`，如果换成 `data/...`，需要按实际数据管理策略决定是否加入 `.gitignore`。

## dataset_metadata

```json
"dataset_metadata": {
  "dataset_name": "fixed_view_grasp_success_dataset",
  "description": "固定视角下机械臂夹取成功数据集，包含夹取前后图像、成功时刻TCP位姿与自然语言指令",
  "coordinate_system": {
    "base_frame": "机械臂基坐标系",
    "tcp_frame": "工具中心点坐标系",
    "position_unit": "m",
    "orientation_unit": "degree",
    "orientation_type": "欧拉角(Rx-Ry-Rz, 固定轴XYZ)"
  }
}
```

推荐保持坐标系说明稳定，除非现场实际记录格式改变。程序只会在 `dataset_root/dataset_metadata.json` 不存在时写入该字段；如果要修改已经存在的数据集元数据，需要手动编辑或删除旧文件后重新生成。

## camera

### RealSense 实机配置

```json
"camera": {
  "type": "realsense",
  "width": 1280,
  "height": 720,
  "fps": 30,
  "preview_window": "grasp dataset collector"
}
```

字段说明：

- `type`：实机采集使用 `realsense`。
- `width` / `height`：彩色图分辨率。
- `fps`：彩色流帧率。
- `preview_window`：OpenCV 预览窗口名称。

如果现场启动失败，优先降低到 `640x480@30` 验证相机链路。

### Mock 配置

```json
"camera": {
  "type": "mock",
  "width": 960,
  "height": 540,
  "fps": 30,
  "preview_window": "grasp dataset collector mock"
}
```

`mock` 用于无 RealSense 环境下验证采集流程、目录结构和 JSON 输出，不代表真实图像质量。

## robot

### RTDE 实机配置

```json
"robot": {
  "type": "rtde",
  "rtde_host": "192.168.1.10",
  "rtde_port": 30004,
  "orientation_input": "rotation_vector_rad"
}
```

字段说明：

- `type`：实机读取 TCP 使用 `rtde`。
- `rtde_host`：机械臂控制器 IP，必须按现场网络修改。
- `rtde_port`：RTDE 端口，默认 `30004`。
- `orientation_input`：RTDE 返回姿态的解释方式。

当前支持的 `orientation_input`：

- `rotation_vector_rad`：UR 常见 TCP 姿态格式，旋转向量，单位弧度。程序会转换为固定轴 XYZ 欧拉角，单位度。
- `euler_degree`：如果上游已经返回欧拉角角度，可直接写入。

本项目只读取 RTDE TCP，不下发机械臂控制指令。

### Mock 配置

```json
"robot": {
  "type": "mock"
}
```

`mock` 会生成稳定的模拟 TCP，用于流程测试。

## sample_defaults

```json
"sample_defaults": {
  "language_instruction": "夹取桌面上的方形白色塑料工件",
  "object_type": "方形塑料工件",
  "arm_model": "UR7e",
  "tcp_set": [0.0, 0.0, 0.15]
}
```

字段会写入每个 sample 的 `annotation.json`：

- `language_instruction`：本批样本的自然语言夹取指令。
- `object_type`：目标物体类型或名称。
- `arm_model`：机械臂型号。
- `tcp_set`：工具 TCP 设置，按现场机械臂配置填写。

不应写入 config 的字段：

- `sample_id`：程序自动按 `sample_00001` 递增生成。
- `image_paths`：程序按采集结果自动生成。
- `grasp_success_tcp_pose`：按 `2` 时实时读取。
- `capture_timestamp`：按 `2` 时实时记录。
- `source_trajectory_id`：当前数据格式不使用该字段。

## 推荐配置管理方式

不同任务、物体、语言指令或输出目录建议使用不同 config，例如：

```text
configs/
├── default.json
├── mock.json
├── white_block_ur7e.json
└── metal_cylinder_ur7e.json
```

正式采集前建议先运行 mock：

```bash
python -m grasp_dataset_collector --config configs/mock.json --no-preview
```

再运行实机配置：

```bash
python -m grasp_dataset_collector --config configs/white_block_ur7e.json
```

## 完整实机示例

```json
{
  "dataset_root": "grasp_success_dataset",
  "dataset_metadata": {
    "dataset_name": "fixed_view_grasp_success_dataset",
    "description": "固定视角下机械臂夹取成功数据集，包含夹取前后图像、成功时刻TCP位姿与自然语言指令",
    "coordinate_system": {
      "base_frame": "机械臂基坐标系",
      "tcp_frame": "工具中心点坐标系",
      "position_unit": "m",
      "orientation_unit": "degree",
      "orientation_type": "欧拉角(Rx-Ry-Rz, 固定轴XYZ)"
    }
  },
  "camera": {
    "type": "realsense",
    "width": 1280,
    "height": 720,
    "fps": 30,
    "preview_window": "grasp dataset collector"
  },
  "robot": {
    "type": "rtde",
    "rtde_host": "192.168.1.10",
    "rtde_port": 30004,
    "orientation_input": "rotation_vector_rad"
  },
  "sample_defaults": {
    "language_instruction": "夹取桌面上的方形白色塑料工件",
    "object_type": "方形塑料工件",
    "arm_model": "UR7e",
    "tcp_set": [0.0, 0.0, 0.15]
  }
}
```
