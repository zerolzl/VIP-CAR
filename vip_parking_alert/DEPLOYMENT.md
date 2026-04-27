# VIP车位告警系统 - 非Docker部署指南

## 环境要求

### Python 后端
- Python >= 3.10
- 依赖库见 `backend/requirements.txt`

### Node.js 前端
- Node.js >= 18
- npm >= 9

### MySQL 数据库
- MySQL >= 8.0

## 快速开始

### 1. 准备 MySQL 数据库

```bash
# 登录MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE vip_parking CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 创建用户（可选）
CREATE USER 'vip_parking'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON vip_parking.* TO 'vip_parking'@'localhost';
FLUSH PRIVILEGES;
```

### 2. 配置数据库连接

编辑 `backend/.env` 文件，修改 MySQL 连接信息：

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=vip_parking
```

### 3. 启动所有服务

双击运行 `start_all.bat`，或执行命令：

```bash
start_all.bat
```

这将自动启动：
- 后端服务: http://localhost:8000
- 前端页面: http://localhost:3000

### 4. 初始化数据库

首次启动时，系统会自动创建数据库表结构。

### 单独启动服务

**启动后端：**
```bash
start_backend.bat
```

**启动前端：**
```bash
start_frontend.bat
```

## 手动部署步骤

### 后端部署

```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
# 编辑 .env 文件，设置MySQL连接信息

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 前端部署

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 配置说明

### 数据库配置

系统默认使用 MySQL 数据库。

`.env` 配置示例：

```env
# MySQL数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=vip_parking
```

### 安全密钥

系统需要一个安全密钥用于密码加密，至少32个字符。

生成方式：
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

将生成的密钥替换 `.env` 中的 `SECRET_KEY`。

## 访问地址

| 服务 | 地址 |
|-----|------|
| 前端页面 | http://localhost:3000 |
| 后端API | http://localhost:8000 |
| API文档 | http://localhost:8000/docs |
| 健康检查 | http://localhost:8000/api/system/health |

## 目录结构

```
vip_parking_alert/
├── backend/              # 后端服务
│   ├── app/              # 应用代码
│   ├── logs/             # 日志文件
│   ├── .env              # 环境配置
│   └── requirements.txt  # Python依赖
├── frontend/             # 前端页面
│   ├── src/              # 源代码
│   └── package.json      # Node依赖
├── start_all.bat         # 启动所有服务
├── start_backend.bat     # 启动后端服务
├── start_frontend.bat    # 启动前端服务
└── DEPLOYMENT.md         # 部署说明
```

## 生产环境部署建议

### 后端

使用 Gunicorn 作为生产服务器：

```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

### 前端

构建生产版本并使用 Nginx 托管：

```bash
cd frontend
npm run build
```

### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 故障排查

### 端口占用

如果端口被占用，可以修改 `backend/.env` 中的 `APP_PORT`。

### 依赖安装失败

确保 Python 和 Node.js 版本符合要求。

### 数据库连接失败

检查 `.env` 中的数据库配置是否正确。

## 日志查看

后端日志位于 `backend/logs/` 目录。
