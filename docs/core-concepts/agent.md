# BaseAgent: 算力与算法

`BaseAgent` 是 `ros_base` 中承载算法和计算的核心组件，其职责重点在于算法逻辑、状态维护与计算流程组织。

## 1. 当前基类提供了什么

`BaseAgent` 当前实现很轻：

```
class BaseAgent(ABC):
    def __init__(self, manager=None, *args, **kwargs):
        self._manager = manager
        self._logger = CustomLogger(self.__class__.__name__)
```

基类默认提供的上下文属性有：

- `self.logger`
- `self.nodes`
- `self.agents`
- `self.timestamp`
- `self.state`
- `self.node_freq_hz`
- `self.get_clock()`

其中 `reset()` 是抽象方法，子类必须实现；`handle()` 则保留给你按需定义。

## 2. 推荐的 Agent 形态

一个好的 Agent，通常满足下面三点：

1. 输入明确
2. 输出明确
3. 内部是可以单独测试的计算逻辑

比如：

```
class TrackerAgent(BaseAgent):
    def handle_initial_bbox(self, initial_bbox, img):
        ...

    def handle_sigma(self, img, depth, timestamp):
        ...

    def reset(self):
        ...
```

这里真正重要的函数，输入都是普通 Python / NumPy 数据，而不是 ROS pub/sub 过程本身。

## 3. 两类典型 Agent

### 任务型 Agent

以 `SigLoMa-VLM` 为例：

- `QwenVLMAgent`: 云端 VLM 调用，低频、高延迟
- `TrackerAgent`: 图像跟踪和 sigma 点生成
- `UIAgent`: 任务过程中的界面与叠加显示

这种 Agent 往往：

- 不适合每一帧都跑
- 需要由 Handler 在特定状态下调度
- 需要避免拖住整个主循环

### 控制型 Agent

以 `quad_deploy` 为例：

- `StandAgent`
- `SigLoMaLocoAgent`
- `SigLoMaNavAgent`
- `SigLoMaTurnAgent`

这些 Agent 基本都继承自 `BaseRLAgent`，特点是：

- 运行频率高
- 每一帧都要尽量稳定
- 会用 `decimation` 控制真正的模型推理节奏

## 4. `BaseRLAgent` 展示了高频 Agent 的一个范式

`quad_deploy` 里的 `BaseRLAgent` 是很好的参考：

```
def handle(self):
    if self.timestamp % self.decimation == 0:
        action, p_gains, d_gains, done = self.step()
    else:
        action, p_gains, d_gains, done = None, None, None, None
    self.robot.send_action(action, p_gains, d_gains)
```

这说明在 `ros_base` 体系下，Agent 并不一定每次 `handle()` 都做完整重计算。常见策略包括：

- 每 N 帧推理一次
- 高频只做轻量后处理
- 把重计算和控制下发解耦

## 5. 关于上下文访问

Agent 虽然可以直接访问 `self.nodes` 和 `self.agents`，但推荐把这当作“接线层”能力，而不是核心设计手段。

更稳的写法是：

- 在 Handler 中取数据
- 把必要数据作为参数传给 Agent
- Agent 内部只处理当前任务

例如：

```
img = self.camera.img
bbox = self.QVLM.handle_bbox(img_np=img, curr_target="toy", multi=False)
```

而不是让 Agent 深层函数到处主动读取 `self.nodes["camera"]`。

## 6. 离线测试建议

如果你希望 Agent 更容易脱离 ROS 测试：

- 构造函数里只放模型加载和轻量配置
- 核心方法尽量接收普通数据类型
- 不把 Topic 名、QoS、消息类型硬编码进 Agent

这样即使没有 Manager，你仍然可以直接实例化它，并复用 `self._logger` 输出日志。
