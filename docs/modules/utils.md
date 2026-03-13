# 模块：常用工具箱 (Utils)

`ros_base` 提供了一系列开箱即用的工具类，用于提高开发效率，降低模板代码量。其中最常用的是性能分析与日志工具。

## 1. 性能分析装饰器 (`profile_latency`)

在机器人系统中，**处理延迟 (Processing Latency)** 与 **循环周期延迟 (Cycle Latency)** 是决定系统表现的生命线。尤其是执行高频控制 (RL Agent) 或高负载感知算子 (Kalman Filter) 时，我们需要精确知道每一步代码花了多少时间，以及 ROS 2 的回调是否按期望频率触发。

`ros_base.utils.decorators.profile_latency` 是为你量身定制的无感分析探针。

### 1.1 核心功能
*   **循环周期分析 (Cycle Latency)**: 自动计算并监控两次函数调用之间的耗时 (间隔)，以此判断实际运行频率。
*   **执行耗时分析 (Processing Latency)**: 监控当前函数逻辑本身执行所需的绝对时间。
*   **通信延迟检查 (Capture Latency)**: 如果函数入参接收了 ROS Standard 消息头 (`header.stamp`)，可自动计算物理产生到软件调用的网络/缓冲区迟滞。
*   **周期性汇报**: 聚合多次调用的结果并自动计算 Avg (平均) / Max (最大) 统计值，保持控制台整洁。

### 1.2 实际应用场景示例

**场景 A: 监控 Node 的 ROS 回调延迟**
这通常用于视觉节点中（如 `KFSigmaNode`），检查图像传输与反序列化是否过载。

```python
from ros_base.utils.decorators import profile_latency
from geometry_msgs.msg import PolygonStamped

class KFSigmaNode(BaseNode):
    # 期望收到 10Hz 数据 (Cycle 100ms)。设定阈值 250ms (超时警告)
    # 处理应该很快完成。设定处理阈值 100ms
    # 大约每 10 秒钟在 log 打印一次统计摘要
    @profile_latency(
        cycle_threshold_ms=250.0,
        process_threshold_ms=100.0,
        log_interval_s=10.0,
        debug=True,
        check_capture_latency=False, # 可以设为 True 来对比 msg.header.stamp 与现时的差值
    )
    def _perception_callback(self, msg: PolygonStamped):
        capture_time = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        # ... 后延感知处理逻辑 ...
```

如果在 10s 内该方法运行了，控制台会自动打印如下统计：
`[INFO]: [_perception_callback] Stats (10.0s): Cycle Avg/Max 101.20/150.32 ms, Process Avg/Max 21.05/45.10 ms`

**场景 B: 严格监控 Agent 算法主频**
控制算法类 (`Locomotion` / `Navigation`) 通常对延时要求极为苛刻。这里我们期望它是 50Hz (20ms/Step)。

```python
class HomiNavAgent(BaseRLAgent):
    @profile_latency(
        cycle_threshold_ms=100.0,   # 控制器容忍断流的最差底线
        process_threshold_ms=50.0,  # 算法前向传播推理底线
        log_interval_s=3.0,         # 高频任务我们加快汇报频率
        debug=True
    )
    def step(self):
        # 1. 获取观察
        self.get_observation()
        # 2. 推理动作
        action = self.infer()
        # 3. 后处理与映射
        return action, None, None, self.done
```

### 1.3 参数说明

| 参数名称 | 类型 | 默认值 | 描述 |
| :--- | :--- | :--- | :--- |
| `cycle_threshold_ms` | `float` | `50.0` | **循环超时阈值**。两次调用间隔（毫秒）若超过此数值并在 `debug=True` 情况下会触发 `logger.warning`。 |
| `process_threshold_ms` | `float` | `20.0` | **执行超时阈值**。函数本身执行耗时（毫秒）超过此值触发警告。 |
| `log_interval_s` | `float` | `5.0` | 统计数据的输出间隔时间（秒）。这段时间内不会刷屏打印，时间到了输出汇总：Avg 与 Max。置为 0 表示关闭汇总。 |
| `debug` | `bool` | `True` | 开启在超越 `threshold` 阈值时的即时单条打印（非常适合抓偶尔的卡顿尖刺）。 |
| `check_capture_latency`| `bool` | `False` | 通信防失真校准：若设为 `True`，且函数第一个参数是带有 `msg.header.stamp` 的消息体，会利用该源时间戳算出网络层的迟滞并即时打印。 |

---
*其它工具方法 (`Logger`, `MathUtils` 等) 的文档正在补充中...*
