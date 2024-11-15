from flask import Flask, request
from celery_app import make_celery
from search_controller import search_folder_files_v2

app = Flask(__name__)

# Optional: Add Flask config for Celery
app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379/0',  # Replace with your Redis broker URL
    CELERY_RESULT_BACKEND='redis://localhost:6379/0'
)

# Create a Celery instance
celery = make_celery(app)


@celery.task
def create_task(**kwargs):
    search_folder_files_v2(**kwargs)


@app.route('/', methods=['GET'])
def index():
    return 'Hello World!. Server running fine'

@app.route('/submit_search', methods=['POST'])
def submit_search():
    json_data = request.get_json()
    search_term = json_data['search_term']
    task_progress_obj_pk = json_data['search_progress_obj_pk']
    folder_path = json_data['logs_folder_path']
    create_task.delay(search_term=search_term, task_progress_obj_pk=task_progress_obj_pk, folder_path=folder_path)
    return "Task is running in the background!"



app.run(host='0.0.0.0', port=7002, debug=True)
