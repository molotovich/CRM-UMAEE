import multiprocessing
import os

# Gunicorn configuration file
bind = "0.0.0.0:" + os.environ.get("PORT", "5001")
workers = multiprocessing.cpu_count() * 2 + 1
threads = 2
worker_class = "gthread"
timeout = 120
keepalive = 5
accesslog = "-"
errorlog = "-"

# Optimization: Preload app to save memory across workers
preload_app = True
