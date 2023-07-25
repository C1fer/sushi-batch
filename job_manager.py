import sub_sync
import console_utils as cu


# Initialize queue with sublists:
# Source files, Destination files, Subtitle files, Tasks, Audio ID, Sub ID,
job_queue = [[], [], [], [], [], []]


# Show Job Queue
def show_job_queue(job_list=job_queue, task="job-queue"):
    if task == "job-queue":
        print(f"{cu.fore.LIGHTMAGENTA_EX}Job Queue")

    # Zip iterables and get the number of the iteration
    for idx, (src, dst, sub, _, aud_id, sub_id) in enumerate(zip(*job_list), start=1):
        print(f"\n{cu.fore.LIGHTBLACK_EX}Job {idx}")
        print(f"{cu.fore.LIGHTBLUE_EX}Source file: {src}")
        print(f"{cu.fore.LIGHTYELLOW_EX}Destination file: {dst}")

        # Don't show values if None
        if sub is not None:
            print(f"{cu.fore.LIGHTRED_EX}Subtitle file: {sub}")

        if aud_id is not None:
            print(f"{cu.fore.LIGHTWHITE_EX}Audio Track ID: {aud_id}")

        if sub_id is not None:
            print(f"{cu.fore.LIGHTGREEN_EX}Subtitle Track ID: {sub_id}")

    # Show queue options
    handle_queue_options(job_list, task)


# Handle queue options
def handle_queue_options(job_list, task):
    while True:
        # Show options based on current task
        if task == "job-queue":
            print("\n1) Run queue \n2) Remove job fom queue \n3) Return to main menu")
        else:
            print("\n1) Add job(s) to queue \n2) Run Job(s) \n3) Return to main menu")

        # Get and confirm selected option
        choice = cu.get_choice(range(1, 4))

        if cu.confirm_action():
            match choice:
                case 1:
                    # Run Queue
                    if task == "job-queue":
                        sub_sync.shift_subs(job_list)
                        clear_job_queue()
                    # Add Jobs
                    else:
                        add_jobs(job_list, task)
                    break
                case 2:
                    # Remove Jobs
                    if task == "job-queue":
                        remove_jobs()
                    # Run jobs
                    else:
                        set_tracks_id(job_list, task)
                        sub_sync.shift_subs(job_list)
                    break
                case 3:
                    # Clear Job  Queue
                    if task == "job-queue":
                        clear_job_queue()
                    cu.clear_screen()
                    break
                case others:
                    # Return to main menu
                    cu.clear_screen()
                    break


# Add selected jobs to queue
def add_jobs(job_list, task):
    # Get job list length
    jbl_len = len(job_list[0])

    # Skip jobs selection if list contains only one job
    if jbl_len == 1:
        jobs_to_add = [1]
        confirm = True
    else:
        choice = input("Select jobs to add to the queue (e.g: 'all' or '1, 5-10'): ")
        # Add all jobs to queue 
        if choice == "all":
            jobs_to_add = list(range(1, jbl_len + 1))
            confirm = True
        else:
            # Validate job indexes entered by user
            jobs_to_add = validate_selected_jobs(choice, job_list)
            confirm = cu.confirm_action()

    # Add selected jobs to queue if list is not empty
    if jobs_to_add is not None and confirm:
        # Set audio and subtitle track id
        set_tracks_id(job_list, task)
        for job_idx in sorted(jobs_to_add): # Add jobs in the order they were presented to user
            for item in range(6):
                job_queue[item].append(job_list[item][job_idx - 1])
        cu.clear_screen()
        print(f"{cu.fore.LIGHTGREEN_EX}{len(jobs_to_add)} job(s) added to queue.")


# Remove selected jobs from queue
def remove_jobs():
    choice = input("Select jobs to remove from the queue (e.g: 1, 5-10): ")
    jobs_to_remove = validate_selected_jobs(choice, job_list)

    if jobs_to_remove is not None and cu.confirm_action():
        # Remove jobs from queue in reverse order to avoid out of bound error 
        for job_idx in sorted(jobs_to_remove, reverse=True):
            for item in range(6):
                # Reduce input index by 1 to match real queue index
                job_queue[item].pop(job_idx - 1)
        cu.clear_screen()  
        print(f"{cu.fore.LIGHTGREEN_EX}{len(jobs_to_remove)} job(s) removed from queue.")


# Validate jobs selected by user
def validate_selected_jobs(user_input, job_list=job_queue):
    valid_job_indexes = []
    selected_jobs = user_input.replace(" ", "").split(",")  # Split user input into list elements
    job_list_range = range(len(job_list[0]) + 1)            # Store job queue length for validations

    for job in selected_jobs:
        # Check if item is a number
        if job.isnumeric():
            job_index = int(job)
            # Decrease index by 1 to match real queue index
            if job_index - 1 in job_list_range:  
                valid_job_indexes.append(job_index)

        else:
            # Check if element is a range of jobs (e.g., "15-20")
            if "-" in job:
                start, end = map(int, job.split("-"))
                # Increase end index by 1 to match range max number
                for job_index in range(start, end + 1):
                    if job_index in job_list_range:
                        valid_job_indexes.append(job_index)

    # Return valid indexes list if not empty
    if not valid_job_indexes:
        print(f"{cu.fore.LIGHTRED_EX}Invalid choice! Please select valid jobs.")
        return None
    else:
        print(f"Selected jobs: {valid_job_indexes}")
        return valid_job_indexes


# Clear queue sublists
def clear_job_queue():
    for item in job_queue:
        item.clear()


# Set custom track id for re-synchronization process
def set_tracks_id(job_list, task):
    # Ask for user to enter track index
    def get_track_id(prompt):
        track_id = int(input(prompt))
        return track_id

    audio_tracks_id = []
    sub_tracks_id = []
    jbl_len = len(job_list[0])

    # Ask if the user wants to set custom track indexes
    if task in ("vid-sync-dir", "vid-sync-fil") and cu.confirm_action("Set custom audio and subtitle track for source file(s)? (Y/N): "):
        # Clear sub-lists before setting track indexes
        job_list.pop(5)
        job_list.pop(4)
        # Allow setting default track indexes only if job list contains more than one job
        if jbl_len > 1 and cu.confirm_action("Set default audio and subtitle Track ID for all source files? (Y/N): "):
            src_audio_id = get_track_id("Audio Track ID: ")
            src_sub_id = get_track_id("Subtitle Track ID: ")
            # Store entered mode in all jobs
            audio_tracks_id.extend([src_audio_id] * jbl_len)
            sub_tracks_id.extend([src_sub_id] * jbl_len)
        else:
            # Set track indexes for every job
            for idx in range(jbl_len):
                print(f"{cu.fore.LIGHTBLUE_EX}Source file: {job_list[0][idx]}")
                src_audio_id = get_track_id("Audio Track ID: ")
                src_sub_id = get_track_id("Subtitle Track ID: ")
                audio_tracks_id.append(src_audio_id)
                sub_tracks_id.append(src_sub_id)
        # Insert new track indexes into sub-lists
        job_list.append(audio_tracks_id)
        job_list.append(sub_tracks_id)
