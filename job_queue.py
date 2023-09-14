import json
from os import path
from json_hooks import JobEncoder, JobDecoder
from enums import Task, Status
from streams import Stream
import sub_sync
import console_utils as cu


class JobQueue:
    def __init__(self, contents=[]):
        self.contents = contents
        self.data_path = path.join(path.dirname(__file__), "queue_data.json")

    # Save queue contents to JSON file
    def save(self):
        # Set JSON file path
        with open(self.data_path, "w", encoding="utf-8") as data_file:
            json.dump(self.contents, data_file, cls=JobEncoder, indent=4)

    # Load queue contents from JSON file
    def load(self):
        # Return jobs list if data file is found
        if path.exists(self.data_path):
            with open(self.data_path, "r", encoding="utf-8") as data_file:
                # Read JSON file
                self.contents = json.load(data_file, cls=JobDecoder)

    # Add selected jobs to queue
    def add_jobs(self, selected_jobs_indexes, unqueued_jobs, task):
        # Allow setting audio and subtitle track indexes for video-sync tasks
        if task in (Task.VIDEO_SYNC_DIR, Task.VIDEO_SYNC_FIL) and cu.confirm_action(
            "\nSpecify audio and sub track indexes for job(s)? (Y/N): "
        ):
            self.set_track_indexes(task)

        # Queue all jobs or those selected by user
        if selected_jobs_indexes == "all":
            self.contents.extend(unqueued_jobs)
        else:
            jobs_to_queue = [
                unqueued_jobs[job_idx - 1] 
                for job_idx in selected_jobs_indexes
            ]
            self.contents.extend(jobs_to_queue)

        # Update JSON data file
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
            jobs_to_run = [
                job 
                for job in self.contents 
                if job.status == Status.PENDING
            ]
        else:
            jobs_to_run = [
                self.contents[job_idx - 1]
                for job_idx in selected_jobs_indexes
                if self.contents[job_idx - 1].status == Status.PENDING
            ]

        # Run sync on selected jobs
        for job in jobs_to_run:
            sub_sync.shift_subs(job)
            self.save()  # Update data file after job completion

    # Clear queue contents
    def clear(self):
        self.contents.clear()
        self.save()

    # Remove jobs without Pending Status
    def clear_completed_jobs(self):
        jobs_to_remove = [
            idx
            for idx, (job) in enumerate(self.contents, start=1)
            if job.status != "Pending"
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
            cu.print_error("Invalid choice! Please select valid jobs.", False)
            return None

    # Get track index from user input
    def get_track_id(self, prompt):
        while True:
            track_id = input(f"{cu.style_reset}{cu.fore.LIGHTBLACK_EX}{prompt}")
            if track_id.isnumeric():
                return track_id
            cu.print_error("Invalid index! Please input a number!", False)

    # Set custom track indexes for video sync tasks
    def set_track_indexes(self, task):
        # Allow setting default track indexes only if job list contains more than one job
        if len(self.contents) > 1 and cu.confirm_action(
            "\nSet a default audio and sub track index for all jobs? [Only useful when all files have the same number of tracks] (Y/N): "
        ):
            src_audio_id = get_track_id("\nSource Audio Track ID: ")
            src_sub_id = get_track_id("Source Subtitle Track ID: ")
            dst_audio_id = get_track_id("Destination Audio Track ID: ")
            for job in job_list:
                job.src_aud_track_id = src_audio_id
                job.src_sub_track_id = src_sub_id
                job.dst_aud_track_id = dst_audio_id
        else:
            # Set track indexes per job
            for job in self.contents:
                # Show job index
                print(f"\n{cu.fore.LIGHTYELLOW_EX}Job {job.idx}")

                # Get source and destination media streams
                src_aud_streams = Stream.get_streams(job.src_file, "audio")
                src_sub_streams = Stream.get_streams(job.src_file, "subtitle")
                dst_aud_streams = Stream.get_streams(job.dst_file, "audio")

                # Limit user input to one of the streams shown
                Stream.show_streams(src_aud_streams)
                job.src_aud_track_id = str(
                    cu.get_choice(
                        end=Stream.get_last_id(src_aud_streams),
                        prompt="Select a source audio stream: ",
                    )
                )

                # Limit user input to one of the streams shown
                Stream.show_streams(src_sub_streams)
                job.src_sub_track_id = str(
                    cu.get_choice(
                        end=Stream.get_last_id(src_sub_streams),
                        prompt="Select a source subtitle stream: ",
                    )
                )

                # Get selected subtitle language code
                job.src_sub_lang = Stream.get_subtitle_lang(
                    src_sub_streams, job.src_sub_track_id
                )

                # Limit user input to one of the streams shown
                Stream.show_streams(dst_aud_streams)
                job.dst_aud_track_id = str(
                    cu.get_choice(
                        end=Stream.get_last_id(dst_aud_streams),
                        prompt="Select a destination audio stream: ",
                    )
                )

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

            if job.src_aud_track_id is not None:
                print(f"{cu.fore.LIGHTMAGENTA_EX}Source Audio Track ID: {job.src_aud_track_id}")

            if job.src_sub_track_id is not None:
                print( f"{cu.fore.LIGHTCYAN_EX}Source Subtitle Track ID: {job.src_sub_track_id}")

            if job.dst_aud_track_id is not None:
                print(f"{cu.fore.YELLOW}Destination Audio Track ID: {job.dst_aud_track_id}")

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
