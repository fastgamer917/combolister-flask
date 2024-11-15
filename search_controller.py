import os
import multiprocessing
import queue as Queue
import requests
from app import celery


def send_combos_to_remote(to_remote_send_results_for_file,task_progress_obj_pk):
    """Send the combos to the remote server"""
    try:
        if to_remote_send_results_for_file:
            url = "http://16.171.36.93:4891/combolister/api/save_results"
            json_data ={
                "search_id":task_progress_obj_pk,
                "results":to_remote_send_results_for_file
            }
            res = requests.put(url, json=json_data)
    except Exception as e:
        print(f"Error sending combos to remote: Exception: {e}")
        return False
    return True


def find_lines_with_keyword(file_path, file_name, keyword, output_queue,task_progress_obj_pk):
    to_remote_send_results_for_file = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                if keyword in line:
                    try:
                        to_remote_send_results_for_file.append({"found_string":line.strip(),"found_in_file":file_name})
                        output_queue.put((file_name, line.strip()), block=False)
                    except Queue.Full:
                        send_combos_to_remote(to_remote_send_results_for_file, task_progress_obj_pk)
                        return
        send_combos_to_remote(to_remote_send_results_for_file,task_progress_obj_pk)
    except Exception as e:
        output_queue.put((file_path, f"Error reading file: {str(e)}"))

def process_files_in_folder(folder_path, keyword, num_processes,task_progress_obj_pk):
    manager = multiprocessing.Manager()
    output_queue = manager.Queue(maxsize=1000)  # Limit queue size to 20000 items
    processes = []

    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            p = multiprocessing.Process(target=find_lines_with_keyword, args=(file_path, file, keyword, output_queue,task_progress_obj_pk))
            processes.append(p)
            p.start()

            # Limit the number of concurrent processes
            if len(processes) >= num_processes:
                for p in processes:
                    p.join()
                processes = []

    # Ensure all remaining processes are joined
    for p in processes:
        p.join()

    # Collect results from queue
    matches = []
    while not output_queue.empty():
        matches.append(output_queue.get())

    return matches


@celery.task
def search_folder_files_v2(keyword:str,task_progress_obj_pk:int, folder_path:str)->list:
    num_processes = multiprocessing.cpu_count()  # Adjust this based on your system's capabilities
    to_return_list=[]
    matches = process_files_in_folder(folder_path.strip(), keyword.strip(), num_processes,task_progress_obj_pk)
    for file_name, combo in matches:
        to_return_list.append({
            "combo":combo,
            "source":file_name,
        })

    #remove duplicate findings
    seen = set()  # Set to track seen "combo" values
    unique_data = []  # List to store unique dictionaries

    for item in to_return_list:
        combo = item["combo"]
        if combo not in seen:
            unique_data.append(item)
            seen.add(combo)

    # unique_data now contains dictionaries with unique "combo" values
    return unique_data
