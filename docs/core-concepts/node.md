# BaseNode: 双模态节点

`BaseNode` 是 `ros_base` 中所有通信模块的统一基类。它最重要的特点不是“继承 ROS Node”，而是**把同一份业务代码同时兼容两种运行方式**：

- 依附模式：挂在 `BaseManager` 上
- 独立模式：自己作为单独 ROS2 Node 运行

## 1. 当前实现的真实结构

`BaseNode.__init__()` 的核心逻辑是：

```
def __init__(self, manager=None, *args, **kwargs):
    self._manager = manager if manager is not None else Node(*args, **kwargs)
```

具体而言：

- 有 `manager` 时，`self._manager` 就是那个 `BaseManager`
- 没有 `manager` 时，`self._manager` 才是临时创建的 `rclpy.node.Node`

后续的这些接口都会被转发给 `self._manager`：

- `create_publisher`
- `create_subscription`
- `create_timer`
- `destroy_publisher`
- `destroy_subscription`
- `get_clock`

## 2. 依附模式

这是最常见的生产用法。Node 只负责：

- 订阅 ROS 消息
- 把结果缓存到自身属性
- 提供发布方法

例如：

```
class SensorNode(BaseNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.latest_msg = None
        self.sub = self.create_subscription(
            Image, "/camera/color/image_raw", self.callback, 10
        )

    def callback(self, msg):
        self.latest_msg = msg
```

在 Handler 或 Agent 里就可以直接读取：

```
img = self.nodes["camera"].img
```

不需要再为“系统内部模块之间传图像”多开一个 Topic。

## 3. 独立模式

当前实现支持直接调用：

```
node.start_spin_standalone()
```

但有一个容易忽略的点：**独立模式前仍然要先 `rclpy.init()`。**

标准模板：

```
import rclpy

rclpy.init()
node = MyNode(node_name="my_node")
try:
    node.start_spin_standalone()
finally:
    node.release_resources()
    if rclpy.ok():
        node.destroy_node()
        rclpy.shutdown()
```

`CamSubNode` 和 `Robot2VLMBridge` 在源码里都提供了这种独立运行入口。

## 4. `BaseNode` 默认暴露的上下文

当它依附在 Manager 上时，可以直接通过属性访问：

- `self.nodes`
- `self.agents`
- `self.logger`
- `self.timestamp`
- `self.node_freq_hz`

该机制允许 Node 读取系统状态，但仍建议保持边界清晰：

- Node 适合做缓存和桥接
- 不建议在 Node 里写复杂业务调度
- 不建议让 Node 主动回调 Agent/Handler，避免反向耦合

## 5. 资源释放

`BaseNode.release_resources()` 在基类中是空实现，留给具体子类覆盖。

典型场景：

- 关闭视频写入器
- 停止后台线程
- 关闭窗口
- 释放串口或硬件句柄

例如 `CamSubNode.release_resources()` 就会停止录制线程并关闭视频文件。

## 6. 典型 Bridge 角色

在两个示例工程里，Node 都承担了“协议边界层”的角色：

- `SigLoMa-VLM/sigloma_vlm/nodes/robot2vlm.py`
 负责把高层感知结果发布给下位机，并订阅 `rl_ready` / `turn_done` / `grasp_done`
- `quad_deploy/quad_deploy/nodes/sigloma/vlm2robot.py`
 负责接收上位机控制信号，并回传 `rl_ready` / `turn_done` / `grasp_done`

这类 Node 的理想形态就是：

- 外部协议复杂
- 内部接口简单
- 业务逻辑仍留在 Handler/Agent 中
