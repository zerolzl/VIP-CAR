# VIP专用车位违规占用告警系统 — 开发实现计划

## 摘要

基于需求文档，本计划为VIP专用车位违规占用告警系统提供全面的开发实现方案。系统通过定时巡检SQL Server外部数据库中的VIP车位停放信息，与白名单比对后通过短信和Webhook并行告警，并提供完整的Web管理界面。

**技术栈**：Python 3.10+ / FastAPI / SQLAlchemy / APScheduler / MySQL / SQL Server(pyodbc) / Vue 3 + Element Plus / Docker

---

## 一、当前状态分析

- 需求文档已完整定义，包含功能需求、数据库设计、API设计、业务逻辑流程
- 尚未开始任何代码实现
- 需要从零搭建完整项目

---

## 二、项目目录结构

```
vip_parking_alert/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI入口 + lifespan管理
│   │   ├── config.py                  # Pydantic Settings配置管理
│   │   ├── dependencies.py            # 依赖注入（数据库会话等）
│   │   ├── api/                       # 路由层
│   │   │   ├── __init__.py
│   │   │   ├── router.py              # 总路由注册
│   │   │   ├── spots.py               # VIP车位管理
│   │   │   ├── contacts.py            # 通讯录
│   │   │   ├── notify_configs.py      # 通知配置
│   │   │   ├── settings.py            # 系统设置
│   │   │   ├── alerts.py              # 告警日志
│   │   │   └── system.py              # 健康检查/热重载
│   │   ├── models/                    # SQLAlchemy ORM模型
│   │   │   ├── __init__.py
│   │   │   ├── base.py                # Base + TimestampMixin
│   │   │   ├── spot.py                # VipParkingSpot
│   │   │   ├── contact.py             # Contact
│   │   │   ├── notify_config.py       # SpotNotifyConfig
│   │   │   ├── alert_log.py           # AlertLog
│   │   │   ├── external_db.py         # ExternalDbConfig
│   │   │   └── sms_gateway.py         # SmsGatewayConfig
│   │   ├── schemas/                   # Pydantic请求/响应模型
│   │   │   ├── __init__.py
│   │   │   ├── spot.py / contact.py / notify_config.py
│   │   │   ├── alert.py / settings.py / common.py
│   │   ├── services/                  # 业务逻辑层
│   │   │   ├── spot_service.py
│   │   │   ├── contact_service.py
│   │   │   ├── notify_config_service.py
│   │   │   ├── alert_service.py       # 告警发送与抑制核心
│   │   │   ├── patrol_service.py      # 巡检编排
│   │   │   ├── sms_sender.py          # 短信发送
│   │   │   ├── webhook_sender.py      # Webhook发送
│   │   │   └── external_db_service.py # SQL Server查询
│   │   ├── db/
│   │   │   ├── session.py             # MySQL引擎与会话工厂
│   │   │   └── external_engine.py     # SQL Server引擎管理
│   │   ├── scheduler/
│   │   │   ├── setup.py               # 调度器初始化与生命周期
│   │   │   └── jobs.py                # 巡检任务定义
│   │   ├── utils/
│   │   │   ├── crypto.py              # Fernet加解密
│   │   │   └── logging_config.py      # 日志配置
│   │   └── core/
│   │       └── enums.py               # NotifyType等枚举
│   ├── alembic/                       # 数据库迁移
│   ├── tests/                         # 测试
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/                       # Axios封装
│   │   ├── views/                     # 页面（Dashboard/Spots/Contacts/Alerts/Settings）
│   │   ├── components/                # 组件（SpotForm/PlateTagInput/NotifyConfigForm等）
│   │   ├── router/ / stores/
│   │   └── App.vue / main.js
│   ├── vite.config.js / package.json
│   └── Dockerfile
├── docker-compose.yml
├── nginx/default.conf
└── .env.example
```

---

## 三、数据库模型设计要点

### 3.1 基础模型
- `Base(DeclarativeBase)` + `TimestampMixin`（created_at / updated_at）
- 使用SQLAlchemy 2.0的`Mapped`类型注解风格

### 3.2 六张核心表（MySQL库 `vip_parking`）
按需求文档定义：`vip_parking_spots`、`contacts`、`spot_notify_config`、`alert_log`、`external_db_config`、`sms_gateway_config`

### 3.3 额外索引（性能优化）
```sql
CREATE INDEX idx_alert_spot_plate_unresolved ON alert_log(spot_id, plate_number, is_resolved);
CREATE INDEX idx_alert_sent_time ON alert_log(sent_time);
CREATE INDEX idx_notify_spot_enabled ON spot_notify_config(spot_id, enabled);
CREATE INDEX idx_contacts_enabled ON contacts(enabled);
```

### 3.4 数据库迁移
- 使用Alembic管理，首次`alembic revision --autogenerate -m "initial"`

---

## 四、外部SQL Server连接管理

### 4.1 驱动选择：pyodbc
- SQLAlchemy官方推荐的mssql驱动，生态成熟
- Docker中需安装 `unixodbc` + `msodbcsql18`

### 4.2 连接池配置
```python
pyodbc.pooling = False  # 禁用pyodbc内置池，由SQLAlchemy管理
engine = create_engine(
    "mssql+pyodbc://...",
    pool_size=3, max_overflow=2,
    pool_recycle=1800,       # 30分钟回收
    pool_pre_ping=True,      # 使用前ping，自动剔除失效连接
    pool_timeout=10
)
```

### 4.3 引擎生命周期管理
- `ExternalDbEngineManager` 单例，通过配置hash判断是否需要重建
- 配置变更时调用 `dispose()` 销毁旧引擎，下次巡检自动重建
- 查询SQL模板：`SELECT CAR_NO FROM dbo.REG_RECORD WHERE CAM_LOCATION = '{spot_number}'`

---

## 五、APScheduler与FastAPI集成

### 5.1 使用lifespan上下文管理器（替代已弃用的on_event）
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with scheduler_lifespan(app):
        yield
```

### 5.2 调度器配置
- `BackgroundScheduler`，时区 `Asia/Shanghai`
- `coalesce=True`（错过的任务合并执行）
- `max_instances=1`（同一任务最多1个实例，避免堆积）
- `misfire_grace_time=60`

### 5.3 巡检间隔动态调整
- 通过 `POST /api/system/reload-config` 热重载
- 调用 `scheduler.reschedule_job()` 修改间隔

---

## 六、多线程告警发送（线程安全）

### 6.1 并行发送架构
- `ThreadPoolExecutor` 并行调用短信和Webhook通道
- `threading.Lock()` 保护alert_log首次写入
- 每个线程通过 `session_factory()` 创建独立SQLAlchemy Session

### 6.2 告警抑制逻辑
1. 查询 `alert_log` 是否存在 `(spot_id, plate_number, is_resolved=0)`
   - 存在 → 跳过（已告警，抑制中）
2. 不存在 → 并行发送，任一成功写入alert_log，全部失败不写入（下轮重试）
3. 违规解除（白名单内或空位）→ 标记 `is_resolved=1`，可选发送恢复通知

### 6.3 sent_via字段
- 首次成功立即加锁写入alert_log
- 后续成功通道追加到sent_via列表（逗号分隔）

---

## 七、密码加密方案

### 7.1 技术选型：cryptography.fernet.Fernet
- AES-128-CBC + HMAC-SHA256 认证加密
- PBKDF2HMAC从SECRET_KEY派生32字节密钥（480000次迭代）
- 比手动AES实现更安全、更简洁

### 7.2 加解密时机
| 场景 | 操作 |
|------|------|
| API保存配置 | 明文 → encrypt() → 存入数据库 |
| 巡检查询SQL Server | 数据库读取 → decrypt() → 建立连接 |
| API返回配置给前端 | 密文脱敏为 `****`，未修改保留原密文 |
| 测试连接 | 临时解密 → 测试 → 不持久化 |

---

## 八、配置热重载机制

- `config.py` 使用 `pydantic-settings` + `@lru_cache` 缓存
- `POST /api/system/reload-config` 触发：
  1. `get_settings.cache_clear()` 清除缓存
  2. `external_engine_manager.dispose()` 重建SQL Server引擎
  3. `scheduler.reschedule_job()` 调整巡检间隔
  4. `CryptoUtil.reset()` 重置加密实例

---

## 九、前端Vue 3 + Element Plus页面规划

### 9.1 页面列表
| 页面 | 路由 | 功能 |
|------|------|------|
| Dashboard | `/` | 统计卡片、最近告警、系统状态 |
| 车位管理 | `/spots` | 车位CRUD、车牌标签输入、监控开关 |
| 车位详情 | `/spots/:id` | 车位信息 + 通知配置管理 |
| 通讯录 | `/contacts` | 联系人CRUD |
| 告警日志 | `/alerts` | 告警记录查询、筛选、分页 |
| 系统设置 | `/settings` | 外部数据库/短信网关/巡检间隔配置 |

### 9.2 关键组件
- `PlateTagInput`：车牌标签输入（el-tag + el-input，回车添加，可删除）
- `NotifyConfigForm`：通知配置表单（类型切换动态表单，联系人选择器自动填充手机号）
- `AlertFilter`：告警筛选（车位、车牌、时间范围、状态）

---

## 十、Docker部署

### 10.1 后端Dockerfile关键点
- 基础镜像 `python:3.11-slim`
- 安装 `unixodbc` + `msodbcsql18`（pyodbc依赖）
- 利用Docker缓存（先COPY requirements.txt）

### 10.2 前端Dockerfile
- 多阶段构建：`node:18-alpine` 构建 → `nginx:alpine` 运行

### 10.3 docker-compose.yml
- 三个服务：mysql(8.0) + backend + frontend
- MySQL健康检查确保后端等待数据库就绪
- 数据持久化：mysql_data volume

### 10.4 Nginx反向代理
- `/` → 前端静态文件（try_files支持SPA路由）
- `/api/` → proxy_pass到backend:8000

---

## 十一、错误处理与日志策略

### 11.1 日志配置
- 结构化格式：`时间 | 级别 | 模块 | 消息`
- 双输出：控制台 + 按日滚动文件
- 第三方库日志降级（apscheduler/sqlalchemy/urllib3设为WARNING）

### 11.2 巡检异常隔离
- 单个车位巡检异常不影响其他车位（try/except + continue）
- 全局异常处理器返回500 + 记录完整堆栈

---

## 十二、测试策略

### 12.1 测试分层
- **单元测试**：pytest + unittest.mock（加解密、发送器、业务逻辑）
- **集成测试**：httpx TestClient + SQLite内存库（API端到端）
- **外部Mock**：Mock SQL Server查询结果、Mock requests发送

### 12.2 核心测试用例
- 告警服务：全部成功/部分成功/全部失败/抑制逻辑/恢复逻辑
- 发送器：Mock HTTP 200/500/Timeout
- 巡检：白名单内/外/空位/无通知配置
- API：CRUD + 参数验证 + 分页搜索

---

## 十三、实现顺序（分5个阶段）

### 第一阶段：基础框架
1. 项目目录结构搭建
2. config.py 配置管理（pydantic-settings）
3. models/ 全部ORM模型 + base.py
4. db/session.py MySQL会话工厂（scoped_session）
5. utils/crypto.py 加解密工具
6. utils/logging_config.py 日志配置
7. main.py FastAPI应用骨架（lifespan）
8. Alembic初始化与首次迁移

### 第二阶段：CRUD API
9. schemas/ Pydantic请求/响应模型
10. dependencies.py 依赖注入
11. api/spots.py 车位管理CRUD
12. api/contacts.py 通讯录CRUD
13. api/notify_configs.py 通知配置CRUD
14. api/settings.py 系统设置（含测试连接）
15. api/alerts.py 告警日志查询

### 第三阶段：巡检与告警
16. db/external_engine.py SQL Server引擎管理
17. services/external_db_service.py 外部查询
18. services/sms_sender.py 短信发送
19. services/webhook_sender.py Webhook发送
20. services/alert_service.py 告警发送与抑制
21. services/patrol_service.py 巡检编排
22. scheduler/setup.py + jobs.py 调度器集成
23. api/system.py 健康检查与热重载

### 第四阶段：前端
24. Vue 3项目初始化（Vite + Element Plus + Pinia + Vue Router）
25. 路由与布局框架
26. 通讯录管理页面
27. 车位管理页面（含PlateTagInput组件）
28. 车位详情与通知配置页面
29. 告警日志页面
30. 系统设置页面
31. Dashboard仪表盘

### 第五阶段：部署与测试
32. 后端Dockerfile
33. 前端Dockerfile（多阶段构建）
34. docker-compose.yml + Nginx配置
35. .env.example
36. 单元测试编写
37. 集成测试编写

---

## 十四、潜在挑战与应对

| 挑战 | 应对方案 |
|------|----------|
| SQL Server连接不稳定 | pool_pre_ping + pool_recycle=1800 + 异常时dispose重建 |
| 巡检执行时间超过间隔 | max_instances=1 + coalesce=True，避免堆积 |
| 多线程Session竞争 | 每线程独立Session，通过session工厂创建 |
| 大量车位巡检性能 | 当前串行（适用于<100车位），可扩展为异步并发 |
| Docker中ODBC驱动 | Dockerfile显式安装unixodbc + msodbcsql18 |
| 密码安全 | Fernet加密存储，API返回脱敏掩码 |

---

## 十五、验证步骤

1. **数据库验证**：启动MySQL，执行Alembic迁移，确认6张表正确创建
2. **API验证**：使用TestClient测试所有CRUD端点，确认200/422响应
3. **巡检验证**：Mock SQL Server返回违规车牌，确认告警写入alert_log
4. **抑制验证**：连续两次巡检同一违规，确认第二次不重复发送
5. **恢复验证**：Mock SQL Server返回白名单车牌，确认is_resolved=1
6. **发送验证**：Mock HTTP请求，确认短信/Webhook并行发送逻辑正确
7. **前端验证**：浏览器访问各页面，确认CRUD操作正常
8. **部署验证**：docker-compose up，确认三服务正常启动，Nginx代理正确
