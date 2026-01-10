# 模块：异步可视化

🚧 **文档编写中**

`ros_base` 提供了一套高效的异步可视化工具，避免 `cv2.imshow` 阻塞主线程。

```python
from ros_base.utils.visualizer import AsyncVisualizer

viz = AsyncVisualizer()
viz.show("Camera", img)
```
