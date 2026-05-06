# 参考应用工程：Quad-Deploy

`quad_deploy` 展示了 `ros_base` 在“高频控制层”里的用法。相比 `SigLoMa-VLM` 的任务型流程，这个仓更强调：

- 高频主循环
- RL Agent 切换
- 手柄驱动状态机
- 与上位机桥接
- 必要时的外部进程隔离

## 1. 当前入口文件

当前主入口是：

```
quad_deploy/scripts/sigloma/sigloma_run_sdk.py
```

这里定义了：

```
class SigLoMaRunSDK(BaseManager):
    ...
```

并在 `setup_environment()` 中装配：

### Nodes

- `robot`: `UnitreeGo2SDKNode`
- `vlm`: `VLM2BobotBridge`
- `gripper`: `GripperNode`
- `joystick`: `JoystickNode`

### Agents

- `stand`
- `loco`
- `nav`
- `turn`
- `auto_trigger`

## 2. 高频控制场景下，Manager 负责什么

`SigLoMaRunSDK` 很克制，只做：

- 注入 `SigLoMaHandler`
- 定义握手规则

例如：

```
if wait_robot:
    self.add_handshake_rule(
        "Robot Connection",
        lambda: hasattr(self.nodes.get("robot"), "low_state"),
    )
```

真正的主频由构造参数控制：

- 仿真：`200Hz`
- 实机：`50Hz`

## 3. Handler 负责全局控制态切换

核心逻辑在：

```
quad_deploy/handlers/sigloma_handler.py
```

这个 Handler 使用的是“直接写 `manager.state`”的风格。常见状态包括：

- `cold_start`
- `recovery`
- `human_teleop`
- `turn`
- `navigation`
- `gripper_start`
- `emergency`

状态切换由：

- joystick 按键
- VLM 消息是否到达
- 当前 Agent 是否 `done`
- 自动触发器判断

共同决定。

## 4. `BaseRLAgent` 体现了高频 Agent 的组织方式

`quad_deploy/agents/base_rl_agent.py` 很值得参考，因为它把高频 Agent 的共性收得很干净：

- 从 Node 取 `robot` / `joystick`
- 解析配置
- 维护观测历史 `CircularBuffer`
- 用 `decimation` 控制真正推理频率

关键逻辑：

```
def handle(self):
    if self.timestamp % self.decimation == 0:
        action, p_gains, d_gains, done = self.step()
    else:
        action, p_gains, d_gains, done = None, None, None, None
    self.robot.send_action(action, p_gains, d_gains)
```

该设计使得：

- Manager 可以维持稳定主循环
- Agent 不必每一拍都跑完整模型
- 控制输出仍然按统一接口下发

## 5. 手柄与安全态是怎么做的

`SigLoMaHandler.get_state_transition()` 里把很多现场常用的安全规则写得很明确：

- `L2` -> `emergency`
- `L1` -> `recovery`
- `R2` -> 强制回 `human_teleop`
- `R1` -> 从人工态进入自动控制流
- `start` -> 直接触发夹爪动作

这说明 `ros_base` 适合将“人机输入 -> 状态切换 -> 当前 Agent 选型”这条链收敛在同一个 Handler 中。

## 6. 与上位机的桥接

`VLM2BobotBridge` 负责接收来自高层的：

- `/control/turn`
- `/control/grasp`
- `/geometry_msgs/sigma_points_filtered`
- `/control/object_ready`

并回传：

- `/control/rl_ready`
- `/control/turn_done`
- `/control/grasp_done`
- `/control/euler_rpy`

这和 `SigLoMa-VLM` 里的 `Robot2VLMBridge` 刚好形成上下位配对。

## 7. 多进程隔离是怎么接进来的

`sigloma_run_sdk.py` 里在 `rclpy.init()` 之前先调用：

```
processes = register_multiprocess_nodes(mp_nodes_dict, cmds_dict)
```

当前代码里典型用途包括：

- `socat` 模拟串口
- 仿真用键盘输入节点

这些都属于“不能污染主控制循环，但又必须跟着系统生命周期走”的边缘进程。

## 8. 这个工程给 `ros_base` 用户的启发

对于高频机器人控制层，`quad_deploy` 的这套结构具有较高的参考价值：

1. Manager 只负责时钟、握手和收尾
2. Handler 负责状态切换和 Agent 选择
3. 高频 Agent 使用统一基类和 decimation
4. 协议桥接单独放在 Node
5. 边缘工具进程通过多进程接口外挂
