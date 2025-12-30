import psutil
from django.utils import timezone
from .models import ActivityLog

def log_system_metrics():
    """Log system metrics every minute"""
    try:
        # CPU Usage
        cpu_percent = psutil.cpu_percent(interval=1)
        ActivityLog.objects.create(
            log_type='system',
            metric='cpu_usage',
            value=cpu_percent,
            message=f'CPU Usage: {cpu_percent}%'
        )

        # Memory Usage
        memory = psutil.virtual_memory()
        ActivityLog.objects.create(
            log_type='system',
            metric='memory_usage',
            value=memory.percent,
            message=f'Memory Usage: {memory.percent}%'
        )

        # Disk Usage
        disk = psutil.disk_usage('/')
        ActivityLog.objects.create(
            log_type='system',
            metric='disk_usage',
            value=disk.percent,
            message=f'Disk Usage: {disk.percent}%'
        )
    except Exception as e:
        ActivityLog.objects.create(
            log_type='error',
            severity='error',
            message=f'Failed to log system metrics: {str(e)}'
        )