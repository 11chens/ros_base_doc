# 基类编排启动系统 (Base Launcher System)

该系统是以 `BaseLauncher` 为核心的通用进程编排工具，旨在为复杂机器人项目提供跨工程、多环境、高性能的启动方案。

## 1. 核心设计原理

### 1.1 配置与逻辑解耦
系统将“如何启动”的通用逻辑封装在 `base_launcher.py` 中，而将“启动什么”的项目细节定义在特定的 `yaml` 配置文件中。这种架构允许开发者在不修改核心代码的情况下，通过增加配置文件快速适配新项目。

### 1.2 层级命令链 (Command Chaining)
启动器的核心竞争力在于其构建的复杂命令链。每个节点在 TMUX 窗口中执行的指令经历了四个关键阶段：

1.  **资源隔离阶段**：通过 `taskset -c <cpus>` 锁定内核，防止进程间的 CPU 争抢。
2.  **环境初始化阶段**：链式执行 `source ros` 和 `conda activate`，解决多版本、多环境依赖冲突。
3.  **上下文定位阶段**：自动 `cd` 进入节点所在的子工程目录，解决路径依赖问题。
4.  **执行与挂起阶段**：执行节点指令，并在结束处添加 `read -n 1; bash`。这确保了当节点崩溃时程序不会自动关闭窗口，方便开发者查看错误栈并直接在该窗口进行交互式调试。

## 2. 核心代码解析 (`base_launcher.py`)

### 2.1 `BaseLauncher` 类职责
*   **`__init__`**: 负责加载 YAML 并校验环境字段（`workspace_root`, `conda_env` 等）的完整性。
*   **`_get_core_command`**: 这是系统的“灵魂”方法。它负责将配置信息组装成一个能够在原生 bash 中运行的复合字符串。特别使用了 `bash -ic` 以确保交互式 shell 特性（如 `.bashrc` 中的别名）在管道执行中依然有效。
*   **`launch`**: 驱动程序。它负责调用 `subprocess` 接口，根据节点索引依次执行 `tmux new-session` (创建会话) 和 `tmux new-window` (扩展窗口)。

### 2.2 异常处理机制
系统在启动序列前会执行 `tmux kill-session`，这能彻底清理上一次运行残留的僵尸进程，保证每次启动都是“冷启动”，减少资源死锁的概率。

## 3. 目录与组织结构

```text
ros_base/ros_base/
├── launch/
│   ├── base_launcher.py         # 核心启动引擎 (通用)
│   ├── homi/                    # 项目配置子目录
│   │   └── launch_cfg.yaml      # Homi 项目专属定义
│   └── project_new/
│       └── launch_cfg.yaml      # 新项目扩展示例
└── docs/
    └── launcher_system.md       # 本技术文档
```

## 4. 使用维护指南

### 4.1 配置文件规范
在 YAML 的 `nodes` 列表中，每一个条目代表一个 TMUX 窗口：
*   `cpus`: 推荐对 SDK 和对实时性敏感的算法节点（如 Kalman）使用独立的单核或核组。
*   `command`: 完整的启动命令（如 `python test.py --arg1`）。

### 4.2 运行指令

在核心目录下运行：

```bash
cd ~/Project/ros_base/ros_base/launch
python3 base_launcher.py homi/launch_cfg.yaml
```

### 4.3 常用交互操作 (TMUX)
*   **后台挂起**: `Ctrl + B` -> `D`。
*   **恢复监控**: `tmux attach -t base_nodes`。
*   **切换窗口**: `Ctrl + B` -> `[数字键]` 快速切换不同节点的日志窗口。
