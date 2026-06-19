# 项目交接文档

## 当前目标

根据 `need.md` 搭建固定视角机械臂夹取成功数据采集工具。工具负责：

- 使用 RealSense 读取固定视角图像并提供预览。
- 使用 RTDE 读取机械臂当前 TCP 位姿。
- 按键采集夹取前 `before.png`、夹取成功后 `after_XX.png`。
- 将实时图片、TCP、时间戳和 config 中的静态标注写成指定数据集结构。

## 已实现结构

```text
configs/
  default.json        # 实机采集配置模板
  mock.json           # 无硬件验证配置
src/grasp_dataset_collector/
  camera.py           # RealSense/Mock 摄像头
  pose.py             # RTDE/Mock TCP 读取与姿态转换
  dataset.py          # 数据集目录、图片、annotation 写入
  cli.py              # 命令行采集流程
docs/
  HANDOFF.md          # 当前交接文档
```

## 关键约定

- 数据输出根目录默认是 `grasp_success_dataset/`，已加入 `.gitignore`，避免把大体积采集数据提交到代码仓库。
- `grasp_success_tcp_pose` 使用当前 sample 最后一次按 `2` 时读到的 TCP。
- 多次按 `1` 会覆盖当前 sample 的 `before.png` 并清空已拍摄的 `after`，避免起点变化后混入旧成功图。
- RTDE 的 UR TCP 姿态默认按旋转向量弧度读取，并转换为固定轴 XYZ 欧拉角角度。

## 待现场确认

- `configs/default.json` 中的 `robot.rtde_host` 是否为真实机械臂 IP。
- `sample_defaults.language_instruction`、`object_type` 是否按每批采集任务创建独立 config。
- 现场 RealSense 分辨率和帧率是否稳定支持 `1280x720@30`。
