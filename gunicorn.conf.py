import os

# Render provides PORT environment variable
port = int(os.environ.get("PORT", 8000))

# Gunicorn configuration for Render deployment
bind = f"0.0.0.0:{port}"
workers = 1  # Single worker for SQLite compatibility
worker_class = "sync"
timeout = 120
keepalive = 2
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "jamnesia"

# Worker processes
worker_tmp_dir = "/dev/shm"

# Security
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190