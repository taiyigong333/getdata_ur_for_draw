一个数据应该有什么

①没有夹取前的固定视角图片
②夹取成功后的固定视角图片
③夹取成功时候的tcp值
④夹取language指令

如何构建
1. 自己采集，并在采集手动完成下面的标注
2. 初始时候的固定相机视角具有①
3. 夹取成功的图片具有②
4. 成功图片对应的tcp就是③

具体的数据结构长什么样
grasp_success_dataset/
├── README.md
├── dataset_metadata.json    # 全局公共元数据（精简版）
└── samples/
    ├── sample_00001/
    │   ├── images/
    │   │   ├── before.png       # 夹取前固定视角图
    │   │   ├── after_01.png     # 夹取成功后图1
    │   │   ├── after_02.png     # 夹取成功后图2（可选）
    │   │   └── after_03.png     # 夹取成功后图3（可选）
    │   └── annotation.json      # 单样本标注，含指定extra_meta字段
    ├── sample_00002/
    │   ├── images/
    │   │   ├── before.png
    │   │   └── after_01.png
    │   └── annotation.json
    └── ...

全局数据：
{
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
单个sample的json：
{
  "sample_id": "sample_00001",
  "source_trajectory_id": "traj_00052",
  "language_instruction": "夹取桌面上的方形白色塑料工件",
  "image_paths": {
    "before": "images/before.png",
    "after_list": [
      "images/after_01.png",
      "images/after_02.png",
      "images/after_03.png"
    ]
  },
  "grasp_success_tcp_pose": {
    "position": {
      "x": 0.352,
      "y": -0.124,
      "z": 0.215
    },
    "orientation": {
      "rx": 0.0,
      "ry": 90.0,
      "rz": 0.0
    }
  },
  "extra_meta": {
    "object_type": "方形塑料工件",
    "capture_timestamp": "2026-06-19 10:23:45",
    "arm_model": "UR7e",
    "tcp_set": [0.0, 0.0, 0.15]
  }
}

相关流程，使用rtde读取机器臂的末端位姿，按1是拍摄初始位置（多次按会重置），按2是拍摄成功位置
同时提供当前sample完毕，切换到下一个sample的拍摄的功能，同时提供摄像头的预览
grasp_success_tcp_pose和图片以及时间戳需要实时的，剩下的内容从config中读取（可能有多个config）
不用涉及对于机器臂的控制，使用rtde和realsense摄像机读取相关需要的内容即可