from os import path
import json
import job


# Save queue contents to JSON file
def save_list_data(job_list):
    # Set JSON file path
    file_path = path.join(path.dirname(__file__), "queue_data.json")

    with open(file_path, "w", encoding="utf-8") as json_file:
        json.dump(job_list, json_file, default=lambda obj: obj.__dict__, indent=4)


# Load queue contents from JSON file
def load_list_data():
    # Set JSON file path
    file_path = path.join(path.dirname(__file__), "queue_data.json")

    if path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as json_file:
            # Read JSON file
                queued_jobs = json.load(json_file)

                # Create objects for each array element
                job_list = [
                    job.Job(
                        queued_job["idx"],
                        queued_job["src_file"],
                        queued_job["dst_file"],
                        queued_job["sub_file"],
                        queued_job["task"],
                        queued_job["src_aud_track_id"],
                        queued_job["src_sub_track_id"],
                        queued_job["dst_aud_track_id"],
                        queued_job["status"],
                        queued_job["result"],
                    )
                    for queued_job in queued_jobs
                ]
                
                return job_list
        except json.JSONDecodeError:
            cu.print_error("An error ocurred while loading the queue contents")
