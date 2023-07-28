import sub_sync
import console_utils as cu


# Initialize queue with sublists: Source files, Destination files, Subtitle files, Tasks, Audio ID, Sub ID
job_queue = [[], [], [], [], [], []]


# Show Job Queue
def show_job_queue(job_list=job_queue, task="job-queue"):
    cu.clear_screen() # Clear command line output before showing jobs

    if task == "job-queue":
        print(f"{cu.fore.LIGHTCYAN_EX}Job Queue")

    # Zip iterables and get the number of the iteration
    for idx, (src, dst, sub, _, aud_id, sub_id) in enumerate(zip(*job_list), start=1):
        print(f"\n{cu.fore.LIGHTBLACK_EX}Job {idx}")
        print(f"{cu.fore.LIGHTBLUE_EX}Source file: {src}")
        print(f"{cu.fore.LIGHTYELLOW_EX}Destination file: {dst}")

        # Don't show values if None
        if sub is not None:
            print(f"{cu.fore.LIGHTRED_EX}Subtitle file: {sub}")

        if aud_id is not None:
            print(f"{cu.fore.LIGHTMAGENTA_EX}Audio Track ID: {aud_id}")

        if sub_id is not None:
            print(f"{cu.fore.LIGHTGREEN_EX}Subtitle Track ID: {sub_id}")

    # Show queue options
    handle_queue_options(job_list, task)


# Handle queue options
def handle_queue_options(job_list, task):
    while True:
        # Show options based on current task
        if task == "job-queue":
            print("\n1) Start queue \n2) Run selected jobs \n3) Remove selected jobs \n4) Clear queue \n5) Return to main menu")
        else:
            print("\n1) Run all jobs \n2) Run selected jobs \n3) Add jobs to queue \n4) Return to main menu")

        # Get and confirm selected option (limit choice to range 1-5)
        choice = cu.get_choice(range(1, 6))

        # Clear output and show job queue if option is not confirmed
        if not cu.confirm_action():
            show_job_queue(job_list,task)
    
        # Handle user-selected options
        match choice:
            case 1:
                sub_sync.shift_subs(job_list)
                # Don't clear job list if running jobs without adding to queue
                if task == "job-queue":
                    clear_job_queue()
            case 2:
                run_selected_jobs(job_list, task)
            case 3:
                if task == "job-queue":
                    choice = input(f"{cu.fore.LIGHTBLACK_EX}Select jobs to remove from the queue (e.g: 1, 5-10): ")
                    jobs_to_remove = validate_selected_jobs(choice, job_list)
                    if jobs_to_remove is not None and cu.confirm_action():
                        remove_jobs_queue(jobs_to_remove)
                else:
                    add_jobs_queue(job_list, task) 
            case 4:
                if task == "job-queue":
                    clear_job_queue()
                cu.clear_screen() 
            case others:
                cu.clear_screen()
        break


# Run user-selected jobs
def run_selected_jobs(job_list, task):
    jobs_to_run = [[],[],[],[],[],[]]
    choice = input(f"{cu.fore.LIGHTBLACK_EX}Select jobs to run (e.g: 1, 5-10): ")
    selected_jobs = validate_selected_jobs(choice, job_list)
    if selected_jobs is not None and cu.confirm_action():
        for job_idx in sorted(selected_jobs):
            for item in range(6):
                jobs_to_run[item].append(job_list[item][job_idx - 1])
        sub_sync.shift_subs(jobs_to_run)
        # Remove selected jobs from queue
        if task == "job-queue":
            remove_jobs_queue(selected_jobs)


# Add selected jobs to queue
def add_jobs_queue(job_list, task):
    # Get length of job list
    jbl_len = len(job_list[0])

    # Skip job selection if list contains only one job
    if jbl_len == 1:
        jobs_to_add = [1]
        confirm = True
    else:
        choice = input(f"{cu.fore.LIGHTBLACK_EX}Select jobs to add to the queue (e.g: 'all' or '1, 5-10'): ")
        if choice == "all": 
            jobs_to_add = list(range(1, jbl_len + 1)) # Add all jobs to queue 
        else:
            jobs_to_add = validate_selected_jobs(choice, job_list) # Validate job indexes entered by user
        confirm = cu.confirm_action()

    # Add selected jobs to queue if list is not empty
    if jobs_to_add is not None and confirm:
        set_tracks_id(job_list, task)  # Set audio and subtitle track id
        for job_idx in sorted(jobs_to_add): # Add jobs to queue in the order they were presented to user
            for item in range(6):
                job_queue[item].append(job_list[item][job_idx - 1])
        cu.clear_screen()
        return print(f"{cu.fore.LIGHTGREEN_EX}{len(jobs_to_add)} job(s) added to queue.")
    else:
        show_job_queue(job_list,task)


# Remove selected jobs from queue
def remove_jobs_queue(jobs_to_remove):
    # Remove jobs from queue in reverse order to avoid out of bounds error 
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
        print(f"{cu.fore.LIGHTYELLOW_EX}Selected jobs: {valid_job_indexes}")
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

    # Allow setting custom track indexes
    if task in ("vid-sync-dir", "vid-sync-fil") and cu.confirm_action("Set custom audio and subtitle track for source file(s)? (Y/N): "):
        # Remove sublists filled with None before setting track indexes
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
