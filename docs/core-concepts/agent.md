# BaseAgent: 算力与算法

`BaseAgent` 是系统的“大脑皮层”。如果说 Node 是手脚（负责收发），Manager 是心脏（提供动力），那么 Agent 就是负责思考的单元。

## 1. 设计原则：纯粹性

一个优秀的 Agent 设计应当遵循 **"IPO 原则"**:

*   **I (Input)**: 输入数据（通常来自 Node 的缓存）。
*   **P (Process)**: 核心算法处理（神经网络、运动学解算、路径规划）。
*   **O (Output)**: 输出结果（通常是控制指令或状态）。

!!! danger "严禁操作 ROS"
    **Agent 不应该包含任何 `create_publisher` 或 `create_subscription` 代码！**
    
    *   **为什么?** 为了保证算法的可移植性和可测试性。
    *   如果 Agent 不依赖 ROS，你就可以直接实例化它，输入一张本地图片，测试它的输出，而不需要启动整个 ROS 环境。

## 2. 编写一个 BaseAgent

### 基础示例

```python
from ros_base.agents.base_agent import BaseAgent

class TrackingAgent(BaseAgent):
    def __init__(self, model_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 加载模型 (耗时操作放在 init)
        self.model = load_yolo(model_path)

    def handle(self, image_np):
        """
        核心处理函数
        Args:
            image_np: numpy array 格式的图片
        Returns:
            bbox: [x, y, w, h]
        """
        if image_np is None:
            return None
            
        # 纯计算逻辑
        result = self.model.detect(image_np)
        return result

    def reset(self):
        # 清除内部状态 (如果有)
        self.model.reset_tracker()
```

## 3. Agent 的分类

在 `ros_base` 实战中，Agent 通常分为两类：

### 3.1 执行型 (Control Agent)
*   **特点**: 高频 (100Hz+)，低延迟，输入输出简单。
*   **示例**: `quad_deploy` 中的 `LocoAgent`。
*   **实现**: 通常做简单的 PID 计算或轻量级神经网络 (ONNX) 推理。

### 3.2 任务型 (Task Agent)
*   **特点**: 低频 (1-30Hz)，计算耗时，可能涉及大模型调用。
*   **示例**: `homi_vlm` 中的 `QwenVLMAgent` (调用云端 API) 或 `TrackerAgent` (运行分割模型)。
*   **策略**:
    *   **分时复用**: 不要让它阻塞主循环。通常由 Handler 控制，在特定状态下才调用。
    *   **异步处理**: 如果耗时实在太长（>100ms），建议配合多线程或将其剥离为独立进程。

## 4. 上下文访问

虽然 Agent 提倡“纯函数”式设计，但有时也需要访问系统状态。
`BaseAgent` 中自动注入了 `self.manager`：

```python
def my_method(self):
    # 可以访问同一 Manager 下的其他 Agent
    tracker = self.agents['tracker']
    
    # 获取系统时间
    t = self.get_clock().now()
```
但请谨慎使用，过多的交叉引用会降低模块的独立性。建议优先通过函数参数传递所需数据。
