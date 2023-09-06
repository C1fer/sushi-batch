import time
from os import path
import json
import sub_sync
import console_utils as cu
import job
import streams
import queue_data as qd


# Initialize empty list
job_queue = []


# Show Job List
def show_jobs(job_list, task):
    # Show title based on current task

    title = "Job Queue" if task == "job-queue" else "Job Details"
    print(f"{cu.fore.LIGHTCYAN_EX}{title}")

    # Enumerate job list and get the number of the iteration
    for job in job_list:
        job.idx = job_list.index(job) + 1
        print(f"\n{cu.fore.LIGHTBLACK_EX}Job {job.idx}")
        print(f"{cu.fore.LIGHTBLUE_EX}Source file: {job.src_file}")
        print(f"{cu.fore.LIGHTYELLOW_EX}Destination file: {job.dst_file}")

        # Don't show field if value is None
        if job.sub_file is not None:
            print(f"{cu.fore.LIGHTCYAN_EX }Subtitle file: {job.sub_file}")

        if job.src_aud_track_id is not None:
            print(f"{cu.fore.LIGHTMAGENTA_EX}Source Audio Track ID: {job.src_aud_track_id}")

        if job.src_sub_track_id is not None:
            print(f"{cu.fore.LIGHTCYAN_EX}Source Subtitle Track ID: {job.src_sub_track_id}")
        
        if job.dst_aud_track_id is not None:
            print(f"{cu.fore.YELLOW}Destination Audio Track ID: {job.dst_aud_track_id}")

        if task == "job-queue":
            match job.status:
                case "Pending":
                    print(f"{cu.fore.LIGHTBLACK_EX}Status: Pending")
                case "Completed":
                    print(f"{cu.fore.LIGHTGREEN_EX}Status: Completed")
                    print(f"{cu.fore.GREEN}Average Shift: {job.result} sec")
                case "Failed":
                    print(f"{cu.fore.LIGHTRED_EX}Status: Failed")
                    print(f"{cu.fore.RED}Error: {job.result}")


# Handle queue options
def handle_queue_options():
    while True:
        # Show menu
        cu.clear_screen()
        show_jobs(job_queue, "job-queue")
        print("\n1) Start queue \n2) Run selected jobs \n3) Remove selected jobs \n4) Clear queue \n5) Clear completed and failed jobs \n6) Return to main menu")

        # Get and confirm selected options
        choice = cu.get_choice(range(1, 7))

        if cu.confirm_action():
            # Handle user-selected options
            match choice:
                case 1:
                    # Run all pending jobs on queue
                    run_selected_jobs("all", job_queue)
                case 2:
                    # Run selected jobs
                    selected_jobs = select_jobs(
                        "Select jobs to run (e.g: 1, 5-10): ", job_queue
                    )
                    if selected_jobs is not None and cu.confirm_action():
                        run_selected_jobs(selected_jobs, job_queue)
                case 3:
                    # Remove selected jobs from queue
                    selected_jobs = select_jobs(
                        "Select jobs to remove from queue (e.g: 1, 5-10): ", job_queue
                    )
                    if selected_jobs is not None and cu.confirm_action():
                        remove_jobs_queue(selected_jobs)
                        cu.print_success(f"{len(selected_jobs)} job(s) removed from queue.")
                        if len(job_queue) == 0:
                            break
                case 4:
                    # Clear queue and return to main menu
                    clear_queue()
                    break
                case 5:
                    # Remove jobs that dont have Pending status
                    clear_completed_jobs()
                    # Return to main menu if queue was cleared
                    if len(job_queue) == 0:
                        break
                case 6:
                    # Return to main menumenu
                    break


# Handle job details options
def handle_details_options(unqueued_jobs, task):
    while True:
        # Show menu
        cu.clear_screen()
        show_jobs(unqueued_jobs, task)
        print("\n1) Run all jobs \n2) Run selected jobs \n3) Add all jobs to queue \n4) Add selected jobs to queue \n5) Return to main menu")

        # Get and confirm selected option (limit choice to range 1-5)
        choice = cu.get_choice(range(1, 6))

        if cu.confirm_action():
            # Handle user-selected options
            match choice:
                case 1:
                    # Queue all jobs and start automatically
                    add_jobs_queue("all", unqueued_jobs, task)
                    run_selected_jobs("all", unqueued_jobs)
                    break
                case 2:
                    # Queue selected jobs and start automatically
                    selected_jobs = select_jobs("Select jobs to run (e.g: 1, 5-10): ", unqueued_jobs)
                    if selected_jobs is not None and cu.confirm_action():
                        add_jobs_queue(selected_jobs, unqueued_jobs, task)
                        run_selected_jobs(selected_jobs, unqueued_jobs)
                        break
                case 3:
                    # Queue all jobs without starting them
                    add_jobs_queue("all", unqueued_jobs, task)
                    cu.print_success(f"{len(unqueued_jobs)} job(s) added to queue.")
                    break
                case 4:
                    # Queue selected jobs without starting them
                    selected_jobs = select_jobs("Select jobs to add to the queue (e.g: all, 1, 5-10): ",unqueued_jobs,)
                    if selected_jobs is not None and cu.confirm_action():
                        add_jobs_queue(selected_jobs, unqueued_jobs, task)
                        cu.print_success(f"{len(selected_jobs)} job(s) added to queue.")
                        break
                case 5:
                    # Return to menu
                    cu.clear_screen()
                    break


# Run user-selected jobs
def run_selected_jobs(selected_jobs_indexes, job_list):
    # Separate confirmation prompt from spinners
    print("")

    # Run all jobs
    if selected_jobs_indexes == "all":
        jobs_to_run = job_list.copy()
    else:
        # Add selected jobs to a new list
        jobs_to_run = [job_list[job_idx - 1] for job_idx in selected_jobs_indexes]
    
    # Run sync on selected jobs
    sub_sync.shift_subs(jobs_to_run, job_queue)

    # Freeze thread to allow viewing job execution results
    time.sleep(1)


# Add selected jobs to queue
def add_jobs_queue(selected_jobs_indexes, unqueued_jobs, task):
    # Set audio and subtitle track id for video-sync tasks
    if task in ("vid-sync-dir", "vid-sync-fil"):
        if cu.confirm_action("\nSpecify audio and sub track indexes for job(s)? [If not, sushi will use the first audio and sub track found]  (Y/N): "):
            set_track_indexes(unqueued_jobs, task)

    # Queue all jobs
    if selected_jobs_indexes == "all":
        job_queue.extend(unqueued_jobs)
    else:
        # Queue jobs selected by user
        jobs_to_queue = [unqueued_jobs[job_idx - 1] for job_idx in selected_jobs_indexes]
        job_queue.extend(jobs_to_queue)

    # Update JSON data file
    qd.save_list_data(job_queue)


# Remove selected jobs from queue
def remove_jobs_queue(selected_jobs_indexes):
    # Remove jobs from queue in reverse order to avoid out of bounds error
    for job_idx in sorted(selected_jobs_indexes, reverse=True):
        del job_queue[job_idx - 1]  # Decrease index by 1 to match real queue index

    # Update JSON data file
    qd.save_list_data(job_queue)


# Remove jobs that dont have Pending status
def clear_completed_jobs():
    jobs_to_remove = [idx for idx, (job) in enumerate(job_queue, start=1) if job.status != "Pending"]

    if jobs_to_remove:
        remove_jobs_queue(jobs_to_remove)
        cu.print_success("Completed jobs cleared from queue.")
    else:
        cu.print_error("No completed jobs to clear!")


# Clear queue contents
def clear_queue():
    job_queue.clear()
    qd.save_list_data(job_queue)
    cu.print_success("Queue cleared.")


# Select and validate jobs selected by user
def select_jobs(prompt, job_list):
    # Ask for user input
    user_input = input(f"\n{cu.fore.LIGHTBLACK_EX}{prompt}")
    selected_jobs_indexes = user_input.replace(" ", "").split(",")

    # Store job queue length for validations
    valid_job_indexes = []
    job_list_range = range(1, len(job_list) + 1)

    for idx in selected_jobs_indexes:
        # Check if item is a number
        if idx.isnumeric():
            job_index = int(idx)
            # Add valid indexes list if found on range
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
        valid_job_indexes.sort()  # Sort indexes
        print(f"{cu.fore.LIGHTYELLOW_EX}Selected jobs: {valid_job_indexes}\n")
        return valid_job_indexes
    else:
        cu.print_error("Invalid choice! Please select valid jobs.")
        return None


# Get track index from user input
def get_track_id(prompt):
    while True:
        track_id = input(f"{cu.style_reset}{cu.fore.LIGHTBLACK_EX}{prompt}")
        if track_id.isnumeric():
            return track_id
        cu.print_error("Invalid index! Please input a number!", False)


# Set custom track indexes for 
def set_track_indexes(job_list, task):
    # Allow setting default track indexes only if job list contains more than one job
    if len(job_list) > 1 and cu.confirm_action("\nSet a default audio and sub track index for all jobs? [Only useful when all files have the same number of tracks] (Y/N): "):
        src_audio_id = get_track_id("\nSource Audio Track ID: ")
        src_sub_id = get_track_id("Source Subtitle Track ID: ")
        dst_audio_id = get_track_id("Destination Audio Track ID: ")
        for job in job_list:
            job.src_aud_track_id = src_audio_id
            job.src_sub_track_id = src_sub_id
            job.dst_aud_track_id = dst_audio_id
    else:
        # Set track indexes per job
        for job in job_list:
            print(f"\n{cu.fore.LIGHTBLACK_EX}Job {job.idx}")

            # Get source and destination media streams
            src_aud_streams, src_aud_indexes = streams.get_streams(job.src_file, "audio")
            src_sub_streams, src_sub_indexes = streams.get_streams(job.src_file, "sub")
            dst_aud_streams, dst_aud_indexes = streams.get_streams(job.dst_file, "audio")

            # Limit user input to one of the streams shown
            streams.show_streams(src_aud_streams, 'audio')
            job.src_aud_track_id = str(cu.get_choice(src_aud_indexes,"Select a source audio stream: "))

            # Limit user input to one of the streams shown
            streams.show_streams(src_sub_streams, 'sub')
            job.src_sub_track_id = str(cu.get_choice(src_sub_indexes, "Select a source subtitle stream: "))

            # Limit user input to one of the streams shown
            streams.show_streams(dst_aud_streams, 'audio')
            job.dst_aud_track_id= str(cu.get_choice(dst_aud_indexes,"Select a destination audio stream: "))
