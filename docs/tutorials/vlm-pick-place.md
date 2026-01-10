# 实战：VLM 驱动的机械臂抓取

本教程将带领您使用 `ros_base` 构建一个基于视觉语言大模型 (VLM) 的物体抓取应用。我们将复现 `HomiQuad-VLM` 项目中的核心逻辑。

## 1. 任务目标

*   用户输入自然语言指令（例如：“把那个红色的苹果拿给我”）。
*   机器人使用 VLM (如 Qwen-VL) 理解图像，输出目标物体的 Bounding Box。
*   使用 Handler 状态机控制机械臂逼近并抓取目标。

## 2. 目录结构设计

建议的工程结构如下：

```text
my_pick_project/
    scripts/
        run_task.py       # 启动脚本 (Manager)
    nodes/
        arm_node.py       # 机械臂驱动
        camera_node.py    # 相机驱动
    agents/
        vlm_agent.py      # 大模型推理
        tracker_agent.py  # 视觉跟踪 (YOLO/Sam)
    handlers/
        pick_fsm.py       # 状态机逻辑
```

## 3. 核心组件实现

### 3.1 定义状态机 (Handler)

首先思考机器人需要哪些状态。

```python
# handlers/pick_fsm.py (简化版)
from enum import Enum, auto
from ros_base.handlers.base_handlers import BaseHandlers

class State(Enum):
    IDLE = auto()        # 等待指令
    THINKING = auto()    # VLM 思考中
    TRACKING = auto()    # 视觉伺服对准
    GRASPING = auto()    # 执行抓取动作

class PickHandler(BaseHandlers):
    def handle(self):
        # 获取最新的传感器数据
        img = self.nodes['camera'].img
        
        # --- 状态跳转逻辑 ---
        if self.current_state == State.IDLE:
            if self.nodes['voice'].has_new_command():
                self.current_state = State.THINKING
                
        elif self.current_state == State.THINKING:
            # 调用 VLM Agent
            result = self.agents['vlm'].inference(img, prompt="Find the red apple")
            if result:
                self.target_bbox = result
                self.current_state = State.TRACKING
                
        elif self.current_state == State.TRACKING:
            # 调用伺服控制 Agent
            cmd_vel = self.agents['pid'].compute(self.target_bbox)
            self.nodes['arm'].publish_vel(cmd_vel)
            
            if self.is_aligned():
                self.current_state = State.GRASPING
```

### 3.2 封装 VLM Agent

将大模型调用封装在 Agent 中，确保主线程不被阻塞（可以使用异步或多线程，此处演示基本逻辑）。

```python
# agents/vlm_agent.py
from ros_base.agents.base_agent import BaseAgent

class VLMAgent(BaseAgent):
    def inference(self, image, prompt):
        # 模拟调用 HTTP API 或本地 TensorRT 推理
        # 注意：如果是耗时操作，建议不要直接在 handle 中同步等待
        print(f"Seeing image, looking for: {prompt}")
        return [100, 100, 50, 50] # 返回 bbox [x,y,w,h]
```

### 3.3 组装 Manager

在 `scripts/run_task.py` 中将它们组装起来。

```python
from ros_base.manager.base_manager import BaseManager
from handlers.pick_fsm import PickHandler, State

class PickManager(BaseManager):
    def __init__(self):
        super().__init__(
            node_name="vlm_pick_task",
            nodes_dict={...},
            agents_dict={...},
            handlers_class=PickHandler
        )
        
        # 添加可视化调试
        self.add_handshake_rule("Camera", lambda: self.nodes['camera'].ok())

if __name__ == "__main__":
    import rclpy
    rclpy.init()
    mgr = PickManager()
    rclpy.spin(mgr)
```

## 4. 运行效果

启动后，您将在终端看到 ros_base 的标准日志格式：

```text
[INFO] [Manager]: Handshake passed. Rules satisfy: ['Camera', 'Arm']
[INFO] [Manager]: Main loop started at 50Hz.
[INFO] [Handler]: State Update: State.IDLE -> State.THINKING
[INFO] [Agent]: VLM Inference time: 0.15s
[INFO] [Handler]: State Update: State.THINKING -> State.TRACKING
```

通过这种方式，复杂的 AI 逻辑被清晰地拆解到了不同的模块中，易于维护和调试。
