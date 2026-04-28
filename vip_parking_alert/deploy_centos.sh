#!/bin/bash
# VIP Parking Alert System - CentOS Deployment Script
# Please run as root user
# This script uses MySQL database, not SQLite

set -e

APP_NAME="vip-parking-alert"
APP_DIR="/opt/${APP_NAME}"
PYTHON_VERSION="3.10"
NODE_VERSION="16"
MYSQL_USER="vip_parking"
MYSQL_DATABASE="vip_parking"
MYSQL_PASSWORD="?jsh;olg"
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

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

check_root() {
    if [ "$(id -u)" != "0" ]; then
        error "Please run this script as root user"
    fi
}

check_centos() {
    if [ -f /etc/centos-release ]; then
        CENTOS_VERSION=$(cat /etc/centos-release | grep -o '[0-9]\+' | head -n1)
        info "Detected CentOS ${CENTOS_VERSION}"
        if [ "$CENTOS_VERSION" -lt 7 ]; then
            error "This script only supports CentOS 7 or later"
        fi
    else
        error "CentOS not detected"
    fi
}

install_system_deps() {
    info "Installing system dependencies..."
    
    info "Disabling problematic repositories..."
    if [ -f /etc/yum.repos.d/CentOS-SCLo-scl-rh.repo ]; then
        sed -i 's/enabled=1/enabled=0/g' /etc/yum.repos.d/CentOS-SCLo-scl-rh.repo
        info "Disabled CentOS-SCLo-scl-rh repo"
    fi
    if [ -f /etc/yum.repos.d/CentOS-SCLo-scl.repo ]; then
        sed -i 's/enabled=1/enabled=0/g' /etc/yum.repos.d/CentOS-SCLo-scl.repo
        info "Disabled CentOS-SCLo-scl repo"
    fi
    
    info "Updating system packages..."
    yum update -y --skip-broken || yum update -y 2>/dev/null || true
    
    info "Installing EPEL repository..."
    yum install -y epel-release --skip-broken
    
    info "Installing basic tools..."
    yum install -y wget git gcc openssl-devel zlib-devel bzip2-devel readline-devel \
        sqlite-devel xz-devel tk-devel gdbm-devel ncurses-devel libffi-devel openssl --skip-broken
    
    info "Checking OpenSSL..."
    if ! openssl version &> /dev/null; then
        error "OpenSSL not found"
    fi
    OPENSSL_DIR=$(dirname $(dirname $(which openssl)))
    info "OpenSSL found at: ${OPENSSL_DIR}"
    
    info "Installing Python ${PYTHON_VERSION}..."
    if ! command -v python${PYTHON_VERSION} &> /dev/null; then
        PYTHON_FULL_VERSION="${PYTHON_VERSION}.14"
        PYTHON_TGZ="/tmp/Python-${PYTHON_FULL_VERSION}.tgz"
        
        MIRRORS=(
            "https://www.python.org/ftp/python/${PYTHON_FULL_VERSION}/Python-${PYTHON_FULL_VERSION}.tgz"
            "https://mirrors.aliyun.com/python/${PYTHON_FULL_VERSION}/Python-${PYTHON_FULL_VERSION}.tgz"
            "https://mirror.bit.edu.cn/python/${PYTHON_FULL_VERSION}/Python-${PYTHON_FULL_VERSION}.tgz"
            "https://mirrors.nju.edu.cn/python/${PYTHON_FULL_VERSION}/Python-${PYTHON_FULL_VERSION}.tgz"
            "https://mirror.hust.edu.cn/python/${PYTHON_FULL_VERSION}/Python-${PYTHON_FULL_VERSION}.tgz"
        )
        
        info "Trying to download Python ${PYTHON_FULL_VERSION}..."
        DOWNLOAD_SUCCESS=false
        for mirror in "${MIRRORS[@]}"; do
            info "Trying: ${mirror}"
            if wget -q "${mirror}" -O "${PYTHON_TGZ}" 2>/dev/null; then
                info "Download succeeded from ${mirror}"
                DOWNLOAD_SUCCESS=true
                break
            fi
        done
        
        if [ "$DOWNLOAD_SUCCESS" = true ]; then
            info "Extracting Python source..."
            tar -xzf "${PYTHON_TGZ}" -C /tmp/
            
            info "Configuring Python build with OpenSSL..."
            cd "/tmp/Python-${PYTHON_FULL_VERSION}"
            ./configure --prefix=/usr/local --with-system-ffi --with-openssl="${OPENSSL_DIR}"
            
            info "Compiling Python..."
            make -j$(nproc)
            
            info "Installing Python..."
            make altinstall
            
            info "Cleaning up..."
            rm -rf "/tmp/Python-${PYTHON_FULL_VERSION}"*
            
            info "Installing pip..."
            /usr/local/bin/python${PYTHON_VERSION} -m ensurepip --upgrade
            
            info "Python ${PYTHON_FULL_VERSION} installed successfully"
        else
            error "Failed to download Python ${PYTHON_FULL_VERSION} from all mirrors"
        fi
    else
        info "Python ${PYTHON_VERSION} already installed"
    fi
    
    info "Installing MySQL 8.0..."
    if ! rpm -qa | grep -q mysql-community-server; then
        info "Cleaning up existing MySQL repo files..."
        yum remove -y mysql*-community-release 2>/dev/null || true
        rm -rf /etc/yum.repos.d/mysql*-community.repo 2>/dev/null || true
        
        wget https://dev.mysql.com/get/mysql80-community-release-el7-3.noarch.rpm -P /tmp/
        
        info "Installing MySQL repo with GPG check disabled..."
        rpm -ivh --nosignature /tmp/mysql80-community-release-el7-3.noarch.rpm
        
        info "Disabling GPG check for MySQL packages..."
        sed -i 's/gpgcheck=1/gpgcheck=0/g' /etc/yum.repos.d/mysql*-community.repo
        
        yum install -y mysql-community-server --skip-broken
    else
        info "MySQL already installed"
    fi
}

install_nodejs() {
    info "Installing Node.js ${NODE_VERSION}..."
    
    if ! command -v node &> /dev/null; then
        curl -fsSL https://rpm.nodesource.com/setup_${NODE_VERSION}.x | bash -
        yum install -y nodejs
    else
        info "Node.js already installed"
    fi
    
    npm install -g npm@9
}

configure_mysql() {
    info "Configuring MySQL database..."
    
    info "Starting MySQL service..."
    systemctl enable mysqld
    systemctl start mysqld
    
    info "Waiting for MySQL initialization..."
    for i in {1..60}; do
        if systemctl is-active --quiet mysqld; then
            break
        fi
        sleep 1
    done
    
    info "Waiting for MySQL to be fully ready..."
    sleep 15
    
    info "Getting MySQL initial password..."
    INITIAL_PASSWORD=$(grep 'temporary password' /var/log/mysqld.log | awk '{print $NF}')
    
    if [ -n "$INITIAL_PASSWORD" ]; then
        info "Found temporary password: ${INITIAL_PASSWORD:0:8}..."
    else
        warn "No temporary password found in mysqld.log"
    fi
    
    MYSQL_SQL="ALTER USER 'root'@'localhost' IDENTIFIED BY '${MYSQL_PASSWORD}';
CREATE DATABASE IF NOT EXISTS ${MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${MYSQL_USER}'@'localhost' IDENTIFIED BY '${MYSQL_PASSWORD}';
GRANT ALL PRIVILEGES ON ${MYSQL_DATABASE}.* TO '${MYSQL_USER}'@'localhost';
FLUSH PRIVILEGES;"
    
    info "Configuring database user and privileges..."
    
    if [ -n "$INITIAL_PASSWORD" ]; then
        info "Trying connection with temporary password..."
        if mysql -u root -p"${INITIAL_PASSWORD}" --connect-expired-password -e "${MYSQL_SQL}" 2>&1; then
            success "MySQL configuration completed"
            echo ""
            echo -e "${GREEN}=================================="
            echo "  MySQL Configuration Completed!"
            echo "==================================${NC}"
            echo ""
            info "Database: ${MYSQL_DATABASE}"
            info "DB User: ${MYSQL_USER}"
            info "DB Password: ${MYSQL_PASSWORD}"
            echo ""
            return
        fi
        warn "Connection with temp password failed"
    fi
    
    info "Trying connection without password..."
    if mysql -u root -e "${MYSQL_SQL}" 2>&1; then
        success "MySQL configuration completed"
        echo ""
        echo -e "${GREEN}=================================="
        echo "  MySQL Configuration Completed!"
        echo "==================================${NC}"
        echo ""
        info "Database: ${MYSQL_DATABASE}"
        info "DB User: ${MYSQL_USER}"
        info "DB Password: ${MYSQL_PASSWORD}"
        echo ""
        return
    fi
    warn "Connection without password failed"
    
    info "Trying connection with socket..."
    if [ -S /var/lib/mysql/mysql.sock ]; then
        if mysql -u root --socket=/var/lib/mysql/mysql.sock -e "${MYSQL_SQL}" 2>&1; then
            success "MySQL configuration completed"
            echo ""
            echo -e "${GREEN}=================================="
            echo "  MySQL Configuration Completed!"
            echo "==================================${NC}"
            echo ""
            info "Database: ${MYSQL_DATABASE}"
            info "DB User: ${MYSQL_USER}"
            info "DB Password: ${MYSQL_PASSWORD}"
            echo ""
            return
        fi
    fi
    warn "Connection with socket failed"
    
    info "Trying mysqladmin to reset root password..."
    if [ -n "$INITIAL_PASSWORD" ]; then
        if mysqladmin -u root password "${MYSQL_PASSWORD}" --connect-expired-password -p"${INITIAL_PASSWORD}" 2>&1; then
            info "Password reset successful, now creating database..."
            if mysql -u root -p"${MYSQL_PASSWORD}" -e "CREATE DATABASE IF NOT EXISTS ${MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; CREATE USER IF NOT EXISTS '${MYSQL_USER}'@'localhost' IDENTIFIED BY '${MYSQL_PASSWORD}'; GRANT ALL PRIVILEGES ON ${MYSQL_DATABASE}.* TO '${MYSQL_USER}'@'localhost'; FLUSH PRIVILEGES;" 2>&1; then
                success "MySQL configuration completed"
                echo ""
                echo -e "${GREEN}=================================="
                echo "  MySQL Configuration Completed!"
                echo "==================================${NC}"
                echo ""
                info "Database: ${MYSQL_DATABASE}"
                info "DB User: ${MYSQL_USER}"
                info "DB Password: ${MYSQL_PASSWORD}"
                echo ""
                return
            fi
        fi
    fi
    warn "mysqladmin method failed"
    
    info "Trying skip-grant-tables method via config..."
    systemctl stop mysqld
    sleep 5
    
    info "Backing up my.cnf..."
    cp /etc/my.cnf /etc/my.cnf.backup 2>/dev/null || true
    cp /etc/mysql/my.cnf /etc/mysql/my.cnf.backup 2>/dev/null || true
    
    info "Adding skip-grant-tables to MySQL config..."
    if [ -f /etc/my.cnf ]; then
        echo -e "\n[mysqld]\nskip-grant-tables\nskip-networking" >> /etc/my.cnf
    elif [ -f /etc/mysql/my.cnf ]; then
        echo -e "\n[mysqld]\nskip-grant-tables\nskip-networking" >> /etc/mysql/my.cnf
    elif [ -d /etc/my.cnf.d ]; then
        echo -e "[mysqld]\nskip-grant-tables\nskip-networking" > /etc/my.cnf.d/skip-grant-tables.cnf
    fi
    
    info "Starting MySQL with skip-grant-tables..."
    systemctl start mysqld
    sleep 15
    
    info "Setting root password via skip-grant-tables..."
    if mysql -u root -e "FLUSH PRIVILEGES; ALTER USER 'root'@'localhost' IDENTIFIED BY '${MYSQL_PASSWORD}'; FLUSH PRIVILEGES;" 2>&1; then
        info "Password set successfully"
    else
        warn "Failed to set password with ALTER USER, trying UPDATE..."
        mysql -u root -e "FLUSH PRIVILEGES; UPDATE mysql.user SET authentication_string=PASSWORD('${MYSQL_PASSWORD}') WHERE User='root' AND Host='localhost'; FLUSH PRIVILEGES;" 2>&1
    fi
    
    info "Stopping MySQL..."
    systemctl stop mysqld
    sleep 5
    
    info "Restoring original MySQL config..."
    mv /etc/my.cnf.backup /etc/my.cnf 2>/dev/null || true
    mv /etc/mysql/my.cnf.backup /etc/mysql/my.cnf 2>/dev/null || true
    rm -f /etc/my.cnf.d/skip-grant-tables.cnf 2>/dev/null || true
    
    info "Restarting MySQL service..."
    systemctl start mysqld
    sleep 15
    
    info "Creating database and user..."
    if mysql -u root -p"${MYSQL_PASSWORD}" -e "CREATE DATABASE IF NOT EXISTS ${MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; CREATE USER IF NOT EXISTS '${MYSQL_USER}'@'localhost' IDENTIFIED BY '${MYSQL_PASSWORD}'; GRANT ALL PRIVILEGES ON ${MYSQL_DATABASE}.* TO '${MYSQL_USER}'@'localhost'; FLUSH PRIVILEGES;" 2>&1; then
        success "MySQL configuration completed"
        echo ""
        echo -e "${GREEN}=================================="
        echo "  MySQL Configuration Completed!"
        echo "==================================${NC}"
        echo ""
        info "Database: ${MYSQL_DATABASE}"
        info "DB User: ${MYSQL_USER}"
        info "DB Password: ${MYSQL_PASSWORD}"
        echo ""
        return
    fi
    
    error "Failed to configure MySQL database"
}

configure_firewall() {
    info "Configuring firewall..."
    
    if systemctl is-active --quiet firewalld; then
        firewall-cmd --zone=public --add-port=80/tcp --permanent
        firewall-cmd --zone=public --add-port=8000/tcp --permanent
        firewall-cmd --reload
        success "Firewall configuration completed"
    else
        warn "firewalld is not running, skipping firewall configuration"
    fi
}

configure_selinux() {
    info "Configuring SELinux..."
    
    SELINUX_STATUS=$(getenforce)
    if [ "$SELINUX_STATUS" = "Enforcing" ]; then
        setsebool -P httpd_can_network_connect 1
        success "SELinux configuration completed"
    else
        warn "SELinux is not enabled or disabled"
    fi
}

create_app_dir() {
    info "Creating application directories..."
    mkdir -p ${APP_DIR}
    mkdir -p ${APP_DIR}/backend/logs
    mkdir -p ${APP_DIR}/frontend
}

copy_app_files() {
    info "Copying application files..."
    
    SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
    
    if [ -d "${SCRIPT_DIR}/backend" ]; then
        cp -r ${SCRIPT_DIR}/backend/* ${APP_DIR}/backend/
    else
        error "Backend directory not found at ${SCRIPT_DIR}/backend"
    fi
    
    if [ -d "${SCRIPT_DIR}/frontend" ]; then
        cp -r ${SCRIPT_DIR}/frontend/* ${APP_DIR}/frontend/
    else
        error "Frontend directory not found at ${SCRIPT_DIR}/frontend"
    fi
    
    success "Application files copied"
}

install_python_deps() {
    info "Installing Python dependencies..."
    cd ${APP_DIR}/backend
    
    info "Finding Python ${PYTHON_VERSION} executable..."
    if command -v python${PYTHON_VERSION} &> /dev/null; then
        PYTHON_BIN="python${PYTHON_VERSION}"
        PIP_BIN="pip${PYTHON_VERSION}"
        info "Found python${PYTHON_VERSION}"
    elif command -v python3 &> /dev/null; then
        PYTHON_BIN="python3"
        PIP_BIN="pip3"
        info "Using python3 as fallback"
    elif command -v python &> /dev/null; then
        PYTHON_BIN="python"
        PIP_BIN="pip"
        info "Using python as fallback"
    else
        error "Python not found"
    fi
    
    info "Upgrading pip..."
    ${PYTHON_BIN} -m pip install --upgrade pip
    
    info "Installing requirements..."
    ${PYTHON_BIN} -m pip install -r requirements.txt
    
    success "Python dependencies installed"
}

install_node_deps() {
    info "Installing Node.js dependencies..."
    cd ${APP_DIR}/frontend
    
    npm install --production
    
    info "Building frontend project..."
    npm run build
    
    success "Node.js dependencies installed"
}

configure_env() {
    info "Configuring environment variables..."
    cat > ${APP_DIR}/backend/.env <<EOF
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=${MYSQL_USER}
MYSQL_PASSWORD=${MYSQL_PASSWORD}
MYSQL_DATABASE=${MYSQL_DATABASE}
SECRET_KEY=${SECRET_KEY}
PATROL_INTERVAL_SECONDS=30
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO
EOF
    success "Environment variables configured"
}

init_database() {
    info "Initializing database tables..."
    cd ${APP_DIR}/backend
    
    python${PYTHON_VERSION} -c "
from app.db.session import engine
from app.models.base import Base
Base.metadata.create_all(bind=engine)
print('Database tables created successfully')
"
    
    success "Database initialization completed"
}

create_backend_service() {
    info "Creating backend service..."
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
    
    success "Backend service created"
}

create_frontend_service() {
    info "Installing and configuring Nginx..."
    
    if ! command -v nginx &> /dev/null; then
        yum install -y nginx
    else
        info "Nginx already installed"
    fi
    
    cat > /etc/nginx/conf.d/vip-parking.conf <<EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    location / {
        root ${APP_DIR}/frontend/dist;
        try_files \$uri \$uri/ /index.html;
        expires 1d;
        add_header Cache-Control "public, max-age=86400";
    }

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

    location /docs {
        proxy_pass http://localhost:8000/docs;
    }

    location /redoc {
        proxy_pass http://localhost:8000/redoc;
    }

    location /api/system/health {
        proxy_pass http://localhost:8000/api/system/health;
        access_log off;
    }
}
EOF

    if [ -f /etc/nginx/conf.d/default.conf ]; then
        mv /etc/nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf.bak
    fi

    systemctl enable nginx
    
    success "Nginx configuration completed"
}

start_services() {
    info "Starting backend service..."
    systemctl start vip-parking-backend
    
    info "Waiting for backend service to start..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/api/system/health &> /dev/null; then
            success "Backend service started successfully"
            break
        fi
        sleep 1
        if [ $i -eq 30 ]; then
            error "Backend service start timeout"
        fi
    done
    
    info "Starting Nginx service..."
    systemctl restart nginx
    
    success "All services started"
}

verify_deployment() {
    info "Verifying deployment..."
    
    if ! systemctl is-active --quiet vip-parking-backend; then
        error "Backend service not running"
    fi
    
    if ! systemctl is-active --quiet nginx; then
        error "Nginx service not running"
    fi
    
    if ! curl -s http://localhost:8000/api/system/health | grep -q "success"; then
        error "API health check failed"
    fi
    
    success "Deployment verification passed"
}

show_info() {
    echo ""
    echo -e "${GREEN}=================================="
    echo "  VIP Parking Alert System Deployed!"
    echo "==================================${NC}"
    echo ""
    info "Access URLs:"
    info "  Frontend: http://$(hostname -I | awk '{print $1}')"
    info "  Backend API: http://$(hostname -I | awk '{print $1}'):8000"
    info "  API Docs: http://$(hostname -I | awk '{print $1}'):8000/docs"
    echo ""
    info "Configuration:"
    info "  Database: ${MYSQL_DATABASE}"
    info "  DB User: ${MYSQL_USER}"
    info "  DB Password: ${MYSQL_PASSWORD}"
    info "  Secret Key: ${SECRET_KEY}"
    echo ""
    info "Service Management:"
    info "  Backend: systemctl [start|stop|restart|status] vip-parking-backend"
    info "  Nginx: systemctl [start|stop|restart|status] nginx"
    info "  MySQL: systemctl [start|stop|restart|status] mysqld"
    echo ""
    info "Log Locations:"
    info "  Backend: ${APP_DIR}/backend/logs/"
    info "  Nginx: /var/log/nginx/"
    info "  MySQL: /var/log/mysqld.log"
    echo ""
    info "Configuration Files:"
    info "  Backend: ${APP_DIR}/backend/.env"
    info "  Nginx: /etc/nginx/conf.d/vip-parking.conf"
    echo ""
}

main() {
    echo -e "${GREEN}=================================="
    echo "  VIP Parking Alert System - CentOS Deployment"
    echo "  Database: MySQL 8.0"
    echo "==================================${NC}"
    echo ""
    
    check_root
    check_centos
    
    install_system_deps
    install_nodejs
    
    configure_mysql
    
    configure_firewall
    configure_selinux
    
    create_app_dir
    copy_app_files
    install_python_deps
    install_node_deps
    configure_env
    
    init_database
    
    create_backend_service
    create_frontend_service
    
    start_services
    
    verify_deployment
    
    show_info
}

main "$@"