# AI Decision Cache

## 概述

AI Cache 功能可以缓存 AI 的交易决策，避免重复调用 API，从而：
- ⚡ **加快测试速度**：重复运行时直接使用缓存
- 💰 **节省 API 成本**：相同市场数据不重复调用
- 🔄 **支持 Replay**：可以重放之前的决策
- 🐛 **便于调试**：可以查看所有历史决策

## 工作原理

### 缓存键 (Cache Key)

缓存键由以下内容生成：
```
SHA256(agent_name | timestamp | prompt)[:16]
```

这确保：
- 相同的市场数据 → 相同的缓存键 → 返回缓存决策
- 不同的市场数据 → 不同的缓存键 → 调用 AI

### 缓存流程

```
1. 构建市场 prompt
2. 计算缓存键
3. 检查缓存:
   - 如果命中 (HIT) → 返回缓存决策 ✅
   - 如果未命中 (MISS) → 调用 AI → 存入缓存 → 返回决策
```

## 使用方法

### 1. 启用缓存

在 `TradingEvaluator` 配置中添加 `ai_cache_file`:

```python
config = {
    "start_date": "2024-11-01",
    "end_date": "2024-11-15",
    "ai_cache_file": "cache/ai_decisions.json",  # ← 启用缓存
    # ... 其他配置
}

evaluator = TradingEvaluator(
    agent_names=["Conservative", "Aggressive"],
    agent_clients=agent_clients,
    config=config
)
```

### 2. 运行回测

第一次运行（缓存为空）：
```bash
$ python3 test_trading_evaluator.py

🗄️  AI Cache enabled: cache/ai_decisions.json
✅ Loaded AI cache: 0 entries

CYCLE 1/3:
  [Conservative] Generating decision...  # 调用 AI
  [Aggressive] Generating decision...    # 调用 AI

CYCLE 2/3:
  [Conservative] Generating decision...  # 调用 AI
  [Aggressive] Generating decision...    # 调用 AI

📊 AI Cache Statistics:
   Entries: 6
   Hits: 0 | Misses: 6
   Hit Rate: 0.0%
```

第二次运行（使用缓存）：
```bash
$ python3 test_trading_evaluator.py

🗄️  AI Cache enabled: cache/ai_decisions.json
✅ Loaded AI cache: 6 entries

CYCLE 1/3:
  💾 [Cache HIT] Conservative at 2024-11-01 00:00:00+00:00
  💾 [Cache HIT] Aggressive at 2024-11-01 00:00:00+00:00

CYCLE 2/3:
  💾 [Cache HIT] Conservative at 2024-11-01 04:00:00+00:00
  💾 [Cache HIT] Aggressive at 2024-11-01 04:00:00+00:00

📊 AI Cache Statistics:
   Entries: 6
   Hits: 6 | Misses: 0
   Hit Rate: 100.0%  # 🎉 全部命中！
```

### 3. 清理缓存

如果你想重新生成决策（例如修改了 prompt）：

```python
# 方法1：删除缓存文件
import os
os.remove("cache/ai_decisions.json")

# 方法2：使用 API
evaluator.ai_cache.clear()

# 方法3：命令行
rm cache/ai_decisions.json
```

## 缓存文件格式

缓存存储为 JSON 文件：

```json
{
  "abc123def456": {
    "agent_name": "Conservative",
    "timestamp": "2024-11-01 00:00:00+00:00",
    "summary": "Hold position due to unclear signals",
    "reasoning": "Market shows mixed signals...",
    "actions": [
      {
        "symbol": "BTCUSDT",
        "action": "hold",
        "leverage": 1,
        "quantity": 0
      }
    ],
    "cached_at": "2024-12-17T10:30:00"
  }
}
```

## 高级用法

### 共享缓存

多个测试可以共享同一个缓存：

```python
# 测试 A
config_a = {
    "ai_cache_file": "shared_cache.json",
    "total_decision_cycles": 10,
}

# 测试 B (共享相同缓存)
config_b = {
    "ai_cache_file": "shared_cache.json",  # 同一个文件
    "total_decision_cycles": 20,
}
```

### 只读模式 (Replay)

如果你想强制只使用缓存（不调用 AI）：

```python
# 在 ai_cache.py 中添加 replay_only 参数
# 或者检查缓存命中率来验证
```

## 最佳实践

1. **开发阶段**：
   - ✅ 启用缓存
   - ✅ 使用小数据集（3-5 cycles）
   - ✅ 快速迭代测试

2. **正式回测**：
   - ✅ 清空缓存
   - ✅ 完整运行
   - ✅ 保存缓存供后续分析

3. **调试**：
   - 📝 检查 `cache/ai_decisions.json`
   - 🔍 查看具体决策内容
   - 🐛 定位问题

## 与 nofx 的对比

| 特性 | nofx | 你的项目 |
|------|------|----------|
| 缓存键算法 | Custom | SHA256 |
| 存储格式 | JSON | JSON |
| Replay 模式 | ✅ | ⚠️ 待添加 |
| 缓存统计 | ✅ | ✅ |
| 自动保存 | ✅ | ✅ |

## 注意事项

⚠️ **缓存失效情况**：
- 修改了 prompt 模板
- 修改了技术指标计算
- 修改了代理策略

在这些情况下，请清空缓存重新生成。

🎯 **最佳实践**：
- 定期清理旧缓存
- 为不同实验使用不同缓存文件
- 保留重要回测的缓存作为参考

