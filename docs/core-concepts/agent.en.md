<!-- i18n-sync: source=docs/core-concepts/agent.md; sha256=15D6041969F3F591DAA546E2A32191D0338553841D1A7CFF2D645258218C326D -->
# BaseAgent: Computation and Algorithms

`BaseAgent` is the main component for algorithms and computation in `ros_base`. Its responsibility is centered on algorithm logic, internal state, and the organization of computation flow.

## 1. What the base class provides today

The current `BaseAgent` implementation is intentionally lightweight:

```
class BaseAgent(ABC):
    def __init__(self, manager=None, *args, **kwargs):
        self._manager = manager
        self._logger = CustomLogger(self.__class__.__name__)
```

The base class exposes these context properties by default:

- `self.logger`
- `self.nodes`
- `self.agents`
- `self.timestamp`
- `self.state`
- `self.node_freq_hz`
- `self.get_clock()`

Among them, `reset()` is abstract and must be implemented by subclasses. `handle()` is left open for the subclass to define when needed.

## 2. What a good agent usually looks like

A good agent typically satisfies three conditions:

1. Clear inputs
2. Clear outputs
3. Computation logic that can be tested independently

For example:

```
class TrackerAgent(BaseAgent):
    def handle_initial_bbox(self, initial_bbox, img):
        ...

    def handle_sigma(self, img, depth, timestamp):
        ...

    def reset(self):
        ...
```

The important point is that these core methods consume regular Python or NumPy data, not the ROS pub/sub process itself.

## 3. Two typical kinds of agents

### Task-oriented agents

Examples from `SigLoMa-VLM`:

- `QwenVLMAgent`: cloud VLM calls, low frequency, high latency
- `TrackerAgent`: image tracking and sigma-point generation
- `UIAgent`: user interface and on-screen interaction during the task flow

These agents often:

- Are not suitable to run on every frame
- Need to be scheduled by the handler in specific states
- Must avoid blocking the whole main loop

### Control-oriented agents

Examples from `quad_deploy`:

- `StandAgent`
- `SigLoMaLocoAgent`
- `SigLoMaNavAgent`
- `SigLoMaTurnAgent`

Most of them inherit from `BaseRLAgent`, with these characteristics:

- High runtime frequency
- Stable behavior required on every cycle
- `decimation` used to control the real model-inference cadence

## 4. `BaseRLAgent` shows a useful pattern for high-frequency agents

`BaseRLAgent` in `quad_deploy` is a strong reference:

```
def handle(self):
    if self.timestamp % self.decimation == 0:
        action, p_gains, d_gains, done = self.step()
    else:
        action, p_gains, d_gains, done = None, None, None, None
    self.robot.send_action(action, p_gains, d_gains)
```

This shows that inside the `ros_base` architecture, an agent does not need to perform a full recomputation every time `handle()` runs. Common strategies include:

- Running inference every N frames
- Doing only lightweight post-processing at high frequency
- Decoupling heavy computation from control output

## 5. About context access

Although an agent can access `self.nodes` and `self.agents` directly, it is better to treat that as a wiring convenience rather than the core design style.

A more stable pattern is:

- Read data in the handler
- Pass only the required data into the agent as arguments
- Let the agent focus on the current task

For example:

```
img = self.camera.img
bbox = self.QVLM.handle_bbox(img_np=img, curr_target="toy", multi=False)
```

instead of making deep agent methods fetch `self.nodes["camera"]` everywhere.

## 6. Suggestions for offline testing

If you want an agent to be easier to test without ROS:

- Keep constructors for model loading and lightweight configuration only
- Let core methods accept regular data types whenever possible
- Do not hard-code topic names, QoS policies, or message types into the agent

With that structure, the agent can still be instantiated directly even without a manager, while continuing to use `self._logger` for logging.
