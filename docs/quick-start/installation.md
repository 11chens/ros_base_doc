# 环境配置与安装

## 1. 前置依赖

### 操作系统
*   **Ubuntu 22.04** (推荐 ROS2 Humble) 或 **Ubuntu 20.04** (ROS2 Foxy)
*   **Linux** 内核建议 5.15+ (如果使用最新的硬件驱动)

### 软件环境
*   **ROS2**: 确保已安装完整的 Desktop 版本。
    ```bash
    # Ubuntu 22.04 示例
    sudo apt install ros-humble-desktop
    ```
*   **Python**: 3.8 或更高版本。
*   **基础工具**:
    ```bash
    sudo apt install python3-pip git
    ```

---

## 2. 安装 ros_base

我们将以“源码安装 (Source Installation)”的方式进行，以便您随时查看核心代码或进行修改。

### 步骤 1: 克隆仓库
建议将代码放在您的工作空间中（例如 `~/project`）。

```bash
cd ~/project
git clone https://github.com/11chens/ros_base.git
```

### 步骤 2: 安装 Python 依赖
进入仓库目录，使用 `pip` 以可编辑模式安装。这会自动解析 `setup.py` 中的依赖。

```bash
cd ros_base
pip install -e .
```

!!! tip "为什么使用 `-e` (Editable Mode)?"
    使用 `-e` 安装意味着您对 `ros_base` 源码的任何修改都会立即生效，无需重新安装。这对于正在开发中的项目非常有用。

---

## 3. 验证安装

安装完成后，可以通过以下 Python 命令验证是否成功导入。

```bash
python3 -c "import ros_base; print('ros_base installed successfully at:', ros_base.__file__)"
```

如果输出类似 `/home/robot/project/ros_base/ros_base/__init__.py` 的路径且没有报错，说明安装成功。

### (可选) 验证 ROS2 环境
确保您的终端已经 sourced 了 ROS2 的环境文件：
```bash
source /opt/ros/humble/setup.bash
# 或者将其加入 ~/.bashrc
```
