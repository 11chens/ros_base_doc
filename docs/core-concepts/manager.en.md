<!-- i18n-sync: source=docs/core-concepts/manager.md; sha256=130E9175BDB6A8A36FA7E6236ECFD00E24FA9325388FD17D8CA373C612FF5982 -->
# BaseManager: System Manager

`BaseManager` is the main entry point of the framework. In the current implementation, it is responsible for four things:

1. Register `Node`, `Agent`, and `Handler`
2. Hold a unified ROS2 node context
3. Run handshakes and the main loop
4. Release resources and clean up child processes on exit

## 1. Constructor arguments used in the current codebase

The most common parameters of `BaseManager` are:

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

Registration happens immediately inside `__init__()`:

```
self._register_nodes(nodes_dict, *args, **kwargs)
self._register_agents(agents_dict, *args, **kwargs)
self._register_handlers(handlers_class, *args, **kwargs)
```

That also means many business arguments passed into the manager are forwarded to nodes, agents, and handlers.

## 2. One real usage pattern

The entry script in `SigLoMa-VLM` is a standard example:

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

Startup looks like this:

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

Here `start_main_loop_timer()` handles everything on its own:

- Handshake loop
- `create_timer`
- `rclpy.spin`
- Cleanup and `shutdown`

## 3. The handshake mechanism

Handshake rules are registered through `add_handshake_rule()`:

```
self.add_handshake_rule("Robot Connection", lambda: hasattr(self.nodes["robot"], "low_state"))
```

Before entering the main loop, `start_main_loop_timer()` repeatedly calls `handshake()`:

- If no rules exist, it passes immediately
- If rules exist, all of them must pass
- While a rule is unsatisfied, the manager waits for new messages through `rclpy.spin_once(self, timeout_sec=0.1)`

This is especially useful for the first camera frame, hardware buses, and upper/lower-level bridges.

## 4. What really happens inside the main loop

The current `BaseManager.main_loop()` order is simple:

1. If `get_state_switch()` exists, try to update `self.state`
2. If `state_handle()` exists, run it
3. If `handlers` is registered, run `handlers.handle()`
4. Increment `self.timestamp`
5. Print the loop frequency when needed

Recommended practice:

- Put most business logic inside `BaseHandlers.handle()`
- Keep `manager.state` for top-level state only
- Avoid blocking work inside the high-frequency loop

## 5. `release_resources()` as the business-side cleanup hook

`BaseManager.release_resources()` is an empty hook in the base class. Business repositories are expected to override it.

For example, `PickPlaceRUN.release_resources()` will:

- Close the UI agent
- Iterate through nodes and call `release_resources()`
- Iterate through agents and call `close()`

Any threads, file handles, windows, or hardware connections that require explicit cleanup should be collected here.

## 6. Multi-process mounting

The current codebase exposes two helper functions directly:

```
from ros_base.manager.base_manager import (
    register_multiprocess_nodes,
    shutdown_multiprocess_nodes,
)
```

### `register_multiprocess_nodes()`

It supports two kinds of child processes:

- `mp_nodes_dict`: move a `BaseNode` subclass into a separate Python process
- `cmds_dict`: launch external commands such as `socat` or custom shell scripts

Example from `quad_deploy`:

```
cmds_dict["sim_port"] = (
    "socat -d -d pty,raw,echo=0,link=/tmp/pty10 "
    "pty,raw,echo=0,link=/tmp/pty11 &"
)
processes = register_multiprocess_nodes(mp_nodes_dict, cmds_dict)
```

Then pass `processes` back into the manager:

```
manager.start_main_loop_timer(processes)
```

When the manager exits, it automatically calls `shutdown_multiprocess_nodes(processes)`.

## 7. Usage guidelines

Good candidates to keep inside the same manager:

- Lightweight subscription caches
- High-frequency shared state
- State machines that need strict sequential execution

Good candidates to move out:

- Blocking external commands
- Camera SDKs or third-party tool processes
- Long-running computation that clearly slows down the loop frequency

One manager should not hold everything.

The value of `ros_base` comes from composition, not from moving all logic back into one large class. If high-frequency control and heavy vision inference stay in the same manager for too long, they will eventually slow each other down.
