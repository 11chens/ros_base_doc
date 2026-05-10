# 参考应用工程：SigLoMa-VLM

`SigLoMa-VLM` 展示了 `ros_base` 在“高层任务编排”场景下的典型用法：相机、桥接、VLM、跟踪器、UI 都运行在统一主流程里，由一个 FSM 驱动。

完整公开入口请参考 [`SigLoMa-Code`](https://github.com/11chens/SigLoMa-Code)。
该仓库整理了训练、部署、硬件连接、演示视频和相关仓库地图，适合作为学习
`ros_base` 如何支撑真实机器人系统的完整案例。

- 部署流程：[`docs/deployment.md`](https://github.com/11chens/SigLoMa-Code/blob/main/docs/deployment.md)
- 硬件连接：[`docs/hardware.md`](https://github.com/11chens/SigLoMa-Code/blob/main/docs/hardware.md)
- 仓库关系：[`docs/repositories.md`](https://github.com/11chens/SigLoMa-Code/blob/main/docs/repositories.md)

## 1. 当前入口文件

当前主入口是：

```
sigloma_vlm/scripts/pick_place_run.py
```

它定义了：

```
class PickPlaceRUN(BaseManager):
    ...
```

并注册：

### Nodes

- `vlm_node`: `Robot2VLMBridge`
- `joystick`: `JoystickSDKNode`
- `camera`: `CamSubNode`

### Agents

- `vlm_qwen`: `QwenVLMAgent`
- `tracker`: `TrackerAgent`
- `user`: `UIAgent`

## 2. 这个工程里 `ros_base` 是怎么被用起来的

### Manager 负责生命周期

`PickPlaceRUN` 的职责相对集中，但处于关键位置：

- 注入 `PickPlaceFSMHandlers`
- 根据 `wait` 参数添加握手规则
- 在退出时统一关闭 UI、Node 和 Agent 资源

握手规则的核心就是：

```
self.add_handshake_rule(
    "Camera Stream",
    lambda: self.nodes["camera"].img is not None,
)
```

### Handler 负责完整任务状态机

真正的任务流在：

```
sigloma_vlm/handlers/pick_place_fsm.py
```

内部状态包括：

- `WAIT_FOR_PICK_TARGET`
- `WAIT_FOR_PLACE_TARGET`
- `ROTATE_TO_PICK`
- `AI_CONFIRM_PICK`
- `GRASP_EXECUTION`
- `ROTATE_TO_PLACE`
- `AI_CONFIRM_PLACE`
- `PLACE_EXECUTION`
- `FINISHED`

这套状态机并没有直接依赖 `manager.state`，而是由 Handler 自己维护 `current_state` / `prev_state`。

## 3. 该案例中值得关注的几个要点

### 任务逻辑和通信层分开了

- `CamSubNode` 只负责拿图
- `Robot2VLMBridge` 只负责和下位机 topic 通信
- `QwenVLMAgent` 负责检测框
- `TrackerAgent` 负责跟踪和 sigma 点
- `UIAgent` 负责交互和渲染

Handler 只做“谁在什么状态下被调用”。

### 用 timestamp 防止重复处理同一帧

在抓取与放置阶段，Handler 会先检查：

```
self._last_grasp_timestamp != self.camera.img_timestamp
```

只有在新相机帧到达时才重新执行 tracker。该模式对于低频相机配合高频主循环的场景尤为重要。

### 视觉结果通过 Bridge 发给下位机

`Robot2VLMBridge` 负责发布：

- `/control/turn`
- `/control/object_ready`
- `/geometry_msgs/sigma_points`
- `/viz/vlm_bboxes`

同时订阅：

- `/control/rl_ready`
- `/control/turn_done`
- `/control/grasp_done`

该设计使高层任务逻辑可以保持在同一个 Manager 内，而不必将低层控制细节直接混入主流程。

## 4. 与 `PoseProcessor` 的结合

这个工程里目标点不是只停留在图像坐标，而是会借助：

```
self.vlm_node.pose_processor.get_object_world_position(...)
```

把：

- 框选目标
- 深度值
- 相机外参
- 视觉里程计 odom

合成为世界坐标。

这也是 `CamSubNode + PoseProcessor + Bridge Node` 组合适合任务型工程的重要原因之一。

## 5. 可复用的组织模式

在构建新的高层任务工程时，可直接参考以下分层方式：

1. 用 `BaseManager` 做统一心跳和握手
2. 用 `CamSubNode` 提供共享图像缓存
3. 用一个 Bridge Node 和下位机通信
4. 用 `BaseHandlers` 写任务 FSM
5. 把检测、跟踪、UI 这些都拆成独立 Agent
