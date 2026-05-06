<!-- i18n-sync: source=docs/core-concepts/handler.md; sha256=840544420200B80AAEAD4DABE5491CE1B83B7DE207647E780C978234E8F531ED -->
# BaseHandlers: State Machines and Scheduling

`BaseHandlers` is the best place in `ros_base` to hold the main application logic. It turns a system from "callbacks scattered everywhere" into "observe state once per cycle and make one coherent decision".

## 1. What the base class actually provides

The current `BaseHandlers` initialization is straightforward:

```
class BaseHandlers:
    def __init__(self, manager=None, *args, **kwargs):
        self.manager = manager
        self.nodes = manager.nodes if manager else {}
        self.agents = manager.agents if manager else {}
```

It also exposes several useful properties:

- `self.logger`
- `self.timestamp`
- `self.node_freq_hz`
- `self.state`

`self.state` wraps `manager.state` and supports direct write-back:

```
self.state = "navigation"
```

## 2. Why handlers matter

ROS callbacks are good for receiving messages, but they are not a good place to organize a complete task. Once a system mixes vision, control, human intervention, and state switching, logic spread across callbacks quickly loses a reliable execution order.

The handler exists to:

- Observe the system on one fixed cadence
- Decide what to call based on the current state
- Keep one cycle of logic in a clear, predictable order

## 3. Two styles used in the current repositories

### Style A: the handler owns its own FSM

`PickPlaceFSMHandlers` in `SigLoMa-VLM` uses:

```
self.current_state
self.prev_state
```

The pattern is:

1. Check whether a state transition should happen
2. Run on-enter logic
3. Execute the cycle logic for the current state

This is a strong fit for task-flow FSMs such as:

- Wait for the user to mark a target
- Rotate toward the target
- Request VLM confirmation
- Track and grasp

### Style B: directly drive `manager.state`

`SigLoMaHandler` in `quad_deploy` uses:

```
new_state = self.get_state_transition()
if new_state:
    self.state = new_state
    self.on_state_enter(new_state)
```

This style works well for global control states such as:

- `cold_start`
- `human_teleop`
- `turn`
- `navigation`
- `emergency`

## 4. Recommended FSM structure

No matter which style you choose, this structure is recommended:

```
def handle(self):
    if state_changed:
        self.on_state_enter(...)

    if current_state == ...:
        ...
    elif current_state == ...:
        ...
```

### Why separate these parts

Some actions should happen only once when a state changes, for example:

- Reset a done flag
- Clear UI markers
- Reset an agent
- Publish a one-shot trigger command

Other actions must run on every cycle, for example:

- Read the latest image
- Call a tracker
- Send the current control output

## 5. Two good habits from real projects

### Habit A: clean up edge-state residue when entering a new state

When switching states, `PickPlaceFSMHandlers` will:

- `reset_action_states()`
- Clear UI sigma points
- Clear masks

This greatly reduces the chance that leftovers from one state pollute the next one.

### Habit B: only do heavy recomputation when new data arrives

During grasp and place stages, `PickPlaceFSMHandlers` compares `camera.img_timestamp` and updates the tracker only when a new frame arrives:

```
if self._last_grasp_timestamp != self.camera.img_timestamp:
    ...
```

This is a very practical throttling pattern that avoids recomputing the same image frame many times.

## 6. What belongs in a handler

Good candidates:

- State machines
- Cross-module scheduling
- Resource startup and shutdown order
- Decision branches

Poor candidates:

- Large-model inference details
- Internal image-algorithm implementation
- Low-level ROS subscription and publication details

Those parts should stay in agents and nodes respectively.
