<!-- i18n-sync: source=docs/quick-start/installation.md; sha256=4149D339591149A102C8C64269799C925A11AA9DDE0211C4D3F7EE20C6DA664D -->
# Environment Setup and Installation

## 1. Runtime assumptions

The current `ros_base` codebase mainly targets ROS2 Python workflows on Linux. The recommended setup is to install ROS2 through **RoboStack + Conda/Mamba**, keeping the runtime inside an isolated environment instead of installing into system-managed directories.

### Requirements

- Miniforge, Mambaforge, or another compatible Conda distribution
- Python 3
- `git`
- `tmux` if you plan to use `BaseLauncher`

Example:

```bash
sudo apt install git tmux
```

## 2. Install `ros_base`

It is recommended to create a dedicated RoboStack environment first, then install ROS2 and `ros_base` inside that environment. A common setup looks like this:

```bash
mamba create -n rosbase python=3.10
conda activate rosbase
mamba install -c conda-forge -c robostack-humble ros-humble-desktop
source $CONDA_PREFIX/setup.bash
```

If your project uses a different ROS2 distribution, replace `humble` with the required release.

Then install `ros_base`:

```bash
cd ~/Project
git clone https://github.com/11chens/ros_base.git
cd ros_base
pip install -e .
```

This setup has several practical advantages:

- The ROS2 runtime stays isolated from the host system.
- It does not occupy a system directory such as `/opt/ros`.
- Different projects can keep different ROS2 dependency versions more easily.

## 3. Verify the installation

```bash
python3 -c "import ros_base; print('ros_base import ok')"
```

You can also verify one of the core modules directly:

```bash
python3 -c "from ros_base.manager.base_manager import BaseManager; print(BaseManager)"
```

## 4. Verify standalone node mode

Use the RealSense camera subscriber as an example. In standalone mode, `rclpy` must be initialized explicitly instead of running the file as a pure Python class.

```bash
python3 ros_base/nodes/camera/cam_sub_node.py --camera realsense_d435i_align --vis_rgb
```

This command is useful for quickly checking:

- Whether the ROS2 topic is available
- Whether images are arriving
- Whether standalone mode for `CamSubNode` works as expected

## 5. Preview the documentation site locally

If you are maintaining `ros_base_doc`:

```bash
cd ~/Project
git clone https://github.com/11chens/ros_base_doc.git
cd ros_base_doc
pip install -r requirements.txt
mkdocs serve
```

The documentation site has lightweight dependencies. In practice, only these packages are required:

- `mkdocs-material`
- `mkdocs-static-i18n`
