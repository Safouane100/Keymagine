import os
DEBUG = True

SECRET_KEY="79f96ec01b2a1db3d3081ce292db4c99bbe9fd22c67f5fce8f0413273abf4361"
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
MONGO_URL = "mongodb://mongodb:27017/"

CELERY_CONFIG = {
    "broker_url": MONGO_URL,
    "result_backend": MONGO_URL,
    "include": [
        "webapp.blueprints.wordpair.tasks"
    ],
    "broker_connection_retry_on_startup": True,
    "task_serializer": "pickle",
    "result_serializer": "pickle",
    "accept_content": ["application/json", "application/x-python-serialize"]
}

db_uri = "postgresql://user:pass@postgres:5432/webapp"
SQLALCHEMY_DATABASE_URI = db_uri
SQLALCHEMY_TRACK_MODIFICATIONS = False