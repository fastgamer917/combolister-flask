from flask import Flask
from celery_app import make_celery

app = Flask(__name__)

# Optional: Add Flask config for Celery
app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379/0',  # Replace with your Redis broker URL
    CELERY_RESULT_BACKEND='redis://localhost:6379/0'
)

# Create a Celery instance
celery = make_celery(app)

@app.route('/submit_search')
def submit_search():
    # Example: Calling a Celery task
    reverse.delay("Hello, Celery!")
    return "Task is running in the background!"
