# ROS Base Project

**ROS Base** 是一个专为复杂机器人系统设计的 ROS2 (Python) 应用框架。

它通过引入 **Manager-Node-Agent-Handler** 的分层设计，解决了传统 ROS 开发中“单体节点过大”与“多进程管理松散”之间的矛盾，提供了一套**高内聚、低耦合、支持插件式扩展**的标准化开发范式。

---

## 为什么需要 ROS Base？

在开发涉及任务规划、运动控制、SLAM 和 目标检测的大型机器人系统时，架构设计往往面临两难选择：

### 1. 传统方案的痛点

=== "方案 A: 单体节点 (Big Node)"

    将所有功能（数据订阅、预处理、算法计算、控制发布）写在一个巨大的 Class 中。
    
    *   **:white_check_mark: 优点**: 数据在进程内直接访问，延迟极低。
    *   **:x: 缺点**: 
        *   **耦合严重**: 牵一发而动全身，难以维护。
        *   **测试困难**: 想测试一下“视觉算法”，却必须启动整个“运控系统”。
        *   **无法复用**: 代码与特定项目绑死。

=== "方案 B: 分布式微服务 (Micro-services)"

    将每个功能拆分成独立的 ROS Node 进程。
    
    *   **:white_check_mark: 优点**: 模块物理隔离，解耦彻底。
    *   **:x: 缺点**: 
        *   **启动繁琐**: 需要编写几十行的 Launch 文件或打开多个终端。
        *   **通信开销**: 进程间数据交互必须序列化/反序列化 (Topic)，延迟增加。
        *   **协同复杂**: 节点间的握手、状态同步、参数配置变得异常麻烦。

### 2. ROS Base 的解决方案

**ROS Base 采用了“方案 C”：基于管理器的进程内解耦架构。**

![Architecture](images/framework.png)

我们引入了一个核心概念 —— **BaseManager**：

1.  **依附式运行 (Attached Mode)**: 
    *   所有的子节点 (Nodes) 和 算法模块 (Agents) 都注册到 Manager 中。
    *   它们对外表现为一个整体 ROS Node，对内通过 `self` 属性共享内存数据（解决了通信开销）。
2.  **双模态设计**:
    *   每个定义好的 **BaseNode** 既可以依附在 Manager 里运行，也可以**随时单独作为标准 ROS2 Node 启动**（解决了测试困难）。
3.  **职责分离**:
    *   **Node**: 只管收发数据。
    *   **Agent**: 只管算法计算。
    *   **Handler**: 只管业务逻辑和状态机。
    *   **Manager**: 管好它们所有人的生老病死。

---

## 核心特性

*   **⚡ 高性能**: 支持多进程挂载 (`register_multiprocess_nodes`)，轻松分离 CPU 密集型任务（如相机采集）。
*   **🧩 可复用**: 提供了开箱即用的相机封装 (`CamSubNode`)、可视化模块 (`Overlay`) 和 数学工具库。
*   **🩺 易调试**: 内置 `profile_latency` 装饰器和统一的日志系统，性能瓶颈一目了然。
*   **🤖 广泛验证**: 已在 **HomiQuad-VLM** (大小脑协同) 和 **Quad-Deploy** (RL 运控) 两个实战项目中稳定运行。

## 快速开始

可以通过以下命令安装：

```bash
git clone https://github.com/11chens/ros_base.git
cd ros_base
pip install -e .
```

接下来，请阅读 [**快速上手**](quick-start/installation.md) 指南。
