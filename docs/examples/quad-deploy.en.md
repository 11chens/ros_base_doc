<!-- i18n-sync: source=docs/examples/quad-deploy.md; sha256=7115273EADA010BCECCBB159F5BFE6CCDF9B0E378BA1793A35A91EA1172161C0 -->
# Example Project: Quad-Deploy

`quad_deploy` shows how `ros_base` is used in a high-frequency control stack. Compared with the task-oriented flow in `SigLoMa-VLM`, this repository emphasizes:

- High-frequency main loops
- RL-agent switching
- Joystick-driven state machines
- Bridging with the upper-level system
- External-process isolation when necessary

## 1. Current entry file

The current main entry is:

```
quad_deploy/scripts/sigloma/sigloma_run_sdk.py
```

It defines:

```
class SigLoMaRunSDK(BaseManager):
    ...
```

and assembles the system in `setup_environment()`:

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

## 2. What the manager does in a high-frequency control setup

`SigLoMaRunSDK` stays disciplined and only handles:

- Injecting `SigLoMaHandler`
- Defining handshake rules

For example:

```
if wait_robot:
    self.add_handshake_rule(
        "Robot Connection",
        lambda: hasattr(self.nodes.get("robot"), "low_state"),
    )
```

The actual loop rate is controlled by constructor arguments:

- Simulation: `200Hz`
- Real robot: `50Hz`

## 3. The handler drives global control-state transitions

The core logic lives in:

```
quad_deploy/handlers/sigloma_handler.py
```

This handler uses the "write `manager.state` directly" style. Common states include:

- `cold_start`
- `recovery`
- `human_teleop`
- `turn`
- `navigation`
- `gripper_start`
- `emergency`

Transitions are jointly determined by:

- Joystick buttons
- Whether VLM messages have arrived
- Whether the current agent is `done`
- Auto-trigger conditions

## 4. `BaseRLAgent` shows how high-frequency agents are organized

`quad_deploy/agents/base_rl_agent.py` is especially valuable as a reference because it keeps the common structure of high-frequency agents very clean:

- Read `robot` and `joystick` from nodes
- Parse configuration
- Maintain observation history with `CircularBuffer`
- Use `decimation` to control real inference frequency

Key logic:

```
def handle(self):
    if self.timestamp % self.decimation == 0:
        action, p_gains, d_gains, done = self.step()
    else:
        action, p_gains, d_gains, done = None, None, None, None
    self.robot.send_action(action, p_gains, d_gains)
```

This design allows:

- The manager to keep a stable main loop
- Agents to avoid running the full model on every cycle
- Control outputs to remain on one unified interface

## 5. How joystick input and safety states are handled

Inside `SigLoMaHandler.get_state_transition()`, many practical field rules are written explicitly:

- `L2` -> `emergency`
- `L1` -> `recovery`
- `R2` -> force return to `human_teleop`
- `R1` -> enter the automatic control flow from manual mode
- `start` -> trigger the gripper directly

This is a good example of how `ros_base` can keep the chain from human input to state transition to current-agent selection inside one handler.

## 6. Bridging with the upper-level system

`VLM2BobotBridge` receives the following messages from the high-level side:

- `/control/turn`
- `/control/grasp`
- `/geometry_msgs/sigma_points_filtered`
- `/control/object_ready`

and sends back:

- `/control/rl_ready`
- `/control/turn_done`
- `/control/grasp_done`
- `/control/euler_rpy`

Together with `Robot2VLMBridge` in `SigLoMa-VLM`, it forms an upper/lower-level bridge pair.

## 7. How multi-process isolation is connected

Inside `sigloma_run_sdk.py`, the code calls:

```
processes = register_multiprocess_nodes(mp_nodes_dict, cmds_dict)
```

before `rclpy.init()`.

Typical uses in the current code include:

- `socat` for simulated serial ports
- Keyboard-input nodes used in simulation

These are exactly the kind of side processes that should follow the system lifecycle without polluting the main control loop.

## 8. What this project teaches `ros_base` users

For a high-frequency robot control layer, the structure in `quad_deploy` is a strong reference:

1. The manager only owns timing, handshakes, and shutdown
2. The handler owns state transitions and agent selection
3. High-frequency agents share one base class and use `decimation`
4. Protocol bridging stays in nodes
5. Edge tool processes are mounted through the multi-process interface
