<!-- i18n-sync: source=docs/modules/utils.md; sha256=A8977BC39A925BE25C0F8E9F0D3BD6CE8ACA7F4B1E46CACC378EBBD608E23B88 -->
# Module: Common Utilities

The utility set under `ros_base.utils` is not large, but it is practical. The most reusable pieces in the current codebase are the following groups.

## 1. `profile_latency`

Location:

```python
from ros_base.utils.decorators import profile_latency
```

It measures two kinds of latency during function calls:

- `cycle latency`: how much time passed since the previous call
- `processing latency`: how long the current function itself took

If the input is a ROS message, it can also inspect capture latency from `header.stamp` to the current time.

Example:

```python
@profile_latency(
    cycle_threshold_ms=100.0,
    process_threshold_ms=50.0,
    log_interval_s=3.0,
    debug=True,
)
def step(self):
    ...
```

Good places to use it:

- `step()` in a high-frequency agent
- A key node callback
- The main update function of a filter or control module

## 2. `CustomLogger`

Location:

```python
from ros_base.utils.logger import CustomLogger
```

This is a lightweight wrapper around `loguru` that keeps many ROS-style logging patterns:

- `info`
- `warning`
- `warn`
- `error`
- `log_once`
- `log_throttle`
- `important`

For example:

```python
self.logger.info("Camera stream ready", once=True)
self.logger.log_throttle("Waiting for VLM...", seconds=2.0)
self.logger.important("Entering State: navigation")
```

Inside `BaseManager`, it can be injected through `custom_logger=CustomLogger`.

## 3. `CameraTrans`

Location:

```python
from ros_base.utils.camera_trans import CameraTrans
```

This class focuses on geometric computation and is useful for:

- base frame -> camera frame
- camera frame -> image plane
- image + depth -> back-projection

It depends on `CameraProfile` and is suitable for standalone use in visual simulation, projection checking, and coordinate-transform validation.

## 4. `math_utils`

Frequently used functions and classes include:

- `CircularBuffer`
- `VectorLPFilter`
- `warp2pi`
- `quat_to_rpy`
- `rpy_to_quat`
- `trans_ros_frame_to_opt_frame`
- `trans_opt_to_ros_frame`

`CircularBuffer` is already used directly inside `BaseRLAgent` in `quad_deploy` to maintain observation history:

```python
self.obs_hist = CircularBuffer(self.len_history)
```

## 5. Debug-entry helpers

Many standalone scripts use:

```python
from ros_base.utils.args_debug import add_debug_mode
```

Its purpose is to let a script accept common debug arguments quickly, which makes it easier to run one node or one entry script independently.

## 6. Suggested starting points

For a project that is adopting `ros_base` for the first time, the most useful utilities to start with are usually:

1. `CustomLogger`
2. `profile_latency`
3. `CircularBuffer`

Together, they cover:

- Logging normalization
- Performance diagnosis
- History buffering for high-frequency control
