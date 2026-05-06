<!-- i18n-sync: source=docs/examples/sigloma-vlm.md; sha256=F6281CE945437EB7D475EA7E5EB0B9C5B5D6DAD11C8B05287E2D5103F5F3DF91 -->
# Example Project: SigLoMa-VLM

`SigLoMa-VLM` shows a typical `ros_base` setup for high-level task orchestration. Cameras, bridge nodes, VLM calls, trackers, and UI all run under one unified main flow driven by a finite-state machine.

## 1. Current entry file

The current main entry is:

```
sigloma_vlm/scripts/pick_place_run.py
```

It defines:

```
class PickPlaceRUN(BaseManager):
    ...
```

and registers:

### Nodes

- `vlm_node`: `Robot2VLMBridge`
- `joystick`: `JoystickSDKNode`
- `camera`: `CamSubNode`

### Agents

- `vlm_qwen`: `QwenVLMAgent`
- `tracker`: `TrackerAgent`
- `user`: `UIAgent`

## 2. How `ros_base` is used in this project

### The manager owns lifecycle management

`PickPlaceRUN` stays relatively focused, but it is placed at the critical control point:

- Inject `PickPlaceFSMHandlers`
- Add handshake rules based on the `wait` argument
- Close UI, node, and agent resources together on exit

The key handshake rule is:

```
self.add_handshake_rule(
    "Camera Stream",
    lambda: self.nodes["camera"].img is not None,
)
```

### The handler owns the full task-state machine

The actual task flow lives in:

```
sigloma_vlm/handlers/pick_place_fsm.py
```

Its internal states include:

- `WAIT_FOR_PICK_TARGET`
- `WAIT_FOR_PLACE_TARGET`
- `ROTATE_TO_PICK`
- `AI_CONFIRM_PICK`
- `GRASP_EXECUTION`
- `ROTATE_TO_PLACE`
- `AI_CONFIRM_PLACE`
- `PLACE_EXECUTION`
- `FINISHED`

This FSM does not depend directly on `manager.state`. Instead, the handler maintains `current_state` and `prev_state` on its own.

## 3. Three design points worth noticing

### Task logic is separated from the communication layer

- `CamSubNode` only acquires images
- `Robot2VLMBridge` only handles topic communication with the lower-level side
- `QwenVLMAgent` produces detection boxes
- `TrackerAgent` handles tracking and sigma points
- `UIAgent` handles interaction and rendering

The handler only decides who gets called in each state.

### Timestamp checks prevent reprocessing the same frame

During grasp and place stages, the handler first checks:

```
self._last_grasp_timestamp != self.camera.img_timestamp
```

The tracker runs again only when a new camera frame arrives. This pattern is especially useful when a low-frequency camera feeds a higher-frequency main loop.

### Visual results are forwarded to the lower-level side through the bridge

`Robot2VLMBridge` publishes:

- `/control/turn`
- `/control/object_ready`
- `/geometry_msgs/sigma_points`
- `/viz/vlm_bboxes`

and subscribes to:

- `/control/rl_ready`
- `/control/turn_done`
- `/control/grasp_done`

This design keeps the high-level task logic inside one manager without mixing low-level control details directly into the main flow.

## 4. How it works with `PoseProcessor`

Target points in this project do not stop at image coordinates. The system uses:

```
self.vlm_node.pose_processor.get_object_world_position(...)
```

to combine:

- selected target boxes
- depth values
- camera extrinsics
- visual-odometry `odom`

into world coordinates.

This is one of the main reasons why the `CamSubNode + PoseProcessor + Bridge Node` combination works well for task-oriented applications.

## 5. A reusable organization pattern

When building a new high-level task project, the following layering pattern is a good starting point:

1. Use `BaseManager` for the system heartbeat and handshakes
2. Use `CamSubNode` for shared image caching
3. Use one bridge node to talk to the lower-level system
4. Use `BaseHandlers` to implement the task FSM
5. Split detection, tracking, and UI into separate agents
