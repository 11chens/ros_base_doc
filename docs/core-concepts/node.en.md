<!-- i18n-sync: source=docs/core-concepts/node.md; sha256=3FBDAAB900E7AE08F499015D3417FCC510EF0D715C4D7A902AF9A87F7460854D -->
# BaseNode: Dual-Mode Node

`BaseNode` is the common base class for communication modules in `ros_base`. Its most important feature is not "inheriting from a ROS node", but **making the same business code work in two runtime modes**:

- Attached mode: mounted onto a `BaseManager`
- Standalone mode: runs as an independent ROS2 node

## 1. The actual structure in the current implementation

The core logic of `BaseNode.__init__()` is:

```
def __init__(self, manager=None, *args, **kwargs):
    self._manager = manager if manager is not None else Node(*args, **kwargs)
```

In practice:

- When `manager` exists, `self._manager` is that `BaseManager`
- When `manager` is absent, `self._manager` is a temporary `rclpy.node.Node`

The following interfaces are then forwarded to `self._manager`:

- `create_publisher`
- `create_subscription`
- `create_timer`
- `destroy_publisher`
- `destroy_subscription`
- `get_clock`

## 2. Attached mode

This is the most common production setup. In this mode, a node only needs to:

- Subscribe to ROS messages
- Cache results into its own attributes
- Provide publish methods when needed

For example:

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

Then a handler or agent can read data directly:

```
img = self.nodes["camera"].img
```

There is no need to create another internal topic just to pass images between modules in the same system.

## 3. Standalone mode

The current implementation supports calling:

```
node.start_spin_standalone()
```

One detail is easy to miss: **standalone mode still requires `rclpy.init()` first.**

Standard template:

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

`CamSubNode` and `Robot2VLMBridge` both provide this kind of standalone entry point in the source tree.

## 4. Context exposed by default

When attached to a manager, `BaseNode` can access:

- `self.nodes`
- `self.agents`
- `self.logger`
- `self.timestamp`
- `self.node_freq_hz`

This makes it possible for a node to read system context, but it is still better to keep boundaries clear:

- Nodes are good at caching and bridging
- Complex business scheduling should stay out of nodes
- Nodes should not actively call agents or handlers in reverse, because that introduces coupling in the wrong direction

## 5. Resource cleanup

`BaseNode.release_resources()` is an empty method in the base class and is meant to be overridden by subclasses.

Typical cases include:

- Closing a video writer
- Stopping a background thread
- Closing a window
- Releasing a serial port or hardware handle

For example, `CamSubNode.release_resources()` stops the recording thread and closes the output video file.

## 6. The typical bridge role

In the two example projects, nodes often act as protocol boundary layers:

- `SigLoMa-VLM/sigloma_vlm/nodes/robot2vlm.py`
  publishes high-level perception results to the lower-level system and subscribes to `rl_ready`, `turn_done`, and `grasp_done`
- `quad_deploy/quad_deploy/nodes/sigloma/vlm2robot.py`
  receives upper-level control signals and sends back `rl_ready`, `turn_done`, and `grasp_done`

The ideal shape of this kind of node is:

- Complex outside-facing protocol
- Simple inside-facing interface
- Business logic still kept inside handlers and agents
