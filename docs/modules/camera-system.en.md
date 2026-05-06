<!-- i18n-sync: source=docs/modules/camera-system.md; sha256=4DB67C0B7CCA361755D3045EA278AC2C13FADE6B1A96A58D12F37C79F088132C -->
# Module: Camera Subscriber Node (`CamSubNode`)

`CamSubNode` is one of the most mature reusable nodes in `ros_base`. Its responsibilities are clear:

- Subscribe to RGB, depth, infra, and `CameraInfo`
- Convert ROS image messages into `numpy.ndarray` automatically
- Cache the latest results into readable attributes
- Provide lightweight visualization and recording when needed

## 1. Data exposed by the current implementation

After the node starts, commonly used attributes include:

- `img`: latest RGB image, `numpy.ndarray`
- `img_timestamp`
- `img_shape`
- `depth`
- `depth_timestamp`
- `depth_shape`
- `rgb_info`
- `infra1` / `infra2`
- `infra1_info`
- `infra_fx`
- `infra_baseline`

That is why handlers and agents can write:

```
img = self.camera.img
depth = self.camera.depth
timestamp = self.camera.img_timestamp
```

## 2. Supported camera configurations

`CamSubNode` currently accepts either a string preset or a `CameraProfile` as `config`.

Built-in string presets include:

- `realsense_d435i`
- `realsense_d435i_compressed`
- `realsense_d435i_align`
- `realsense_d435i_align_compressed`
- `realsense_d435i_infra`
- `zed_mini`

One detail to note: although the constructor type hint mentions `dict`, the current implementation actually accepts only:

- `str`
- `CameraProfile`

## 3. Typical usage in attached mode

The entry script in `SigLoMa-VLM` registers it directly into `nodes_dict`:

```
nodes_dict = {
    "vlm_node": Robot2VLMBridge,
    "joystick": JoystickSDKNode,
    "camera": CamSubNode,
}
```

Then the manager uses a handshake rule to guarantee that the first frame has arrived:

```
self.add_handshake_rule(
    "Camera Stream",
    lambda: self.nodes["camera"].img is not None,
)
```

That way, by the time `handlers.handle()` actually starts, a valid image is usually already available.

## 4. Typical parameters

| Parameter | Default | Description |
| --- | --- | --- |
| `config` | `"realsense_d435i_align"` | Preset camera configuration |
| `record` | `False` | Whether to record video in a background thread |
| `record_fps` | `20` | Maximum recording frame rate |
| `vis_rgb` | `False` | Show an RGB window |
| `vis_depth` | `False` | Show a pseudo-color depth window |
| `gamma` | `2.0` | Gamma preprocessing |
| `use_clahe` | `False` | CLAHE local contrast enhancement |

### Recording behavior

If `record=True`, the current implementation will:

- Start a background thread
- Write images to an `mp4`
- Write timestamps into a text file

The output directory format is:

```
~/Data/rosbags/track_session_YYYYMMDD_HHMM/
```

## 5. Standalone debugging

The source file already provides a command-line entry:

```
python3 ros_base/nodes/camera/cam_sub_node.py \
    --camera realsense_d435i_align \
    --vis_rgb \
    --clahe
```

If you also want to inspect depth:

```
python3 ros_base/nodes/camera/cam_sub_node.py \
    --camera realsense_d435i_align \
    --vis_rgb \
    --vis_depth
```

## 6. Working with `PoseProcessor`

`CamSubNode` itself only acquires images and camera info. The actual conversion from:

- `bbox + depth`
- `odom`
- `camera extrinsics`

into world coordinates is handled by `ros_base.nodes.camera.pose_processor.PoseProcessor`.

In `SigLoMa-VLM`, this object is held by `Robot2VLMBridge.pose_processor` and is used to:

- Get the robot base position in the world frame
- Convert a selected target box into world coordinates

## 7. What it should and should not do

Good responsibilities:

- Subscribe to and cache the latest image data
- Lightweight preprocessing
- Temporary visualization
- Development-time recording

Poor responsibilities:

- Running heavy model inference inside callbacks
- Holding the whole vision business logic
- Mixing complex state machines into a single callback

Those parts should stay in agents and handlers.
