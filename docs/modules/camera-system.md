# 模块：相机订阅节点 (CamSubNode)

相较于纯粹的底层驱动硬件读取，`ros_base` 提供的 `CamSubNode` (`ros_base.nodes.camera.cam_sub_node.CamSubNode`) 是一个高度封装的、专为机器人算法端设计的“数据搬运工”。

它的核心作用是将 ROS 2 中的图像类型 (如 `Image`, `CompressedImage`) 自动转化为算法能直接使用的 `numpy.ndarray` 结构，并缓存在内存中供其它模块（Handler/Agent）高速读取。

## 1. 核心特性

1. **多流解析与自适应编解码**：支持同步处理 RGB、Depth 深度图和双目 Infra 红外图像信息。可以自动根据配置判断当前网域流使用的是原图还是 `CompressedImage` 并分别解码。
2. **图像实时预处理**：内建了 Gamma 矫正与限制对比度自适应直方图均衡化 (CLAHE) 支持，无需修改算法逻辑即可应对光照不均和大量阴影的场景。
3. **基于线程的硬件级录制**：内部提供纯后台线程的 OpenCV 多媒体录像机制及同步的系统时间戳日志（无需启动 `rosbag record`引入重复订阅导致潜在阻塞），大大提高运行性能和调试验证效率。

---

## 2. 在 Manager 中的典型用法 (依附模式)

`CamSubNode` 最标准的使用场景是挂载在 `BaseManager` 的节点字典中。

我们以 `homi_vlm` 项目的抓取任务 (`pick_place_run_v3.py`) 为例进行分析：

### 2.1 依赖注册与系统握手
在 Manager 的 `__init__` 函数中，我们通过增加一个握手条件 `Handshake Rule` 来确保真正执行主循环逻辑前，相机的首帧图像已经到达。

```python
class PickPlaceRUNV3(BaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 获取挂载的相机节点实例
        self.camera: CamSubNode = self.nodes["camera"]

        # 添加握手规则：阻塞系统启动，直到 self.camera.img 成功取得数据
        self.add_handshake_rule("Camera Stream", lambda: self.camera.img is not None)
```

然后在执行的主入口将 `CamSubNode` 注册进启动字典：

```python
def main(args):
    # 注册配置字典
    nodes_dict = {
        "camera": CamSubNode,
        # ... 其他 Node
    }
    
    fsm_run = PickPlaceRUNV3(
        node_name="PickPlaceOrchestrator",
        nodes_dict=nodes_dict,
        # ...
    )
    fsm_run.start_main_loop_timer()
```

### 2.2 算法处理处读取数据
在具体执行逻辑的 `BaseHandler` (如 `PickPlaceFSMHandlers`) 或 `BaseAgent` 内部，不再需要像原生 ROS 那样书写独立的回调函数存储图像，你可以直接读取缓存在节点属性中的 `numpy` 数据。

```python
class PickPlaceFSMHandlers(BaseHandlers):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 从资源池拿到相机的引用
        self.camera: CamSubNode = self.nodes.get("camera")

    def handle_ai_confirm_pick(self):
        # 【关键】非常直观地同步获取最新图像矩阵 (H, W, C)
        img = self.camera.img  
        
        # 也可以同步获取时间戳或深度图
        timestamp = self.camera.img_timestamp
        depth = self.camera.depth
        
        bbox_data = self.get_target_bbox(img, target_type="toy")
        # 后续视觉处理...
```

---

## 3. 高级配置参数

在新版本的 `ros_base` 架构中，相机的配置参数已被模块化为 `CameraProfile` 数据类。在实例化 `CamSubNode` 或在 Manager 注册时传递 `kwargs` 时，可以使用以下关键参数：

| 参数名称 | 类型 | 默认值 | 描述说明 |
| :--- | :--- | :--- | :--- |
| `config` | `str` 或 `CameraProfile` | `"realsense_d435i_align"` | 相机类型模板映射。内置支持 `realsense_d435i`、`realsense_d435i_compressed`、`zed_mini` 等配置预设。 |
| `record` | `bool` | `False` | 开启多线程视频数据持久化写入，日志文件落盘存储到 `~/Data/rosbags/`。 |
| `record_fps` | `int` | `20` | 控制写盘时的限制帧率。 |
| `vis_rgb` | `bool` | `False` | 自动开启一个利用 cv2 渲染的低频窗口以供快速可视化。 |
| `vis_depth` | `bool` | `False` | 可视化 Jet Colormap 后的深度数据图像。 |
| `gamma` | `float` | `2.0` | Gamma 光照矫正系数，大于 1 提升环境亮度。 |
| `use_clahe` | `bool` | `False` | 开启局部对比度增强，对阴影和细节提亮有显著帮助。 |

### 独立测试与验证
你可以脱离 Manager 直接作为独立 Node 测试相机的联通性，由于内部重写了独立模式方法，支持快速用命令测试：

```bash
python3 /home/robot/project/ros_base/ros_base/nodes/camera/cam_sub_node.py \
    --camera realsense_d435i_align \
    --vis_rgb \
    --clahe
```
