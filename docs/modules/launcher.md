# 基类编排启动系统 (Base Launcher System)

`BaseLauncher` 是 `ros_base` 里专门负责“把很多进程按统一方式拉起来”的工具。它不替代 ROS launch，而是更偏向机器人项目里常见的：

- 多工程目录
- Conda + ROS 混合环境
- tmux 常驻调试
- CPU 绑核

## 1. 当前实现的行为

`BaseLauncher` 主要完成以下工作：

1. 读取 YAML 配置
2. 解析一个或多个 session
3. 杀掉同名旧 tmux session
4. 创建一个 `MAIN` window，并不断 `split-window`
5. 在每个 pane 中依次完成：
   - 可选 `source ros_setup`
   - 可选 `conda activate`
   - `cd` 到目标工程目录
   - 执行 `command`

## 2. 配置文件结构

当前实现支持两种写法：

- 根对象就是单个 session
- 根对象里有 `sessions:`，表示多个 session

每个 session 的核心字段如下：

```
env:
  session_name: "sigloma_system"
  workspace_root: "~/Project"
  ros_setup: "~/unitree_ros2/setup_id1.sh"
  conda_env: "sigloma_run"

nodes:
  - name: "RL_CONTROL"
    project: "quad_deploy"
    cpus: "7"
    autostart: true
    command: "python quad_deploy/scripts/sigloma/sigloma_run_sdk.py"
```

### `env`

- `session_name`: tmux 会话名
- `workspace_root`: 所有 `project` 的根目录
- `ros_setup`: 可选，先 source 的 ROS 环境脚本
- `conda_env`: 可选，先激活的 Conda 环境

### `nodes`

每个节点配置代表一个 tmux pane：

- `name`: 节点标识名
- `project`: 相对 `workspace_root` 的工程目录
- `command`: 字符串或字符串列表
- `cpus`: 可选，第一条命令前加 `taskset -c`
- `autostart`: 默认为 `true`

## 3. 一个更贴近当前代码的例子

```
sessions:
  - env:
      session_name: "sigloma_system"
      workspace_root: "~/Project"
      ros_setup: "~/unitree_ros2/setup_id1.sh"
      conda_env: "sigloma_run"

    nodes:
      - name: "LOW_LEVEL"
        project: "quad_deploy"
        cpus: "7"
        command: "python quad_deploy/scripts/sigloma/sigloma_run_sdk.py"

      - name: "HIGH_LEVEL"
        project: "SigLoMa-VLM"
        cpus: "4-5"
        command: "python sigloma_vlm/scripts/pick_place_run.py"

      - name: "KALMAN"
        project: "ros_base"
        command: "python ros_base/nodes/kalman/kf_sigma_node.py"
```

## 4. 命令解析的几个细节

### 配置路径解析

`BaseLauncher` 会先尝试：

1. 当前工作目录
2. 再尝试相对 `ros_base/launch/base_launcher.py` 所在目录

所以业务仓既可以直接传绝对路径，也可以把 `launch_cfg.yaml` 放在启动脚本旁边。

### `command` 可以是列表

如果是：

```
command:
  - "isaac_ros_container"
  - "source vslam.sh"
  - "launch_vslam"
```

启动器会依次向同一个 pane 发送多条命令。

### `cpus` 只作用在第一条命令

当前实现只会对 `command` 的第一条命令加 `taskset -c ...`。当 `command` 为命令列表时，后续命令不会自动再次添加绑核前缀。

## 5. 启动时的筛选功能

命令行支持：

```
python ros_base/launch/base_launcher.py launch_cfg.yaml --enable LOW_LEVEL
python ros_base/launch/base_launcher.py launch_cfg.yaml --disable KALMAN
```

规则是：

- `disable_nodes` 里的项目直接跳过
- `enable_nodes` 里的项目强制启用
- 其余节点看 `autostart`

## 6. 适合放在哪里

`BaseLauncher` 本身在 `ros_base` 里，但更推荐在业务仓封一层薄入口，例如：

```
SigLoMa-VLM/
└── launch/
    ├── sigloma_launch.py
    └── launch_cfg.yaml
```

这样团队成员只需要记住业务仓自己的启动命令。

## 7. tmux 常用操作

- 分离会话：`Ctrl + B`，再按 `D`
- 恢复会话：`tmux attach -t sigloma_system`
- 查看 pane：`Ctrl + B` 后方向键切换

如果你已经习惯 tmux，这个启动器最大的价值就是把“环境初始化 + 目录跳转 + 节点启动”统一固化成配置，而不是每次手敲。
