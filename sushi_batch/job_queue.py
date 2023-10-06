import json
from os import path

from . import console_utils as cu
from . import settings as s
from .enums import Status, Task
from .json_hooks import JobDecoder, JobEncoder
from .mkv_merge import MKVMerge
from .streams import Stream
from .sub_sync import Sushi


class JobQueue:
    def __init__(self, contents=[]):
        self.contents = contents
        self.file_path = path.join(s.config.data_path, "queue_data.json")

    # Save queue contents to JSON file
    def save(self):
        # Set JSON file path
        with open(self.file_path, "w", encoding="utf-8") as data_file:
            json.dump(self.contents, data_file, cls=JobEncoder, indent=4)

    # Load queue contents from JSON file
    def load(self):
        if path.exists(self.file_path):
            # Return jobs list if data file is found
            with open(self.file_path, "r", encoding="utf-8") as data_file:
                # Read JSON file
                self.contents = json.load(data_file, cls=JobDecoder)

    # Add selected jobs to queue
    def add_jobs(self, selected_jobs_indexes, unqueued_jobs, task):
        # Queue all jobs or those selected by user
        if selected_jobs_indexes == "all":
           jobs_to_queue = unqueued_jobs.copy()
        else:
            jobs_to_queue = [unqueued_jobs[job_idx - 1] for job_idx in selected_jobs_indexes]
            
        # Allow setting audio and subtitle track indexes for video-sync tasks
        if task in (Task.VIDEO_SYNC_DIR, Task.VIDEO_SYNC_FIL):
            if cu.confirm_action("\nSpecify audio and sub track indexes for job(s)? (Y/N): "):
                self.set_stream_indexes(jobs_to_queue, task)
            else:
                for job in jobs_to_queue:
                    indexes = JobQueue.get_indexes(job, False)
                    job.__dict__.update(indexes)
                    
        # Add to queue and update data file
        self.contents.extend(jobs_to_queue)
        self.save()

    # Remove selected jobs from queue
    def remove_jobs(self, selected_jobs_indexes):
        # Remove jobs from queue in reverse order to avoid out of bounds error
        for job_idx in sorted(selected_jobs_indexes, reverse=True):
            # Decrease index by 1 to match real job index
            del self.contents[job_idx - 1]

        # Update JSON data file
        self.save()

    # Run user-selected jobs
    def run_jobs(self, selected_jobs_indexes):
        # Get jobs to run
        if selected_jobs_indexes == "all":
            jobs_to_run = [job for job in self.contents if job.status == Status.PENDING]
        else:
            jobs_to_run = [
                self.contents[job_idx - 1]
                for job_idx in selected_jobs_indexes
                if self.contents[job_idx - 1].status == Status.PENDING
            ]
        
        if jobs_to_run: 
            # Run sync on selected jobs 
            cu.print_subheader("Running jobs")           
            for job in jobs_to_run:
                Sushi.run(job)
                self.save()  # Update data file after job execution

            # If enabled and mkvmerge is installed, merge files for completed jobs
            if s.config.merge_files_after_execution:
                if cu.is_app_installed("mkvmerge"):
                    self.merge_completed_video_tasks(jobs_to_run)
                else:
                    cu.print_error("\nMKVMerge could not be found. Video files cannot be merged.")
        else:
            cu.print_error("\nNo pending jobs to run!")
            
    # Generate a new video file from completed video tasks
    def merge_completed_video_tasks(self, job_list):
        completed_jobs = [
            job 
            for job in job_list
            if job.status == Status.COMPLETED 
            and job.task in (Task.VIDEO_SYNC_DIR, Task.VIDEO_SYNC_FIL)
            and job.merged == False
        ]
        
        if completed_jobs:
            cu.print_subheader("Merging files")
            for job in completed_jobs:
                MKVMerge.run(job)
                self.save()
            input("\nPress Enter to go back... ")
        else:
            cu.print_error("No completed jobs to merge!")
            
    # Clear queue contents
    def clear(self):
        self.contents.clear()
        self.save()

    # Remove jobs without Pending Status
    def clear_completed_jobs(self):
        jobs_to_remove = [
            idx
            for idx, (job) in enumerate(self.contents, start=1)
            if job.status != Status.PENDING
        ]

        if jobs_to_remove:
            self.remove_jobs(jobs_to_remove)
            cu.print_success("Completed jobs cleared from queue.")
        else:
            cu.print_error("No completed jobs to clear!")

    # Select and validate jobs selected by user
    def select_jobs(self, prompt):
        # Get selected indexes from user input
        user_input = input(f"\n{cu.fore.LIGHTBLACK_EX}{prompt}")
        selected_jobs_indexes = user_input.replace(" ", "").split(",")

        # Store job queue length for validations
        valid_job_indexes = []
        job_list_range = range(1, len(self.contents) + 1)

        for idx in selected_jobs_indexes:
            # Check if item is a number
            if idx.isnumeric():
                job_index = int(idx)
                # Add to valid indexes list if found on range
                if job_index in job_list_range:
                    valid_job_indexes.append(job_index)

            # Check if item is a range of jobs (e.g., "15-20")
            elif "-" in idx:
                start, end = map(int, idx.split("-"))
                # Increase end index by 1 to match range max number
                for job_index in range(start, end + 1):
                    if job_index in job_list_range:
                        valid_job_indexes.append(job_index)

        # Return valid indexes list if not empty
        if valid_job_indexes:
            valid_job_indexes.sort()
            print(f"{cu.fore.LIGHTYELLOW_EX}Selected jobs: {valid_job_indexes}\n")
            return valid_job_indexes
        else:
            cu.print_error("Invalid choice! Please select valid jobs.")
            return None

    # Allow selecting a stream index
    @staticmethod
    def get_stream_index(streams, prompt):
        last_stream_index = Stream.get_last_stream(streams)
        Stream.show_streams(streams)
        return str(cu.get_choice(0, last_stream_index, prompt))
    
    # Get all stream indexes
    @staticmethod
    def get_indexes(job, select_streams):
        # Get source and destination media streams
        src_aud_streams = Stream.get_streams(job.src_file, "audio")
        src_sub_streams = Stream.get_streams(job.src_file, "subtitle")
        dst_aud_streams = Stream.get_streams(job.dst_file, "audio")

        if select_streams:
            print(f"{cu.fore.LIGHTYELLOW_EX}\nJob {job.idx}")
            src_aud_id = JobQueue.get_stream_index(src_aud_streams, "Select a source audio stream: ")
            src_sub_id = JobQueue.get_stream_index(src_sub_streams, "Select a source subtitle stream: ")
            dst_aud_id = JobQueue.get_stream_index(dst_aud_streams, "Select a destination audio stream: ")
        else:
            src_aud_id = Stream.get_first_stream(src_aud_streams)
            src_sub_id = Stream.get_first_stream(src_sub_streams)
            dst_aud_id = Stream.get_first_stream(dst_aud_streams)
        
        indexes = {
            "src_aud_id": src_aud_id,
            "src_sub_id": src_sub_id,
            "dst_aud_id": dst_aud_id,
            "src_sub_lang": Stream.get_stream_lang(src_sub_streams, src_sub_id),
            "src_sub_name": Stream.get_stream_name(src_sub_streams, src_sub_id),
        }
        return indexes
    
    @staticmethod
    def set_stream_indexes(unqueued_jobs, task):
        if len(unqueued_jobs) > 1 and cu.confirm_action("\nSet default stream index for all jobs? (Y/N): "):
            # Set default track indexes for all jobs
            default_indexes = JobQueue.get_indexes(unqueued_jobs[0], True) # Use first job as reference
            for job in unqueued_jobs:
                job.__dict__.update(default_indexes) # Update object dict with indexes
        else:
            # Set track indexes per job
            for job in unqueued_jobs:
                indexes = JobQueue.get_indexes(job, True)
                job.__dict__.update(indexes)

    # Show Job List
    def show(self, task):
        cu.clear_screen()

        # Show title based on current task
        title = "Job Queue" if task == Task.JOB_QUEUE else "Jobs"
        cu.print_header(f"{title}")

        # Enumerate job list and get the number of the iteration
        for job in self.contents:
            job.idx = self.contents.index(job) + 1
            print(f"\n{cu.fore.LIGHTBLACK_EX}Job {job.idx}")
            print(f"{cu.fore.LIGHTBLUE_EX}Source file: {job.src_file}")
            print(f"{cu.fore.LIGHTYELLOW_EX}Destination file: {job.dst_file}")

            # Don't show field if value is None
            if job.sub_file is not None:
                print(f"{cu.fore.LIGHTCYAN_EX }Subtitle file: {job.sub_file}")

            if job.src_aud_id is not None:
                print(
                    f"{cu.fore.LIGHTMAGENTA_EX}Source Audio Track ID: {job.src_aud_id}"
                )

            if job.src_sub_id is not None:
                print(
                    f"{cu.fore.LIGHTCYAN_EX}Source Subtitle Track ID: {job.src_sub_id}"
                )

            if job.dst_aud_id is not None:
                print(
                    f"{cu.fore.YELLOW}Destination Audio Track ID: {job.dst_aud_id}"
                )

            if task == Task.JOB_QUEUE: 
                match job.status:
                    case Status.PENDING:
                        print(f"{cu.fore.LIGHTBLACK_EX}Status: Pending")
                    case Status.COMPLETED:
                        print(f"{cu.fore.LIGHTGREEN_EX}Status: Completed")
                        print(f"{cu.fore.GREEN}Average Shift: {job.result}")
                    case Status.FAILED:
                        print(f"{cu.fore.LIGHTRED_EX}Status: Failed")
                        print(f"{cu.fore.RED}Error: {job.result}")
                        
                match job.merged:
                    case True:
                        print(f"{cu.fore.LIGHTGREEN_EX}Merged: Yes")
                    case False:
                        print(f"{cu.fore.LIGHTBLACK_EX}Merged: No")

