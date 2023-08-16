import sub_sync
import console_utils as cu
import job

# Initialize queue with sublists: Source files, Destination files, Subtitle files, Tasks, Audio ID, Sub ID
job_queue = []


# Show Job Queue
def show_job_queue(job_list=job_queue, task="job-queue"):
    # Clear command line output before showing jobs
    cu.clear_screen()

    if task == "job-queue":
        print(f"{cu.fore.LIGHTCYAN_EX}Job Queue")

    # Zip iterables and get the number of the iteration
    for idx, (job) in enumerate(job_list, start=1):
        print(f"\n{cu.fore.LIGHTBLACK_EX}Job {idx}")
        print(f"{cu.fore.LIGHTBLUE_EX}Source file: {job.src_file}")
        print(f"{cu.fore.LIGHTYELLOW_EX}Destination file: {job.dst_file}")

        # Don't show values if None
        if job.sub_file is not None:
            print(f"{cu.fore.LIGHTCYAN_EX }Subtitle file: {job.sub_file}")

        if job.aud_track_id is not None:
            print(f"{cu.fore.LIGHTMAGENTA_EX}Audio Track ID: {job.aud_track_id}")

        if job.sub_track_id is not None:
            print(f"{cu.fore.LIGHTCYAN_EX}Subtitle Track ID: {job.sub_track_id}")

        if task == "job-queue":
            match job.status:
                case "Pending":
                    print(f"{cu.fore.LIGHTBLACK_EX}Status: Not Started")
                case "Completed":
                    print(f"{cu.fore.LIGHTGREEN_EX}Status: Completed") 
                case "Failed":
                    print(f"{cu.fore.LIGHTRED_EX}Status: Failed")
                    print(f"{cu.fore.LIGHTRED_EX}Error: {job.error_message}")
                case other:
                    print(job.status)

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
                # if task == "job-queue":
                #     clear_job_queue()
            case 2:
                run_selected_jobs(job_list, task)
            case 3:
                if task == "job-queue":
                    choice = input(f"{cu.fore.LIGHTBLACK_EX}Select jobs to remove from the queue (e.g: 1, 5-10): ")
                    jobs_to_remove = validate_selected_jobs(choice, job_list)
                    if jobs_to_remove is not None and cu.confirm_action():
                        remove_jobs_queue(jobs_to_remove)
                        cu.clear_screen()  
                        print(f"{cu.fore.LIGHTGREEN_EX}{len(jobs_to_remove)} job(s) removed from queue.")
                else:
                    add_jobs_queue(job_list, task) 
            case 4:
                if task == "job-queue":
                   job_queue.clear()
                cu.clear_screen() 
            case others:
                cu.clear_screen()
        break


# Run user-selected jobs
def run_selected_jobs(job_list, task):
    jobs_to_run = []
    choice = input(f"{cu.fore.LIGHTBLACK_EX}Select jobs to run (e.g: 1, 5-10): ")
    selected_jobs = validate_selected_jobs(choice, job_list)
     
    if selected_jobs is not None and cu.confirm_action():
        for job_idx in selected_jobs:
            jobs_to_run.append(job_list[job_idx - 1]) # Decrease job index by 1 to match real queue index
        sub_sync.shift_subs(jobs_to_run)


# Add selected jobs to queue
def add_jobs_queue(job_list, task):
    # Get length of job list
    jbl_len = len(job_list)
    jobs_to_add = []

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
        confirm = cu.confirm_action() # Confirm selection

    # Add selected jobs to queue if list is not empty 
    if jobs_to_add is not None and confirm:
        set_tracks_id(job_list, task)  # Set audio and subtitle track id
        for job_idx in jobs_to_add: 
            job = job_list[job_idx - 1]
            job_queue.append(job)
        cu.clear_screen()
        return print(f"{cu.fore.LIGHTGREEN_EX}{len(jobs_to_add)} job(s) added to queue.")
    else:
        show_job_queue(job_list,task) # Reset job screen if user doesn't confirm the action


# Remove selected jobs from queue
def remove_jobs_queue(selected_jobs):
    # Remove jobs from queue in reverse order to avoid out of bounds error 
    for job_idx in sorted(selected_jobs, reverse=True):
        del job_queue[job_idx - 1] # Delete job object (decrease index by 1 to match real queue index)


# Validate jobs selected by user
def validate_selected_jobs(user_input, job_list=job_queue):
    valid_job_indexes = []
    selected_jobs = user_input.replace(" ", "").split(",")  # Split user input into list elements
    job_list_range = range(len(job_list) + 1)            # Store job queue length for validations

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
        valid_job_indexes.sort() # Sort indexes
        print(f"{cu.fore.LIGHTYELLOW_EX}Selected jobs: {valid_job_indexes}")
        return valid_job_indexes


# Set custom track id for re-synchronization process
def set_tracks_id(job_list, task):
    # Ask for user to enter track index
    def get_track_id(prompt):
        track_id = int(input(prompt))
        return track_id

    jbl_len = len(job_list)

    # Allow setting custom track indexes
    if task in ("vid-sync-dir", "vid-sync-fil") and cu.confirm_action("Set custom audio and subtitle track for source file(s)? (Y/N): "):
        # Allow setting default track indexes only if job list contains more than one job
        if jbl_len > 1 and cu.confirm_action("Set default audio and subtitle Track ID for all source files? (Y/N): "):
            src_audio_id = get_track_id("Audio Track ID: ")
            src_sub_id = get_track_id("Subtitle Track ID: ")
            for job in job_list:
                job.aud_track_id = src_audio_id
                job.sub_track_id = src_sub_id
        else:
            # Set track indexes per job
            for job in job_list:
                print(f"{cu.fore.LIGHTBLUE_EX}Source file: {job.src_file}")
                job.aud_track_id = get_track_id("Audio Track ID: ")
                job.sub_track_id = get_track_id("Subtitle Track ID: ")
                

