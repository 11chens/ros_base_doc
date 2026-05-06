# BaseManager: 系统管家

`BaseManager` 是整个框架的主入口。当前实现里，它负责四件事：

1. 注册 `Node / Agent / Handler`
2. 持有统一的 ROS2 Node 上下文
3. 执行握手和主循环
4. 在退出时统一释放资源和清理子进程

## 1. 当前源码里的构造参数

`BaseManager` 目前最常用的参数有：

```
BaseManager(
    node_name="BaseManager",
    nodes_dict={},
    agents_dict={},
    handlers_class=None,
    node_freq_hz=200,
    start_state=None,
    custom_logger=None,
    log_freq=False,
)
```

它会在 `__init__()` 里立即完成注册：

```
self._register_nodes(nodes_dict, *args, **kwargs)
self._register_agents(agents_dict, *args, **kwargs)
self._register_handlers(handlers_class, *args, **kwargs)
```

这意味着传给 Manager 的很多业务参数，也会继续透传给 Node、Agent 和 Handler。

## 2. 一个真实用法

`SigLoMa-VLM` 中的入口脚本就是标准写法：

```
class PickPlaceRUN(BaseManager):
    def __init__(self, wait=["img"], *args, **kwargs):
        kwargs["handlers_class"] = PickPlaceFSMHandlers
        super().__init__(*args, **kwargs)

        if "img" in wait:
            self.add_handshake_rule(
                "Camera Stream",
                lambda: self.nodes["camera"].img is not None,
            )
```

启动时：

```
rclpy.init()
manager = PickPlaceRUN(
    node_name="PickPlaceOrchestrator",
    nodes_dict=nodes_dict,
    agents_dict=agents_dict,
    node_freq_hz=10,
    start_state="PREPARE",
)
manager.start_main_loop_timer()
```

这里 `start_main_loop_timer()` 会自己完成：

- 握手循环
- `create_timer`
- `rclpy.spin`
- 收尾和 `shutdown`

## 3. 握手机制

握手规则通过 `add_handshake_rule()` 注册：

```
self.add_handshake_rule("Robot Connection", lambda: hasattr(self.nodes["robot"], "low_state"))
```

`start_main_loop_timer()` 会在进入主循环前反复调用 `handshake()`：

- 没有规则时直接通过
- 有规则时必须全部满足
- 未满足时通过 `rclpy.spin_once(self, timeout_sec=0.1)` 等待新消息推进状态

这对相机首帧、硬件总线、上位机桥接特别有用。

## 4. 主循环里到底发生什么

`BaseManager.main_loop()` 当前实现顺序很简单：

1. 若定义了 `get_state_switch()`，先尝试切换 `self.state`
2. 若定义了 `state_handle()`，执行该逻辑
3. 如果注册了 `handlers`，执行 `handlers.handle()`
4. `self.timestamp += 1`
5. 按需打印频率

所以推荐的实践是：

- 业务逻辑优先放在 `BaseHandlers.handle()`
- `manager.state` 只保存顶层状态
- 高频循环里避免阻塞操作

## 5. `release_resources()` 作为业务侧释放钩子

`BaseManager.release_resources()` 在基类里是空实现，专门留给业务仓重载。

比如 `PickPlaceRUN.release_resources()` 会：

- 关闭 UI Agent
- 遍历 Node 调用 `release_resources()`
- 遍历 Agent 调用 `close()`

因此，**所有需要显式回收的线程、文件句柄、窗口、硬件连接，都建议在这里统一收口。**

## 6. 多进程挂载能力

当前代码仓直接提供了两个帮助函数：

```
from ros_base.manager.base_manager import (
    register_multiprocess_nodes,
    shutdown_multiprocess_nodes,
)
```

### `register_multiprocess_nodes()`

支持两类子进程：

- `mp_nodes_dict`: 把某个 `BaseNode` 子类拉到独立 Python 进程里
- `cmds_dict`: 启动外部命令，比如 `socat`、自定义 bash 脚本

示例来自 `quad_deploy`：

```
cmds_dict["sim_port"] = (
    "socat -d -d pty,raw,echo=0,link=/tmp/pty10 "
    "pty,raw,echo=0,link=/tmp/pty11 &"
)
processes = register_multiprocess_nodes(mp_nodes_dict, cmds_dict)
```

然后把 `processes` 传回 Manager：

```
manager.start_main_loop_timer(processes)
```

Manager 退出时会自动调用 `shutdown_multiprocess_nodes(processes)`。

## 7. 使用建议

适合放在同一个 Manager 里的内容：

- 轻量订阅缓存
- 高频共享状态
- 需要顺序执行的状态机

建议拆出去的内容：

- 阻塞式外部命令
- 相机 SDK 或第三方工具进程
- 明显拖慢主频的长耗时计算

一个 Manager 不要什么都塞

`ros_base` 的价值在于“组合”，不是把所有逻辑重新写回一个大类。高频控制和重视觉推理如果长期共处一个 Manager，最终还是会互相拖慢。
