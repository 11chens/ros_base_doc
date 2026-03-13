# BaseManager: 系统管家

`BaseManager` 是整个框架的基石，也是开发者编写机器人**启动脚本**时直接继承的类。

## 1. 为什么它是唯一的 "ROS Node"?

在 `ros_base` 架构中，为了避免多进程通信的开销，我们将所有子模块“依附”在一个主进程内。`BaseManager` 继承自 `rclpy.node.Node`，它是操作系统和 ROS2 网络中可见的物理实体。

**单线程事件循环机制**：
Manager 使用默认的 ROS2 Executor（通常是 SingleThreadedExecutor）。这意味着：
1.  **Timer Loop**: 主逻辑（FSM、Handlers）由定时器触发。
2.  **External Msg**: 订阅的消息回调会插入到主线程的空闲时间执行，更新内部状态（State）。
3.  **Thread Safety**: 由于所有逻辑都在同一个线程中顺序执行，访问 `self.nodes` 或 `self.agents` 中的共享变量通常不需要锁（Lock）。

```python
class BaseManager(Node):
    def __init__(self, node_name, ...):
        super().__init__(node_name)
        # 初始化资源容器
        self.nodes = {}
        self.agents = {}
        self.handlers = None
```

## 2. 如何使用 Manager?

开发者通常不需要修改 `BaseManager` 的源码，而是通过**继承**或**配置**来创建一个具体的任务管理器。

### 示例：创建一个「捡球任务」管理器

模仿 `homi_vlm/scripts/pick_place_run_v2.py` 的设计：

```python
from ros_base.manager.base_manager import BaseManager

# 1. 导入你的组件
from my_nodes import CameraNode, ChassisNode
from my_agents import VisionAgent, ControlAgent
from my_handlers import PickPlaceHandler

class PickPlaceManager(BaseManager):
    def __init__(self):
        # 2. 定义要注册的模块
        nodes_dict = {
            "camera": CameraNode,
            "chassis": ChassisNode
        }
        agents_dict = {
            "vision": VisionAgent,
            "control": ControlAgent
        }
        
        # 3. 初始化父类，自动完成注册
        super().__init__(
            node_name="pick_place_task",
            nodes_dict=nodes_dict,
            agents_dict=agents_dict,
            handlers_class=PickPlaceHandler,
            node_freq_hz=50  # 主循环频率 50Hz
        )
        
        # 4. 添加握手规则 (Handshake Rules)
        # 只有当 chassis 节点的 ready 属性为 True 时，才开始主循环
        self.add_handshake_rule("Chassis Ready", lambda: self.nodes["chassis"].ready)

# 5. 启动
def main():
    rclpy.init()
    manager = PickPlaceManager()
    manager.start_main_loop_timer()  # 开启心脏跳动
    rclpy.spin(manager)
```

## 3. 核心功能详解

### 3.1 资源注册 (Registry)
Manager 会自动遍历 `nodes_dict` 和 `agents_dict`：
1.  实例化类对象。
2.  将 `self` (Manager实例) 注入给子对象，使它们能反向访问系统资源。
3.  将实例保存在 `self.nodes` 和 `self.agents` 字典中。

### 3.2 握手机制 (Handshake)
这是 `ros_base` 的一大特色。在进入正式控制循环前，Manager 会阻塞等待所有硬件和依赖就绪。

*   **避免报错**: 防止因为相机还没数据，第一帧算法处理就报 `NoneType` 错误。
*   **可视化提示**: 也可以在 Logs 中清晰看到系统正在等待哪个模块。

```python
self.add_handshake_rule("描述文字", 检查函数_返回bool)
```

### 3.3 多进程挂载 (Multi-Process)
虽然 Manager 本身是单进程的，但它支持管理子进程。这对于 Python 这种受 GIL 限制的语言尤为重要。

*   **适用场景**: 相机 SDK 采集（通常是阻塞的）、繁重的图像预处理、外部 Bash 脚本。
*   **使用方法**:
    ```python
    # 在 main 函数中
    from ros_base.manager.base_manager import register_multiprocess_nodes
    
    # 这些 Node 会在独立的 Python 进程中启动
    mp_nodes = {"lidar_driver": LidarNode}
    processes = register_ultiprocess_nodes(mp_nodes_dict=mp_nodes)
    ```

## 4. 最佳实践

!!! warning "性能陷阱"
    **不要贪心！** 一个 Manager 受到 Python 单线程性能限制。
    *   如果要在 500Hz 跑运控，就不要在同一个 Manager 里跑 10Hz 的 YOLO 检测。
    *   **建议方案**: 将 YOLO 单独做成一个进程，或者使用 ros_base 的多进程机制分离。
    *   Manager 适合做 **"逻辑控制 (Logic)"** 和 **"中低频决策 (Decision)"**。
