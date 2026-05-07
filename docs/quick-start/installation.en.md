<!-- i18n-sync: source=docs/quick-start/installation.md; sha256=34B14DCD1D93A5E50CD5B19F74015CB838E29B0EA9814BABDE91FB3AA946A317 -->
# Environment Setup and Installation

## 1. Runtime assumptions

The current `ros_base` codebase mainly targets ROS2 Python workflows on Linux. The installation method should match the actual runtime scenario instead of being limited to one environment:

- Desktop development and `sim2sim` debugging: `RoboStack + Conda/Mamba` is convenient for isolated environments
- Real-robot deployment: system-level ROS2 installation is usually a better fit and should stay aligned with the robot runtime

When launching nodes on a Unitree robot, it is recommended to run `setup_id1.sh` first. In practice this script usually does two things:

- `source` the system-level ROS2 environment
- Set `ROS_DOMAIN_ID=1`

This reduces the chance of DDS channel conflicts with the ROS/DDS stack used by the Unitree SDK.

### Requirements

- A system-level ROS2 installation, or Miniforge / Mambaforge / another compatible Conda distribution
- Python 3
- `git`
- `tmux` if you plan to use `BaseLauncher`

Example:

```bash
sudo apt install git tmux
```

## 2. Install `ros_base`

### Option A: RoboStack for desktop and `sim2sim`

A common RoboStack-based setup looks like this:

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

### Option B: system-level ROS2 for real-robot deployment

For real-robot deployment, it is often better to use the system-level ROS2 environment directly and install `ros_base` on top of it:

```bash
source /opt/ros/humble/setup.bash
cd ~/Project
git clone https://github.com/11chens/ros_base.git
cd ros_base
pip install -e .
```

If the real environment is not `humble`, or the robot already provides its own initialization script, replace the command accordingly.

For Unitree robots, it is usually better to centralize environment setup in `setup_id1.sh`, for example:

```bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=1
```

In practice, these two lines are often wrapped into one script and then sourced first by the launch script or by `BaseLauncher`.

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
