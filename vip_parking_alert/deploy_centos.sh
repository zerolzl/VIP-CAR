#!/bin/bash
# VIP车位告警系统 - CentOS 一键部署脚�?# 使用前请确保�?root 用户运行
# 本脚本使�?MySQL 数据库，不使�?SQLite

set -e

# 配置参数
APP_NAME="vip-parking-alert"
APP_DIR="/opt/${APP_NAME}"
PYTHON_VERSION="3.10"
NODE_VERSION="18"
MYSQL_USER="vip_parking"
MYSQL_DATABASE="vip_parking"
MYSQL_PASSWORD=$(openssl rand -hex 16)
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info() {
    echo -e "${GREEN}[INFO] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

# 检查是否为 root 用户
check_root() {
    if [ "$(id -u)" != "0" ]; then
        error "请以 root 用户运行此脚�?
    fi
}

# 检�?CentOS 版本
check_centos() {
    if [ -f /etc/centos-release ]; then
        CENTOS_VERSION=$(cat /etc/centos-release | grep -o '[0-9]\+' | head -n1)
        info "检测到 CentOS ${CENTOS_VERSION}"
        if [ "$CENTOS_VERSION" -lt 7 ]; then
            error "This script only supports CentOS 7 or later"
        fi
    else
        error "未检测到 CentOS 系统"
    fi
}

# 安装系统依赖
install_system_deps() {
    info "安装系统依赖..."
    
    # 更新系统
    info "更新系统软件�?.."
    yum update -y
    
    # 安装 EPEL
    info "安装 EPEL �?.."
    yum install -y epel-release
    
    # 安装基础工具
    info "安装基础工具..."
    yum install -y wget git gcc python${PYTHON_VERSION} python${PYTHON_VERSION}-devel \
        python${PYTHON_VERSION}-pip openssl-devel
    
    # 安装 MySQL 8.0
    info "安装 MySQL 8.0..."
    if ! rpm -qa | grep -q mysql-community-server; then
        wget https://dev.mysql.com/get/mysql80-community-release-el7-3.noarch.rpm -P /tmp/
        rpm -ivh /tmp/mysql80-community-release-el7-3.noarch.rpm
        yum install -y mysql-community-server
    else
        info "MySQL 已安�?
    fi
}

# 安装 Node.js
install_nodejs() {
    info "安装 Node.js ${NODE_VERSION}..."
    
    if ! command -v node &> /dev/null; then
        curl -fsSL https://rpm.nodesource.com/setup_${NODE_VERSION}.x | bash -
        yum install -y nodejs
    else
        info "Node.js 已安�?
    fi
    
    # 更新 npm
    npm install -g npm@9
}

# 配置 MySQL
configure_mysql() {
    info "配置 MySQL 数据�?.."
    
    # 启动 MySQL 服务
    info "启动 MySQL 服务..."
    systemctl enable mysqld
    systemctl start mysqld
    
    # 等待 MySQL 启动
    info "等待 MySQL 初始�?.."
    for i in {1..30}; do
        if systemctl is-active --quiet mysqld; then
            break
        fi
        sleep 1
    done
    
    # 获取初始密码
    info "获取 MySQL 初始密码..."
    INITIAL_PASSWORD=$(grep 'temporary password' /var/log/mysqld.log | awk '{print $NF}')
    
    if [ -z "$INITIAL_PASSWORD" ]; then
        error "无法获取 MySQL 初始密码"
    fi

    info "配置数据库用户和权限..."
    MYSQL_SQL="ALTER USER 'root'@'localhost' IDENTIFIED BY '${MYSQL_PASSWORD}';
CREATE DATABASE IF NOT EXISTS ${MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${MYSQL_USER}'@'localhost' IDENTIFIED BY '${MYSQL_PASSWORD}';
GRANT ALL PRIVILEGES ON ${MYSQL_DATABASE}.* TO '${MYSQL_USER}'@'localhost';
FLUSH PRIVILEGES;"
    
    if ! mysql -u root -p"${INITIAL_PASSWORD}" --connect-expired-password -e "${MYSQL_SQL}" 2>/dev/null; then
        warn "第一次连接失败，重试..."
        sleep 3
        mysql -u root -p"${INITIAL_PASSWORD}" --connect-expired-password -e "${MYSQL_SQL}"
    fi
    
    success "MySQL 配置完成"
}

# 配置防火�?configure_firewall() {
    info "配置防火�?.."
    
    if systemctl is-active --quiet firewalld; then
        # 开�?HTTP 端口
        firewall-cmd --zone=public --add-port=80/tcp --permanent
        firewall-cmd --zone=public --add-port=8000/tcp --permanent
        firewall-cmd --reload
        success "防火墙配置完�?
    else
        warn "firewalld 未运行，跳过防火墙配�?
    fi
}

# 配置 SELinux
configure_selinux() {
    info "配置 SELinux..."
    
    SELINUX_STATUS=$(getenforce)
    if [ "$SELINUX_STATUS" = "Enforcing" ]; then
        # 允许 Nginx 连接到后�?        setsebool -P httpd_can_network_connect 1
        success "SELinux 配置完成"
    else
        warn "SELinux 未启用或已禁�?
    fi
}

# 创建项目目录
create_app_dir() {
    info "创建项目目录..."
    mkdir -p ${APP_DIR}
    mkdir -p ${APP_DIR}/backend/logs
    mkdir -p ${APP_DIR}/frontend
}

# 复制项目文件
copy_app_files() {
    info "复制项目文件..."
    
    # 复制后端代码
    if [ -d "vip_parking_alert/backend" ]; then
        cp -r vip_parking_alert/backend/* ${APP_DIR}/backend/
    elif [ -d "../backend" ]; then
        cp -r ../backend/* ${APP_DIR}/backend/
    else
        error "未找到后端代码目�?
    fi
    
    # 复制前端代码
    if [ -d "vip_parking_alert/frontend" ]; then
        cp -r vip_parking_alert/frontend/* ${APP_DIR}/frontend/
    elif [ -d "../frontend" ]; then
        cp -r ../frontend/* ${APP_DIR}/frontend/
    else
        error "未找到前端代码目�?
    fi
    
    success "项目文件复制完成"
}

# 安装 Python 依赖
install_python_deps() {
    info "安装 Python 依赖..."
    cd ${APP_DIR}/backend
    
    # 升级 pip
    python${PYTHON_VERSION} -m pip install --upgrade pip
    
    # 安装依赖
    pip${PYTHON_VERSION} install -r requirements.txt
    
    success "Python 依赖安装完成"
}

# 安装 Node.js 依赖并构�?install_node_deps() {
    info "安装 Node.js 依赖..."
    cd ${APP_DIR}/frontend
    
    # 安装依赖
    npm install --production
    
    # 构建生产版本
    info "构建前端项目..."
    npm run build
    
    success "Node.js 依赖安装完成"
}

# 配置环境变量
configure_env() {
    info "配置环境变量..."
    cat > ${APP_DIR}/backend/.env <<EOF
# VIP专用车位告警系统 - CentOS 部署配置
# 数据库配�?- 使用 MySQL
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=${MYSQL_USER}
MYSQL_PASSWORD=${MYSQL_PASSWORD}
MYSQL_DATABASE=${MYSQL_DATABASE}

# 安全密钥
SECRET_KEY=${SECRET_KEY}

# 巡检间隔（秒�?PATROL_INTERVAL_SECONDS=30

# 应用配置
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO
EOF
    success "环境变量配置完成"
}

# 初始化数据库�?init_database() {
    info "初始化数据库�?.."
    cd ${APP_DIR}/backend
    
    # 创建数据库表
    python${PYTHON_VERSION} -c "
from app.db.session import engine
from app.models.base import Base
Base.metadata.create_all(bind=engine)
print('数据库表创建成功')
"
    
    success "数据库表初始化完�?
}

# 创建后端服务
create_backend_service() {
    info "创建后端服务..."
    cat > /etc/systemd/system/vip-parking-backend.service <<EOF
[Unit]
Description=VIP Parking Alert Backend Service
After=network.target mysqld.service
Wants=mysqld.service

[Service]
Type=simple
User=root
WorkingDirectory=${APP_DIR}/backend
Environment=PYTHONPATH=${APP_DIR}/backend
ExecStart=/usr/bin/python${PYTHON_VERSION} -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
TimeoutStopSec=10

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable vip-parking-backend
    
    success "后端服务创建完成"
}

# 创建前端服务（使�?Nginx�?create_frontend_service() {
    info "安装并配�?Nginx..."
    
    # 安装 Nginx
    if ! command -v nginx &> /dev/null; then
        yum install -y nginx
    else
        info "Nginx 已安�?
    fi
    
    # 创建配置文件
    cat > /etc/nginx/conf.d/vip-parking.conf <<EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    # 前端静态文�?    location / {
        root ${APP_DIR}/frontend/dist;
        try_files \$uri \$uri/ /index.html;
        expires 1d;
        add_header Cache-Control "public, max-age=86400";
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # API 文档
    location /docs {
        proxy_pass http://localhost:8000/docs;
    }

    location /redoc {
        proxy_pass http://localhost:8000/redoc;
    }

    # 健康检�?    location /api/system/health {
        proxy_pass http://localhost:8000/api/system/health;
        access_log off;
    }
}
EOF

    # 备份默认配置
    if [ -f /etc/nginx/conf.d/default.conf ]; then
        mv /etc/nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf.bak
    fi

    systemctl enable nginx
    
    success "Nginx 配置完成"
}

# 启动服务
start_services() {
    info "启动后端服务..."
    systemctl start vip-parking-backend
    
    # 等待后端服务启动
    info "等待后端服务启动..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/api/system/health &> /dev/null; then
            success "后端服务启动成功"
            break
        fi
        sleep 1
        if [ $i -eq 30 ]; then
            error "后端服务启动超时"
        fi
    done
    
    info "启动 Nginx 服务..."
    systemctl restart nginx
    
    success "所有服务启动完�?
}

# 验证部署
verify_deployment() {
    info "验证部署..."
    
    # 检查后端服�?    if ! systemctl is-active --quiet vip-parking-backend; then
        error "后端服务未启�?
    fi
    
    # 检�?Nginx 服务
    if ! systemctl is-active --quiet nginx; then
        error "Nginx 服务未启�?
    fi
    
    # 检�?API 健康状�?    if ! curl -s http://localhost:8000/api/system/health | grep -q "success"; then
        error "API 健康检查失�?
    fi
    
    success "部署验证通过"
}

# 显示部署信息
show_info() {
    echo ""
    echo -e "${GREEN}=================================="
    echo "  VIP车位告警系统部署完成!"
    echo "==================================${NC}"
    echo ""
    info "访问地址:"
    info "  前端页面: http://$(hostname -I | awk '{print $1}')"
    info "  后端API:  http://$(hostname -I | awk '{print $1}'):8000"
    info "  API文档:  http://$(hostname -I | awk '{print $1}'):8000/docs"
    echo ""
    info "配置信息:"
    info "  数据库名: ${MYSQL_DATABASE}"
    info "  数据库用�? ${MYSQL_USER}"
    info "  数据库密�? ${MYSQL_PASSWORD}"
    info "  安全密钥: ${SECRET_KEY}"
    echo ""
    info "服务管理:"
    info "  后端服务: systemctl [start|stop|restart|status] vip-parking-backend"
    info "  Nginx服务: systemctl [start|stop|restart|status] nginx"
    info "  MySQL服务: systemctl [start|stop|restart|status] mysqld"
    echo ""
    info "日志位置:"
    info "  后端日志: ${APP_DIR}/backend/logs/"
    info "  Nginx日志: /var/log/nginx/"
    info "  MySQL日志: /var/log/mysqld.log"
    echo ""
    info "配置文件:"
    info "  后端配置: ${APP_DIR}/backend/.env"
    info "  Nginx配置: /etc/nginx/conf.d/vip-parking.conf"
    echo ""
}

# 主函�?main() {
    echo -e "${GREEN}=================================="
    echo "  VIP车位告警系统 - CentOS部署脚本"
    echo "  数据�? MySQL 8.0"
    echo "==================================${NC}"
    echo ""
    
    # 前置检�?    check_root
    check_centos
    
    # 安装依赖
    install_system_deps
    install_nodejs
    
    # 配置数据�?    configure_mysql
    
    # 配置系统
    configure_firewall
    configure_selinux
    
    # 部署应用
    create_app_dir
    copy_app_files
    install_python_deps
    install_node_deps
    configure_env
    
    # 初始化数据库
    init_database
    
    # 创建服务
    create_backend_service
    create_frontend_service
    
    # 启动服务
    start_services
    
    # 验证部署
    verify_deployment
    
    # 显示信息
    show_info
}

# Execute main function
main "$@"
