<!-- i18n-sync: source=docs/modules/launcher.md; sha256=91246C6FA5A995CC9002EB330EF1DD5D2E990C9268EC55B19E3707B2F7ADB05F -->
# Base Launcher System

`BaseLauncher` is the tool in `ros_base` that brings up many processes in one consistent way. It does not replace ROS launch. Instead, it targets patterns that show up frequently in robot projects:

- Multiple project directories
- Mixed Conda and ROS environments
- Long-running `tmux` debugging sessions
- Optional CPU pinning

## 1. What the current implementation does

`BaseLauncher` mainly performs the following steps:

1. Read a YAML configuration file
2. Parse one or more sessions
3. Kill old `tmux` sessions with the same name
4. Create a `MAIN` window and keep calling `split-window`
5. In each pane, execute the following sequence:
   - Optional `source ros_setup`
   - Optional `conda activate`
   - `cd` into the target project directory
   - Run `command`

## 2. Configuration structure

The current implementation supports two layouts:

- The root object is one session
- The root object contains `sessions:`, which means multiple sessions

The core fields of each session are:

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

- `session_name`: the `tmux` session name
- `workspace_root`: root directory for all `project` entries
- `ros_setup`: optional ROS environment script sourced first
- `conda_env`: optional Conda environment activated first

### `nodes`

Each node entry represents one `tmux` pane:

- `name`: logical node name
- `project`: project directory relative to `workspace_root`
- `command`: a string or a list of strings
- `cpus`: optional, prepend `taskset -c` to the first command
- `autostart`: defaults to `true`

## 3. An example closer to the current code

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

## 4. A few command-resolution details

### Configuration path resolution

`BaseLauncher` first tries:

1. The current working directory
2. Then a path relative to `ros_base/launch/base_launcher.py`

So business repositories can either pass an absolute path directly or place `launch_cfg.yaml` next to their own launcher script.

### `command` can be a list

For example:

```
command:
  - "isaac_ros_container"
  - "source vslam.sh"
  - "launch_vslam"
```

The launcher will send each command to the same pane in sequence.

### `cpus` applies only to the first command

In the current implementation, `taskset -c ...` is added only to the first command. If `command` is a list, later commands do not receive the CPU-pinning prefix again automatically.

## 5. Startup filtering

The command line supports:

```
python ros_base/launch/base_launcher.py launch_cfg.yaml --enable LOW_LEVEL
python ros_base/launch/base_launcher.py launch_cfg.yaml --disable KALMAN
```

The rules are:

- Entries in `disable_nodes` are skipped directly
- Entries in `enable_nodes` are force-enabled
- All other nodes follow `autostart`

## 6. Where to place it

`BaseLauncher` lives in `ros_base`, but it is usually better to wrap it with a thin entry point inside the business repository, for example:

```
SigLoMa-VLM/
└── launch/
    ├── sigloma_launch.py
    └── launch_cfg.yaml
```

That way, team members only need to remember the launch command of the business repository itself.

## 7. Common `tmux` operations

- Detach a session: `Ctrl + B`, then `D`
- Reattach a session: `tmux attach -t sigloma_system`
- Switch panes: `Ctrl + B`, then use the arrow keys

If you already use `tmux`, the main value of this launcher is that it turns environment setup, directory changes, and node startup into configuration instead of repeated manual typing.
