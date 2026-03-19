#!/bin/bash

# =============================================================================
# GOVERNMENT-LEVEL DEPLOYMENT SCRIPT
# Automated deployment script for production government environments
# =============================================================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Script metadata
SCRIPT_NAME="Government Attendance System Deployment"
SCRIPT_VERSION="2.0.0"
DEPLOYMENT_DATE=$(date '+%Y-%m-%d %H:%M:%S UTC')

# =============================================================================
# CONFIGURATION AND ENVIRONMENT SETUP
# =============================================================================

# Default configuration
ENVIRONMENT="${ENVIRONMENT:-production}"
PROJECT_NAME="${PROJECT_NAME:-government-attendance-system}"
DOMAIN_NAME="${DOMAIN_NAME:-attendance.gov.local}"
BACKUP_ENABLED="${BACKUP_ENABLED:-true}"
MONITORING_ENABLED="${MONITORING_ENABLED:-true}"
SSL_ENABLED="${SSL_ENABLED:-true}"

# Directories
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${PROJECT_DIR}/backups"
CONFIG_DIR="${PROJECT_DIR}/config"
SSL_DIR="${PROJECT_DIR}/ssl"
DATA_DIR="${PROJECT_DIR}/data"
LOGS_DIR="${PROJECT_DIR}/logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "\n${PURPLE}========================================${NC}"
    echo -e "${PURPLE} $1${NC}"
    echo -e "${PURPLE}========================================${NC}\n"
}

check_prerequisites() {
    log_header "Checking Prerequisites"
    
    local missing_deps=()
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        missing_deps+=("Docker")
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        missing_deps+=("Docker Compose")
    fi
    
    # Check OpenSSL (for SSL certificate generation)
    if ! command -v openssl &> /dev/null; then
        missing_deps+=("OpenSSL")
    fi
    
    # Check required environment variables
    required_vars=("DB_PASSWORD" "SECRET_KEY" "ENCRYPTION_KEY")
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            missing_deps+=("Environment variable: $var")
        fi
    done
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing prerequisites:"
        for dep in "${missing_deps[@]}"; do
            echo -e "  ${RED}✗${NC} $dep"
        done
        exit 1
    fi
    
    log_success "All prerequisites met"
}

create_directories() {
    log_header "Creating Directory Structure"
    
    local dirs=(
        "${BACKUP_DIR}"
        "${CONFIG_DIR}/nginx/conf.d"
        "${CONFIG_DIR}/postgres"
        "${CONFIG_DIR}/redis"
        "${CONFIG_DIR}/prometheus"
        "${CONFIG_DIR}/grafana/provisioning/datasources"
        "${CONFIG_DIR}/grafana/provisioning/dashboards"
        "${CONFIG_DIR}/grafana/dashboards"
        "${CONFIG_DIR}/logstash"
        "${SSL_DIR}/certs"
        "${SSL_DIR}/private"
        "${DATA_DIR}/postgres_primary"
        "${DATA_DIR}/postgres_replica"
        "${DATA_DIR}/redis_master"
        "${DATA_DIR}/staticfiles"
        "${DATA_DIR}/media"
        "${LOGS_DIR}/nginx"
        "${LOGS_DIR}/application"
        "${LOGS_DIR}/security"
        "${LOGS_DIR}/audit"
    )
    
    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log_info "Created directory: $dir"
        fi
    done
    
    # Set proper permissions for sensitive directories
    chmod 700 "${SSL_DIR}/private"
    chmod 755 "${DATA_DIR}"
    chmod 755 "${LOGS_DIR}"
    
    log_success "Directory structure created"
}

generate_ssl_certificates() {
    log_header "Generating SSL Certificates"
    
    if [[ "$SSL_ENABLED" != "true" ]]; then
        log_warning "SSL disabled, skipping certificate generation"
        return
    fi
    
    local cert_file="${SSL_DIR}/certs/${DOMAIN_NAME}.crt"
    local key_file="${SSL_DIR}/private/${DOMAIN_NAME}.key"
    
    if [[ -f "$cert_file" && -f "$key_file" ]]; then
        log_info "SSL certificates already exist"
        return
    fi
    
    log_info "Generating self-signed SSL certificate for ${DOMAIN_NAME}"
    
    # Generate private key
    openssl genrsa -out "$key_file" 2048
    
    # Generate certificate signing request
    openssl req -new -key "$key_file" -out "${SSL_DIR}/private/${DOMAIN_NAME}.csr" \
        -subj "/C=US/ST=State/L=City/O=Government/OU=IT Department/CN=${DOMAIN_NAME}"
    
    # Generate self-signed certificate
    openssl x509 -req -days 365 -in "${SSL_DIR}/private/${DOMAIN_NAME}.csr" \
        -signkey "$key_file" -out "$cert_file"
    
    # Set proper permissions
    chmod 600 "$key_file"
    chmod 644 "$cert_file"
    
    log_success "SSL certificates generated"
}

create_configuration_files() {
    log_header "Creating Configuration Files"
    
    # Nginx configuration
    cat > "${CONFIG_DIR}/nginx/nginx.conf" << 'EOF'
user nginx;
worker_processes auto;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:" always;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/s;
    
    # Include configuration files
    include /etc/nginx/conf.d/*.conf;
}
EOF
    
    # Nginx server configuration
    cat > "${CONFIG_DIR}/nginx/conf.d/attendance.conf" << EOF
upstream api_backend {
    least_conn;
    server api_1:8000 max_fails=3 fail_timeout=30s;
    server api_2:8000 max_fails=3 fail_timeout=30s;
}

upstream websocket_backend {
    server websocket:8000;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name ${DOMAIN_NAME};
    return 301 https://\$server_name\$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name ${DOMAIN_NAME};
    
    # SSL configuration
    ssl_certificate /etc/ssl/certs/${DOMAIN_NAME}.crt;
    ssl_certificate_key /etc/ssl/private/${DOMAIN_NAME}.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Static files
    location /static/ {
        alias /app/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /app/media/;
        expires 1y;
    }
    
    # API endpoints with rate limiting
    location /api/auth/ {
        limit_req zone=auth burst=20 nodelay;
        proxy_pass http://api_backend;
        include /etc/nginx/proxy_params;
    }
    
    location /api/ {
        limit_req zone=api burst=50 nodelay;
        proxy_pass http://api_backend;
        include /etc/nginx/proxy_params;
    }
    
    # WebSocket connections
    location /ws/ {
        proxy_pass http://websocket_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Health check endpoint
    location /health/ {
        proxy_pass http://api_backend;
        access_log off;
    }
    
    # Admin interface
    location /admin/ {
        proxy_pass http://api_backend;
        include /etc/nginx/proxy_params;
    }
    
    # Default location
    location / {
        proxy_pass http://api_backend;
        include /etc/nginx/proxy_params;
    }
}
EOF
    
    # Nginx proxy parameters
    cat > "${CONFIG_DIR}/nginx/proxy_params" << 'EOF'
proxy_set_header Host $http_host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_connect_timeout 30s;
proxy_send_timeout 30s;
proxy_read_timeout 30s;
proxy_buffering on;
proxy_buffer_size 4k;
proxy_buffers 8 4k;
EOF

    # PostgreSQL configuration
    cat > "${CONFIG_DIR}/postgres/postgresql.conf" << 'EOF'
# Government security configuration
listen_addresses = '*'
port = 5432
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100

# Logging configuration for audit
logging_collector = on
log_directory = 'pg_log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_truncate_on_rotation = off
log_rotation_age = 1d
log_rotation_size = 100MB
log_statement = 'all'
log_duration = on
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '

# Security settings
ssl = off
password_encryption = md5
EOF
    
    # Redis configuration
    cat > "${CONFIG_DIR}/redis/redis-master.conf" << 'EOF'
# Government security Redis configuration
bind 0.0.0.0
port 6379
protected-mode yes
requirepass "${REDIS_PASSWORD:-changeme123}"

# Memory and persistence
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000

# Logging
loglevel notice
logfile "/var/log/redis/redis-server.log"

# Security
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command EVAL ""
rename-command DEBUG ""
EOF
    
    log_success "Configuration files created"
}

setup_monitoring() {
    log_header "Setting Up Monitoring"
    
    if [[ "$MONITORING_ENABLED" != "true" ]]; then
        log_warning "Monitoring disabled, skipping setup"
        return
    fi
    
    # Prometheus configuration
    cat > "${CONFIG_DIR}/prometheus/prometheus.yml" << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "/etc/prometheus/rules/*.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node_exporter:9100']
  
  - job_name: 'attendance-api'
    static_configs:
      - targets: ['api_1:8000', 'api_2:8000']
    metrics_path: '/metrics/'
    
  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:9113']
      
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres_exporter:9187']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
EOF
    
    # Grafana datasource configuration
    cat > "${CONFIG_DIR}/grafana/provisioning/datasources/prometheus.yml" << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF
    
    log_success "Monitoring configuration created"
}

generate_environment_file() {
    log_header "Generating Environment Configuration"
    
    local env_file="${PROJECT_DIR}/.env.production"
    
    cat > "$env_file" << EOF
# =============================================================================
# GOVERNMENT ATTENDANCE SYSTEM - PRODUCTION ENVIRONMENT
# Generated on: ${DEPLOYMENT_DATE}
# =============================================================================

# Environment Configuration
ENVIRONMENT=production
DEBUG=False

# Security Configuration (CRITICAL - CHANGE THESE VALUES)
SECRET_KEY=${SECRET_KEY}
ENCRYPTION_KEY=${ENCRYPTION_KEY}

# Database Configuration
DB_NAME=${DB_NAME:-attendance_gov}
DB_USER=${DB_USER:-postgres}
DB_PASSWORD=${DB_PASSWORD}
DB_PRIMARY_PORT=5432
DB_REPLICA_PORT=5433

# Redis Configuration  
REDIS_PASSWORD=${REDIS_PASSWORD:-changeme123}
REDIS_MASTER_PORT=6379
REDIS_SENTINEL_PORT=26379

# Network Configuration
DOMAIN_NAME=${DOMAIN_NAME}
ALLOWED_HOSTS=${DOMAIN_NAME},localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=https://${DOMAIN_NAME}
CSRF_TRUSTED_ORIGINS=https://${DOMAIN_NAME}

# SSL Configuration
SSL_ENABLED=${SSL_ENABLED}

# Feature Flags
ENABLE_MULTI_TENANCY=True
ENABLE_ENTERPRISE_SECURITY=True
ENABLE_COMPLIANCE_MONITORING=True

# Monitoring Ports
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
ELASTICSEARCH_PORT=9200
KIBANA_PORT=5601
LOGSTASH_PORT=5044
FLOWER_PORT=5555

# Grafana Admin Credentials (CHANGE THESE)
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-admin123}

# Flower Monitoring Credentials
FLOWER_USER=admin
FLOWER_PASSWORD=${FLOWER_PASSWORD:-admin123}

# Backup Configuration
BACKUP_ENABLED=${BACKUP_ENABLED}
BACKUP_SCHEDULE="0 2 * * *"
BACKUP_RETENTION_DAYS=30

# File Paths
DATA_PATH=${DATA_DIR}
MEDIA_PATH=${DATA_DIR}/media
LOGS_PATH=${LOGS_DIR}

# Email Configuration (Optional - for notifications)
EMAIL_HOST=${EMAIL_HOST:-}
EMAIL_PORT=${EMAIL_PORT:-587}
EMAIL_HOST_USER=${EMAIL_HOST_USER:-}
EMAIL_HOST_PASSWORD=${EMAIL_HOST_PASSWORD:-}
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=${DEFAULT_FROM_EMAIL:-noreply@${DOMAIN_NAME}}

# AWS S3 Configuration (Optional - for file storage)
AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID:-}
AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY:-}
AWS_STORAGE_BUCKET_NAME=${AWS_STORAGE_BUCKET_NAME:-}
AWS_S3_REGION_NAME=${AWS_S3_REGION_NAME:-us-east-1}
AWS_S3_BACKUP_BUCKET=${AWS_S3_BACKUP_BUCKET:-}

# Monitoring and Error Tracking
SENTRY_DSN=${SENTRY_DSN:-}
LOG_LEVEL=INFO

# Government Compliance Settings
COMPLIANCE_MODE=ENABLED
AUDIT_LOGGING=ENABLED
DATA_RETENTION_DAYS=2555
EOF
    
    chmod 600 "$env_file"
    log_success "Environment file created: $env_file"
}

deploy_application() {
    log_header "Deploying Application"
    
    # Load environment variables
    set -a
    source "${PROJECT_DIR}/.env.production"
    set +a
    
    # Pull latest images
    log_info "Pulling Docker images..."
    docker-compose -f docker-compose.production.yml pull
    
    # Build application image
    log_info "Building application image..."
    docker-compose -f docker-compose.production.yml build --no-cache
    
    # Stop existing containers
    log_info "Stopping existing containers..."
    docker-compose -f docker-compose.production.yml down --remove-orphans
    
    # Start database and cache first
    log_info "Starting database and cache services..."
    docker-compose -f docker-compose.production.yml up -d db_primary redis_master
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    sleep 30
    
    # Run database migrations
    log_info "Running database migrations..."
    docker-compose -f docker-compose.production.yml run --rm api_1 \
        python manage.py migrate --no-input
    
    # Collect static files
    log_info "Collecting static files..."
    docker-compose -f docker-compose.production.yml run --rm api_1 \
        python manage.py collectstatic --no-input --clear
    
    # Create superuser (if not exists)
    log_info "Creating superuser..."
    docker-compose -f docker-compose.production.yml run --rm api_1 \
        python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@${DOMAIN_NAME}', '${ADMIN_PASSWORD:-admin123}');
    print('Superuser created')
else:
    print('Superuser already exists')
"
    
    # Start all services
    log_info "Starting all services..."
    docker-compose -f docker-compose.production.yml up -d
    
    # Wait for services to stabilize
    log_info "Waiting for services to stabilize..."
    sleep 60
    
    # Verify deployment
    log_info "Verifying deployment..."
    if curl -f -s "http://localhost/health/" > /dev/null; then
        log_success "Application deployed successfully"
    else
        log_error "Deployment verification failed"
        return 1
    fi
}

setup_backup_job() {
    log_header "Setting Up Automated Backups"
    
    if [[ "$BACKUP_ENABLED" != "true" ]]; then
        log_warning "Backups disabled, skipping setup"
        return
    fi
    
    # Create backup script
    cat > "${PROJECT_DIR}/scripts/backup_database.sh" << 'EOF'
#!/bin/bash
set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="/backups/attendance_db_${TIMESTAMP}.sql"

# Create database dump
docker-compose -f docker-compose.production.yml exec -T db_primary \
    pg_dump -U "${DB_USER}" "${DB_NAME}" > "${BACKUP_FILE}"

# Compress backup
gzip "${BACKUP_FILE}"

# Upload to S3 (if configured)
if [[ -n "${AWS_S3_BACKUP_BUCKET:-}" ]]; then
    aws s3 cp "${BACKUP_FILE}.gz" "s3://${AWS_S3_BACKUP_BUCKET}/database/"
fi

# Clean old backups (keep last 30 days)
find /backups -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: ${BACKUP_FILE}.gz"
EOF
    
    chmod +x "${PROJECT_DIR}/scripts/backup_database.sh"
    
    # Add to crontab
    (crontab -l 2>/dev/null || echo "") | grep -v "backup_database.sh" | \
    (cat; echo "0 2 * * * ${PROJECT_DIR}/scripts/backup_database.sh") | crontab -
    
    log_success "Automated backups configured"
}

print_deployment_summary() {
    log_header "Deployment Summary"
    
    cat << EOF
${GREEN}✓ Government AI Attendance System Successfully Deployed${NC}

${BLUE}Application Information:${NC}
  • Version: ${SCRIPT_VERSION}
  • Environment: ${ENVIRONMENT}
  • Domain: https://${DOMAIN_NAME}
  • Deployment Date: ${DEPLOYMENT_DATE}

${BLUE}Service URLs:${NC}
  • Main Application: https://${DOMAIN_NAME}
  • Admin Panel: https://${DOMAIN_NAME}/admin/
  • API Documentation: https://${DOMAIN_NAME}/api/
  • Grafana Dashboard: https://${DOMAIN_NAME}:3001/
  • Kibana Logs: https://${DOMAIN_NAME}:5601/

${BLUE}Security Features:${NC}
  ✓ Multi-tenant architecture enabled
  ✓ Enterprise security controls active
  ✓ Compliance monitoring enabled
  ✓ SSL/TLS encryption configured
  ✓ Audit logging activated

${BLUE}High Availability Features:${NC}
  ✓ Database read replicas
  ✓ Redis clustering
  ✓ Load-balanced API instances  
  ✓ Automated backups
  ✓ Health monitoring

${YELLOW}Next Steps:${NC}
  1. Configure DNS to point ${DOMAIN_NAME} to this server
  2. Replace self-signed SSL certificates with CA-signed certificates
  3. Review and customize government compliance settings
  4. Set up external monitoring and alerting
  5. Perform security hardening review
  6. Configure backup testing procedures

${YELLOW}Important Files:${NC}
  • Environment Config: .env.production
  • SSL Certificates: ssl/
  • Configuration Files: config/
  • Application Logs: logs/
  • Backup Location: backups/

${RED}Security Reminders:${NC}
  ⚠️  Change default admin password: ${ADMIN_PASSWORD:-admin123}
  ⚠️  Update Grafana admin password: ${GRAFANA_ADMIN_PASSWORD:-admin123}
  ⚠️  Review firewall settings
  ⚠️  Enable fail2ban for SSH protection
  ⚠️  Regular security updates required

For support and documentation, visit: https://github.com/your-org/government-attendance-system
EOF
}

# =============================================================================
# MAIN DEPLOYMENT PROCESS
# =============================================================================

main() {
    log_header "$SCRIPT_NAME v$SCRIPT_VERSION"
    log_info "Starting government-level deployment process..."
    
    # Deployment steps
    check_prerequisites
    create_directories
    generate_ssl_certificates
    create_configuration_files
    setup_monitoring
    generate_environment_file
    deploy_application
    setup_backup_job
    print_deployment_summary
    
    log_success "Deployment completed successfully!"
}

# Run main function
main "$@"