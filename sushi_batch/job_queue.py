import json
from os import path

from . import console_utils as cu
from . import settings
from .enums import Status, Task, JobSelection
from .json_hooks import JobDecoder, JobEncoder
from .mkv_merge import MKVMerge
from .streams import Stream
from .sub_sync import Sushi
from .sub_resample import SubResampler


class JobQueue:
    def __init__(self, contents=[]):
        self.contents = contents
        self.file_path = path.join(settings.config.data_path, "queue_data.json")

    def save(self):
        """Save queue contents to JSON file"""
        with open(self.file_path, "w", encoding="utf-8") as data_file:
            json.dump(self.contents, data_file, cls=JobEncoder, indent=4)

    def load(self):
        """Load queue contents from JSON file"""
        if path.exists(self.file_path):
            with open(self.file_path, "r", encoding="utf-8") as data_file:
                self.contents = json.load(data_file, cls=JobDecoder)

    def add_jobs(self, selected_jobs_indexes, unqueued_jobs, task):
        """Add selected jobs to queue"""
        jobs_to_queue = (
            unqueued_jobs.copy()
            if selected_jobs_indexes == JobSelection.ALL
            else [unqueued_jobs[job_idx - 1] for job_idx in selected_jobs_indexes]
        )

        if task in (Task.VIDEO_SYNC_DIR, Task.VIDEO_SYNC_FIL):
            self._set_video_job_indexes(jobs_to_queue)

        self.contents.extend(jobs_to_queue)
        self.save()

    def _set_video_job_indexes(self, jobs_to_queue):
        """Set audio and subtitle track indexes for video sync jobs"""
        if cu.confirm_action("\nSpecify audio and sub track indexes for job(s)? (Y/N): "):
            self._set_stream_indexes(jobs_to_queue)
        else:
            for job in jobs_to_queue:
                indexes = self._get_stream_indexes(job, False)
                job.__dict__.update(indexes)

    def remove_jobs(self, selected_jobs_indexes):
        """Remove selected jobs from queue"""
        self.contents = [
            job
            for idx, job in enumerate(self.contents, start=1)
            if idx not in selected_jobs_indexes
        ]
        self.save()

    def run_jobs(self, selected_jobs_indexes):
        """ Run jobs selected by user"""
        if selected_jobs_indexes == JobSelection.ALL:
            jobs_to_run = [job for job in self.contents if job.status == Status.PENDING]
        else:
            jobs_to_run = [
                self.contents[job_idx - 1]
                for job_idx in selected_jobs_indexes
                if self.contents[job_idx - 1].status == Status.PENDING
            ]

        if not jobs_to_run:
            cu.print_error("\nNo pending jobs to run!") 
            return

        cu.print_subheader("Running jobs")           
        for job in jobs_to_run:
            Sushi.run(job)
            self.save() 

        contains_video_tasks = any(job.task in (Task.VIDEO_SYNC_DIR, Task.VIDEO_SYNC_FIL) for job in jobs_to_run)

        if settings.config.merge_files_after_execution and contains_video_tasks:
            if MKVMerge.is_installed:
                self.merge_completed_video_tasks(jobs_to_run)
            else:
                cu.print_error("\nMKVMerge could not be found. Video files cannot be merged.")

    def merge_completed_video_tasks(self, job_list):
        """ Generate a new video file from completed video tasks """
        completed_jobs = [
            job for job in job_list
            if job.status == Status.COMPLETED 
            and job.task in (Task.VIDEO_SYNC_DIR, Task.VIDEO_SYNC_FIL)
            and not job.merged
        ]

        if not completed_jobs:
            cu.print_error("No completed jobs to merge!")
            return

        cu.print_subheader("Merging files")

        can_resample = settings.config.resample_subs_on_merge

        if can_resample and not SubResampler.is_installed:
            cu.print_error("Aegisub-CLI could not be found. Subtitle resampling is disabled.")

        for job in completed_jobs:
            if can_resample and SubResampler.is_installed:
                resample_result = SubResampler.run(job)
                MKVMerge.run(job, use_resampled_sub=resample_result)
                if not resample_result:
                    print(f"{cu.fore.LIGHTYELLOW_EX}Subtitle could not be resampled. Merged synced subtitle instead.")
            else:
                MKVMerge.run(job)
            self.save()

        input("\nPress Enter to go back... ")

    def clear(self):
        """ Clear queue contents """
        self.contents.clear()
        self.save()

    def clear_completed_jobs(self):
        """ Clear completed and failed jobs from queue """
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

    def select_jobs(self, prompt):
        """ Select jobs from queue based on user input """
        user_input = input(f"\n{cu.fore.LIGHTBLACK_EX}{prompt}")
        selected_jobs_indexes = user_input.replace(" ", "").split(",")

        valid_job_indexes = []
        job_list_range = range(1, len(self.contents) + 1)

        for idx in selected_jobs_indexes:
            if idx.isnumeric():
                job_index = int(idx)
                if job_index in job_list_range:
                    valid_job_indexes.append(job_index)

            # Check if item is a range of jobs (e.g., "15-20")
            elif "-" in idx:
                start, end = map(int, idx.split("-"))
                for job_index in range(start, end + 1):
                    if job_index in job_list_range:
                        valid_job_indexes.append(job_index)

        if valid_job_indexes:
            valid_job_indexes.sort()
            print(f"{cu.fore.LIGHTYELLOW_EX}Selected jobs: {valid_job_indexes}\n")
            return valid_job_indexes
        else:
            cu.print_error("Invalid choice! Please select valid jobs.")
            return None

    def _get_stream_choice(self, streams, prompt):
        """"Get user-selected stream from list"""
        Stream.show_streams(streams)
        stream_choice = cu.get_choice(int(streams[0].id), int(streams[-1].id), prompt)
        return next(stream for stream in streams if int(stream.id) == stream_choice)

    def _get_stream_indexes(self, job, select_streams):
        """"Get source and destination media stream indexes"""
        src_aud_streams = Stream.get_streams(job.src_file, "audio")
        src_sub_streams = Stream.get_streams(job.src_file, "subtitle")
        dst_aud_streams = Stream.get_streams(job.dst_file, "audio")

        if select_streams:
            print(f"{cu.fore.LIGHTYELLOW_EX}\nJob {job.idx}")

        def _select_stream(streams, prompt):
            return self._get_stream_choice(streams, prompt) if select_streams else streams[0]

        src_aud_selected = _select_stream(src_aud_streams, "Select a source audio stream: ")
        src_sub_selected = _select_stream(src_sub_streams, "Select a source subtitle stream: ")
        dst_aud_selected = _select_stream(dst_aud_streams, "Select a destination audio stream: ")
        streams_info = {
            "src_aud_id": src_aud_selected.id,
            "src_aud_display": src_aud_selected.display_name,
            "dst_aud_id": dst_aud_selected.id,
            "dst_aud_display": dst_aud_selected.display_name,
            "src_sub_id": src_sub_selected.id,
            "src_sub_display": src_sub_selected.display_name,
            "src_sub_lang": Stream.get_stream_lang(src_sub_streams, src_sub_selected.id),
            "src_sub_name": Stream.get_stream_name(src_sub_streams, src_sub_selected.id),
        }
        return streams_info

    def _set_stream_indexes(self, unqueued_jobs):
        """"Set audio and subtitle track indexes for video sync jobs"""
        if len(unqueued_jobs) > 1 and cu.confirm_action("\nSet default stream index for all jobs? (Y/N): "):
            default_indexes = self._get_stream_indexes(unqueued_jobs[0], True) # Use first job as reference
            for job in unqueued_jobs:
                job.__dict__.update(default_indexes)
        else:
            for job in unqueued_jobs:
                indexes = self._get_stream_indexes(job, True)
                job.__dict__.update(indexes)

    def show(self, task):
        """ Show Job List contents """
        cu.clear_screen()

        title = "Job Queue" if task == Task.JOB_QUEUE else "Jobs"
        cu.print_header(f"{title}")

        for job in self.contents:
            job.idx = self.contents.index(job) + 1
            print(f"\n{cu.fore.LIGHTBLACK_EX}Job {job.idx}")
            print(f"{cu.fore.LIGHTBLUE_EX}Source file: {job.src_file}")
            print(f"{cu.fore.LIGHTYELLOW_EX}Destination file: {job.dst_file}")

            if job.sub_file is not None:
                print(f"{cu.fore.LIGHTCYAN_EX }Subtitle file: {job.sub_file}")

            if job.src_aud_display is not None:
                print(f"{cu.fore.LIGHTMAGENTA_EX}Source Audio Track: {job.src_aud_display}")

            if job.src_sub_display is not None:
                print(f"{cu.fore.LIGHTCYAN_EX}Source Subtitle Track: {job.src_sub_display}")

            if job.dst_aud_display is not None:
                print(f"{cu.fore.YELLOW}Destination Audio Track: {job.dst_aud_display}")

            if job.src_aud_id is not None and job.src_aud_display is None:
                print(f"{cu.fore.LIGHTMAGENTA_EX}Source Audio Track ID: {job.src_aud_id}")

            if job.src_sub_id is not None and job.src_sub_display is None:
                print(f"{cu.fore.LIGHTCYAN_EX}Source Subtitle Track ID: {job.src_sub_id}")

            if job.dst_aud_id is not None and job.dst_aud_display is None:
                print(f"{cu.fore.YELLOW}Destination Audio Track ID: {job.dst_aud_id}")

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
