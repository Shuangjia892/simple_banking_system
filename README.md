# Simple Banking System (Python)

一个轻量的命令行银行系统示例，聚焦于账户管理、转账和 CSV 持久化。  
本项目在保持简洁的前提下，加入了更贴近真实资金系统的基础保障：金额精度、原子转账、输入校验和更健壮的数据加载。

## 功能特性

- 创建账户（账户名唯一，初始余额不可为负）
- 存款、取款（金额必须为正数，不允许透支）
- 账户间转账（单次转账具备原子性语义）
- 使用 CSV 保存/加载账户数据
- 支持交易流水记录与导出（`transactions.csv`）
- 金额使用 `Decimal`，统一保留两位小数
- 内置单元测试，覆盖核心流程和常见异常场景

## 设计约束与一致性规则

- **金额精度**：所有金额转换为 `Decimal`，并按两位小数（`ROUND_HALF_UP`）处理。
- **转账一致性**：转账时对双方账户加锁，避免并发下的部分更新和竞态。
- **输入校验**：账户名必须是非空字符串；金额必须是合法数值且满足业务约束。
- **加载事务性**：CSV 导入先完整校验，再一次性替换内存状态；中途失败不会污染已有数据。
- **安全落盘**：保存 CSV 时先写临时文件并 `os.replace` 原子替换，降低文件损坏风险。

## 项目结构

```text
simple_banking_system/
├── banking_system.py        # 核心领域逻辑（账户、异常、持久化）
├── main.py                  # 交互式 CLI
├── data.csv                 # 账户数据文件
├── transactions.csv         # 交易流水文件（运行后生成）
├── test_banking_system.py   # 单元测试
└── README.md                # 项目说明
```

## 快速开始

### 1) 运行示例

```bash
python3 main.py
```

启动后可在菜单中执行：

- 创建账户
- 存款/取款
- 转账
- 查看余额
- 查看最近交易流水
- 保存并退出（会写入 `data.csv` 和 `transactions.csv`）

### 2) 运行测试

```bash
python3 -m unittest -v
```

## CSV 数据格式

CSV 必须包含以下列名：

```csv
name,balance
Alice,1000.00
Bob,500.00
```

约束说明：

- `name` 不可为空，且文件内不可重复。
- `balance` 必须是合法金额，且不可为负数。

## 交易流水格式（transactions.csv）

示例字段：

- `timestamp`：UTC 时间戳
- `type`：交易类型（`CREATE_ACCOUNT`、`DEPOSIT`、`WITHDRAW`、`TRANSFER`）
- `amount`：交易金额
- `source_account` / `target_account`：来源/目标账户
- `before_balance_source` / `after_balance_source`：来源账户交易前后余额
- `before_balance_target` / `after_balance_target`：目标账户交易前后余额
- `status`：交易状态（当前为 `SUCCESS`）
- `message`：补充信息

## 主要异常类型

- `DuplicateAccountError`：账户已存在
- `AccountNotFoundError`：账户不存在
- `InvalidAmountError`：金额非法（非数字、非正数、负初始余额等）
- `InsufficientFundsError`：余额不足
- `InvalidAccountNameError`：账户名非法
- `DataFormatError`：CSV 结构或读取过程异常

## 后续可扩展方向

- 增加交易流水与审计日志（交易 ID、前后余额、操作结果）
- 引入数据库事务（替代 CSV）以支持多进程/多实例
- 增加接口层（REST API / CLI 参数化）与更完整的集成测试


