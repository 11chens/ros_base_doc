# BaseHandlers: 状态机与调度

`BaseHandlers` 是 `ros_base` 中最适合承载“主逻辑”的位置。它将系统从“回调分散在各处”的形式收敛成“每个周期观察一次状态并完成决策”的形式。

## 1. 基类实际提供了什么

当前 `BaseHandlers` 的初始化很直接：

```
class BaseHandlers:
    def __init__(self, manager=None, *args, **kwargs):
        self.manager = manager
        self.nodes = manager.nodes if manager else {}
        self.agents = manager.agents if manager else {}
```

同时还提供几个常用属性：

- `self.logger`
- `self.timestamp`
- `self.node_freq_hz`
- `self.state`

其中 `self.state` 是对 `manager.state` 的包装，支持直接写回：

```
self.state = "navigation"
```

## 2. Handler 为什么重要

ROS 回调适合“接收消息”，但不适合“组织完整任务”。当系统同时包含视觉、控制、人工干预和状态切换时，若逻辑分散在回调中，整体执行顺序很容易失去一致性。

Handler 的作用就是：

- 在一个固定节拍里观察系统
- 按当前状态决定要调用谁
- 保证一帧逻辑有清晰的执行顺序

## 3. 当前代码仓里的两种写法

### 写法 A: Handler 内部自己维护 FSM

`SigLoMa-VLM` 的 `PickPlaceFSMHandlers` 使用：

```
self.current_state
self.prev_state
```

模式上是：

1. 先判断有没有状态切换
2. 处理 on-enter 动作
3. 再执行当前状态下的循环逻辑

这非常适合任务流程型状态机，例如：

- 等待用户圈选目标
- 旋转到目标
- VLM 二次确认
- 跟踪并抓取

### 写法 B: 直接驱动 `manager.state`

`quad_deploy` 的 `SigLoMaHandler` 使用：

```
new_state = self.get_state_transition()
if new_state:
    self.state = new_state
    self.on_state_enter(new_state)
```

这种风格更适合全局控制态，例如：

- `cold_start`
- `human_teleop`
- `turn`
- `navigation`
- `emergency`

## 4. 推荐的状态机结构

无论采用哪种写法，均建议使用如下结构：

```
def handle(self):
    if state_changed:
        self.on_state_enter(...)

    if current_state == ...:
        ...
    elif current_state == ...:
        ...
```

### 为什么要分开

因为很多动作只能在“切换瞬间”做一次，比如：

- 重置 done 标志
- 清空界面标记
- 复位 Agent
- 发布一次性触发命令

而另一些动作必须“每个周期都执行”，比如：

- 读取最新图像
- 调一次跟踪器
- 发送当前控制量

## 5. 真实案例里的两个好习惯

### 习惯 A: 进入新状态时统一清理边缘状态

`PickPlaceFSMHandlers` 在状态切换时会：

- `reset_action_states()`
- 清空 UI sigma points
- 清空 mask

这能显著减少“上一个状态残留结果污染下一个状态”的问题。

### 习惯 B: 高频流程只在新数据到达时做重计算

`PickPlaceFSMHandlers` 在抓取/放置阶段会比对 `camera.img_timestamp`，只在新帧到达时才更新 tracker：

```
if self._last_grasp_timestamp != self.camera.img_timestamp:
    ...
```

这是一种非常实用的节流方式，避免同一帧图像被重复重算很多次。

## 6. Handler 最适合放什么

适合：

- 状态机
- 跨模块调度
- 资源启停顺序
- 决策分支

不适合：

- 大模型推理细节
- 图像算法内部实现
- ROS 订阅/发布底层细节

这些应该分别留在 Agent 和 Node 中。
