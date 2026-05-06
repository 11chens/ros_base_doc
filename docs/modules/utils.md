# 模块：常用工具箱 (Utils)

`ros_base.utils` 中的工具数量有限，但实用性较高。当前代码仓中较值得直接复用的主要包括以下几组。

## 1. `profile_latency`

位置：

```python
from ros_base.utils.decorators import profile_latency
```

它会在函数调用时统计两类延迟：

- `cycle latency`: 两次调用之间隔了多久
- `processing latency`: 这次函数本身跑了多久

还可以在输入是 ROS 消息时，检查 `header.stamp` 到当前时刻的 capture latency。

示例：

```python
@profile_latency(
    cycle_threshold_ms=100.0,
    process_threshold_ms=50.0,
    log_interval_s=3.0,
    debug=True,
)
def step(self):
    ...
```

适合放在：

- 高频 Agent 的 `step()`
- Node 的关键 callback
- 滤波或控制模块的主更新函数

## 2. `CustomLogger`

位置：

```python
from ros_base.utils.logger import CustomLogger
```

这是一个基于 `loguru` 的轻量封装，兼容了很多 ROS 风格用法：

- `info`
- `warning`
- `warn`
- `error`
- `log_once`
- `log_throttle`
- `important`

例如：

```python
self.logger.info("Camera stream ready", once=True)
self.logger.log_throttle("Waiting for VLM...", seconds=2.0)
self.logger.important("Entering State: navigation")
```

在 `BaseManager` 中可以通过 `custom_logger=CustomLogger` 注入。

## 3. `CameraTrans`

位置：

```python
from ros_base.utils.camera_trans import CameraTrans
```

这个类偏几何计算，适合做：

- base frame -> camera frame
- camera frame -> image plane
- image + depth -> 反投影

它依赖 `CameraProfile`，适合在视觉仿真、投影校验、坐标变换验证里单独使用。

## 4. `math_utils`

常用函数和类包括：

- `CircularBuffer`
- `VectorLPFilter`
- `warp2pi`
- `quat_to_rpy`
- `rpy_to_quat`
- `trans_ros_frame_to_opt_frame`
- `trans_opt_to_ros_frame`

其中 `CircularBuffer` 已经在 `quad_deploy` 的 `BaseRLAgent` 里直接用来维护观测历史：

```python
self.obs_hist = CircularBuffer(self.len_history)
```

## 5. 调试入口辅助

很多独立脚本都在用：

```python
from ros_base.utils.args_debug import add_debug_mode
```

它的作用是帮脚本快速接入调试参数，便于独立运行单个节点或入口脚本。

## 6. 使用建议

对于初次接入 `ros_base` 的项目，通常建议优先使用：

1. `CustomLogger`
2. `profile_latency`
3. `CircularBuffer`

这三样基本能覆盖：

- 日志规范化
- 性能定位
- 高频控制历史缓存
