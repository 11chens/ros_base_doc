# 模块：相机订阅节点 (`CamSubNode`)

`CamSubNode` 是 `ros_base` 里目前最成熟的可复用 Node 之一。它做的事很明确：

- 订阅 RGB / Depth / Infra / CameraInfo
- 自动把 ROS 图像消息转成 `numpy.ndarray`
- 把最新结果缓存成易读属性
- 按需做简单可视化和录像

## 1. 当前提供的数据

实例运行后，常用属性包括：

- `img`: 最新 RGB 图像，`numpy.ndarray`
- `img_timestamp`
- `img_shape`
- `depth`
- `depth_timestamp`
- `depth_shape`
- `rgb_info`
- `infra1` / `infra2`
- `infra1_info`
- `infra_fx`
- `infra_baseline`

这也是为什么在 Handler 或 Agent 里可以直接写：

```
img = self.camera.img
depth = self.camera.depth
timestamp = self.camera.img_timestamp
```

## 2. 支持的相机配置

`CamSubNode` 当前支持把 `config` 传成字符串或 `CameraProfile`。

内置字符串预设有：

- `realsense_d435i`
- `realsense_d435i_compressed`
- `realsense_d435i_align`
- `realsense_d435i_align_compressed`
- `realsense_d435i_infra`
- `zed_mini`

注意：虽然构造函数类型提示里写了 `dict`，但当前实现实际只接受：

- `str`
- `CameraProfile`

## 3. 依附模式下的典型用法

`SigLoMa-VLM` 的入口脚本就是直接把它注册进 `nodes_dict`：

```
nodes_dict = {
    "vlm_node": Robot2VLMBridge,
    "joystick": JoystickSDKNode,
    "camera": CamSubNode,
}
```

然后在 Manager 中用握手保证首帧到达：

```
self.add_handshake_rule(
    "Camera Stream",
    lambda: self.nodes["camera"].img is not None,
)
```

这样 `handlers.handle()` 真正开始执行时，通常已经能拿到有效图像。

## 4. 典型参数

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| config | "realsense_d435i_align" | 预设相机配置 |
| record | False | 是否后台录制视频 |
| record_fps | 20 | 录制帧率上限 |
| vis_rgb | False | 开启 RGB 窗口 |
| vis_depth | False | 开启深度伪彩窗口 |
| gamma | 2.0 | Gamma 预处理 |
| use_clahe | False | CLAHE 局部对比度增强 |

### 录制行为

如果 `record=True`，当前实现会：

- 起一个后台线程
- 把图像写入 `mp4`
- 把时间戳写入文本文件

输出目录格式为：

```
~/Data/rosbags/track_session_YYYYMMDD_HHMM/
```

## 5. 独立调试方式

源码里已经内置了命令行入口：

```
python3 ros_base/nodes/camera/cam_sub_node.py \
    --camera realsense_d435i_align \
    --vis_rgb \
    --clahe
```

如果你想同时看深度：

```
python3 ros_base/nodes/camera/cam_sub_node.py \
    --camera realsense_d435i_align \
    --vis_rgb \
    --vis_depth
```

## 6. 与 `PoseProcessor` 的配合

`CamSubNode` 本身只负责拿图和相机信息。真正把：

- `bbox + depth`
- `odom`
- `camera extrinsics`

转成世界坐标的，是 `ros_base.nodes.camera.pose_processor.PoseProcessor`。

在 `SigLoMa-VLM` 中，这部分由 `Robot2VLMBridge.pose_processor` 持有，用于：

- 获取机器人 base 在 world 下的位置
- 把选中的目标框转换到世界坐标

## 7. 适合它做什么，不适合它做什么

适合：

- 订阅并缓存最新图像
- 轻量预处理
- 临时可视化
- 开发期录制

不适合：

- 在回调里做重型模型推理
- 承担整套视觉业务逻辑
- 在同一个回调里处理复杂状态机

这些应该继续留在 Agent 和 Handler 中。
