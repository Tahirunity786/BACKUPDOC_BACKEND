import os
from celery import Celery
from kombu import Queue

# Set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "processor.settings")

# Create an instance of the Celery application
app = Celery("processor")

# Load task-related settings with the prefix 'CELERY_'
app.config_from_object("django.conf:settings", namespace="CELERY")

# Define priority queues properly
app.conf.task_queues = (
    # Queue("high_priority"),
    Queue("default"),
)

# Set default queue
app.conf.task_default_queue = "default"

# Route specific tasks to high-priority queue
# app.conf.task_routes = {
#     "core_payment.tasks.email_agent": {"queue": "high_priority"},
# }

# # Define the periodic task schedule.
# app.conf.beat_schedule = {
#     'expire-bookings-every-5-minutes': {
#         'task': 'core_posts.tasks.expire_bookings',  # Replace 'bookings' with your app name
#         'schedule': crontab(minute='*/5'),        # Runs every 5 minutes
#     },
# }


# Auto-discover tasks
app.autodiscover_tasks()
