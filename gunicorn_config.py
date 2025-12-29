#!/usr/bin/env python
"""
Gunicorn configuration for production deployment
"""
import multiprocessing
import os
from pathlib import Path

# Get base directory
BASE_DIR = Path(__file__).resolve().parent / 'attendance_system'

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = BASE_DIR / "logs" / "gunicorn_access.log"
errorlog = BASE_DIR / "logs" / "gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "attendance-api"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = os.environ.get("SSL_KEY_FILE")
certfile = os.environ.get("SSL_CERT_FILE")
ssl_version = 17  # TLSv1.2
ciphers = "HIGH:!aNULL:!MD5"

# Application
pythonpath = str(BASE_DIR)
# DJANGO_SETTINGS_MODULE should be set via environment variable
# Remove hardcoded production settings to allow flexibility

# Response settings
max_requests = 1000
max_requests_jitter = 100

# Hooks
def post_fork(server, worker):
    """Handle post fork"""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_fork(server, worker):
    """Handle pre fork"""
    pass

def pre_exec(server):
    """Handle pre exec"""
    server.log.info("Forking new master process")

def when_ready(server):
    """Handle when ready"""
    server.log.info("Gunicorn server is ready. Spawning workers")

def worker_int(worker):
    """Handle worker int"""
    worker.log.info("Worker received INT or QUIT signal")

def worker_abort(worker):
    """Handle worker abort"""
    worker.log.info("Worker received SIGABRT signal")
