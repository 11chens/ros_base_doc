# 环境配置与安装

## 1. 运行前提

`ros_base` 当前代码主要面向 Linux 下的 ROS2 Python 工作流。安装方式需要结合运行场景选择，而不是只限定为一种环境：

- 电脑端开发、`sim2sim` 调试：`RoboStack + Conda/Mamba` 更方便管理独立环境
- 真机部署：更推荐使用系统级 ROS2 安装，并与机器人现有运行环境保持一致

如果是在宇树真机上启动各个节点，推荐统一先执行 `setup_id1.sh`。这个脚本通常会完成两件事：

- `source` 系统级 ROS2 环境
- 设置 `ROS_DOMAIN_ID=1`

这样可以避免和宇树自带 SDK 所使用 DDS 通道发生冲突。

### 基础要求

- 系统级 ROS2 安装，或 Miniforge / Mambaforge / 其他兼容的 Conda 发行版
- Python 3
- `git`
- 如果要使用 `BaseLauncher`，还需要 `tmux`

示例：

```bash
sudo apt install git tmux
```

## 2. 安装 `ros_base`

### 方案 A：电脑端 / `sim2sim` 使用 RoboStack

```bash
mamba create -n rosbase python=3.10
conda activate rosbase
mamba install -c conda-forge -c robostack-humble ros-humble-desktop
source $CONDA_PREFIX/setup.bash
```

如项目使用其他 ROS2 发行版，可将上例中的 `humble` 替换为实际所需版本。

随后安装 `ros_base`：

```bash
cd ~/Project
git clone https://github.com/11chens/ros_base.git
cd ros_base
pip install -e .
```

这种方式的优点是：

- ROS2 运行环境与系统环境隔离
- 不占用系统目录中的 `/opt/ros`
- 便于为不同项目维护不同版本的 ROS2 依赖

### 方案 B：真机部署使用系统级 ROS2

如果项目部署在真机，通常更推荐直接使用系统级 ROS2 环境，再在该环境下安装 `ros_base`：

```bash
source /opt/ros/humble/setup.bash
cd ~/Project
git clone https://github.com/11chens/ros_base.git
cd ros_base
pip install -e .
```

如实际环境不是 `humble`，或机器人侧已经封装了自己的初始化脚本，可替换成对应命令。

对于宇树真机，更推荐将环境初始化统一收口到 `setup_id1.sh`，例如：

```bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=1
```

实际使用时，往往会把这两步写进一个脚本中，再在启动脚本或 `BaseLauncher` 里优先执行它。

## 3. 验证安装

```bash
python3 -c "import ros_base; print('ros_base import ok')"
```

也可以直接验证某个核心模块：

```bash
python3 -c "from ros_base.manager.base_manager import BaseManager; print(BaseManager)"
```

## 4. 验证独立节点模式

以 RealSense 相机订阅节点为例，独立模式下需自行初始化 `rclpy`，而不是只运行一个纯 Python 类。

```bash
python3 ros_base/nodes/camera/cam_sub_node.py --camera realsense_d435i_align --vis_rgb
```

这条命令适合用来快速验证：

- ROS2 topic 是否正常
- 图像是否进来了
- `CamSubNode` 的独立模式是否能工作

## 5. 本地预览文档站点

如需维护 `ros_base_doc`：

```bash
cd ~/Project
git clone https://github.com/11chens/ros_base_doc.git
cd ros_base_doc
pip install -r requirements.txt
mkdocs serve
```

当前文档站的依赖较为轻量，仅需：

- `mkdocs-material`
- `mkdocs-static-i18n`
