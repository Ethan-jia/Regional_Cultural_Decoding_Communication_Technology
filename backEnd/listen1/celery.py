import os
import django
from celery import Celery

from celery.schedules import crontab
from listen1.settings import BASE_DIR

base_name = os.path.basename(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'{base_name}.settings')  # 设置django环境
django.setup()

celery_app = Celery(f'{base_name}')
celery_app.config_from_object('django.conf:settings', namespace='CELERY')  # 使用CELERY_ 作为前缀，在settings中写配置
celery_app.autodiscover_tasks()  # 发现任务文件每个app下的task.py

celery_app.conf.update(
    CELERYBEAT_SCHEDULE={
        'every-30-min': {
            'task': 'app.tasks.test',
            # 'schedule': crontab(hour=2, minute=26),
            'schedule': crontab(hour=10, minute=47),
        }
    }
)

# celery worker -B -A listen1 --loglevel=info --pool=solo --concurrency=10


