<!-- i18n-sync: source=docs/index.md; sha256=B22AA9726C25FBC1E9183C80C88D0A35AE9CD75C50C0A4A6F5130448D0681BBC -->
# ROS Base Project

**ROS Base** is a ROS2 Python framework for complex robotic applications. Its goal is not to wrap ROS one more time, but to reduce the engineering problems that most easily grow out of control in large projects into a fixed structure:

- How to separate communication, algorithms, state machines, and lifecycle management.
- How to share context inside one main process without turning the codebase into one giant node.
- How to move high-load modules into separate processes when needed while keeping the whole system under one main flow.

This documentation is synced to the current `ros_base` implementation and explains the framework through two real projects:

- `SigLoMa-VLM`: low-frequency task orchestration, VLM calls, and visual tracking.
- `quad_deploy`: high-frequency RL control, hardware bridging, and joystick-driven state machines.

---

## Why ROS Base

When building robot projects, teams often swing between two extremes:

=== "Approach A: One Large Node"

    All subscriptions, caches, algorithms, and control logic live in one class.

    Pros:

    - Data access is simple and adds almost no extra communication overhead.

    Cons:

    - Module boundaries become blurry, which makes maintenance and reuse difficult.
    - Testing one part of the logic often requires launching the whole system.
    - State machines, callbacks, and algorithm calls easily become tangled together.

=== "Approach B: Everything as Separate Processes"

    Every function becomes an independent ROS node connected by topics or services.

    Pros:

    - Physical isolation is clear and module boundaries are explicit.

    Cons:

    - Startup chains become complicated and debugging costs increase.
    - Cross-process serialization becomes expensive, especially for images and high-frequency control.
    - Handshakes, state synchronization, and resource cleanup become harder to manage.

### The ROS Base compromise

ROS Base uses a **single main node + in-process composition + optional multi-process sidecars** pattern:

![Architecture](images/framework.png)

1. `BaseManager` is the only core object in the main process that directly inherits `rclpy.node.Node`.
2. `BaseNode` acts as the communication wrapper layer. When attached to a manager, it reuses the same ROS node. When debugged independently, it can also spin on its own.
3. `BaseAgent` holds computation logic and does not own publishers or subscriptions directly.
4. `BaseHandlers` drives scheduling, business flow, and state machines.
5. Modules that genuinely slow down the main loop can be mounted into separate processes through `register_multiprocess_nodes()`.

---

## Quick Start

```bash
git clone https://github.com/11chens/ros_base.git
cd ros_base
pip install -e .
```

To preview this documentation site locally:

```bash
git clone https://github.com/11chens/ros_base_doc.git
cd ros_base_doc
pip install -r requirements.txt
mkdocs serve
```

The recommended next step is to read [Installation](quick-start/installation.md) and [Architecture](quick-start/architecture.md).
