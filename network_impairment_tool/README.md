# 网络损伤模拟工具 (Network Impairment Tool)

本工具用于在 Linux 主机上模拟复杂/波动的生产环境网络场景。通过 Python 脚本自动化调用 `tc/netem`，实现随机的延迟、抖动、丢包组合。

## 1. 推荐架构：透明桥接 (Transparent Bridge)

为了使损伤主机对测试链路透明，建议将两块物理网口桥接：

```bash
# 假设网口名为 eth1 和 eth2
sudo ip link add br0 type bridge
sudo ip link set eth1 master br0
sudo ip link set eth2 master br0
sudo ip link set eth1 up
sudo ip link set eth2 up
sudo ip link set br0 up
```

> [!IMPORTANT]
> **网络隔离风险提示**：请确保损伤的网口（或桥接网口）**不是**您当前 SSH 连接的管理网口。如果损伤配置过于严重，可能会导致您与 Linux 主机失联。
> **建议方案**：再额外配置一个独立的管理网口，或者在启动前确认管理流量不经过损伤路径。

这样，通过 `eth1` 进入的数据包将通过 `br0` 从 `eth2` 出去，反之亦然。我们的脚本将作用于 `br0` 接口。

## 2. 快速开始

### 依赖
- Linux 系统 (支持 `iproute2` 和 `tc`)
- Python 3.6+
- root 权限 (sudo)

### 运行脚本
执行脚本并指定要损伤的接口（如桥接网口 `br0`）：

```bash
sudo python3 random_impairment.py br0
```

### 停止损伤
按下 `Ctrl + C`，脚本会自动捕获信号并执行 `tc qdisc del` 清理操作，恢复网络正常。

## 3. 配置说明
您可以直接修改 `random_impairment.py` 顶部的 `DEFAULT_CONFIG` 字典来调整随机范围：

- `delay_ms`: 延迟波动范围 (min, max)。
- `jitter_ms`: 延迟抖动范围。注意脚本会自动修正 `jitter < delay`，以保证网络仿真的一致性。
- `loss_percent`: 丢包百分比范围。
- `interval_sec`: 规则随机切换的时间间隔（秒）。

## 4. 测试与质量保障 (Testing & QA)

本工具内置了完善的自动化单元测试 (UT)，确保核心逻辑（如随机参数修正、Ctrl+C 自动清理、权限拦截等）在不同环境下的一致性。

### 运行单元测试
1. **创建并激活虚拟环境**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install pytest
   ```
2. **执行测试**:
   ```bash
   pytest tests/test_random_impairment.py
   ```

### 测试全景 (P1-P5)
详细的测试策略与 P1-P5 维度矩阵请参阅 `docs/test_strategy_draft.md`。

## 5. 常见问题
- **Q: 为什么提示命令执行失败？**
  - A: 请确保使用了 `sudo`。如果是第一次在接口上运行，脚本会自动尝试初始化。
- **Q: 我该如何查看当前的损伤规则？**
  - A: 运行 `tc qdisc show dev br0` 即可实时查看内核中的 netem 配置。
