import sub_sync
import console_utils as cu
import job

# Initialize empty queue
job_queue = []


# Show Job List
def show_job_list(job_list=job_queue, task="job-queue"):
    # Clear command line output before showing jobs
    cu.clear_screen()

    if task == "job-queue":
        print(f"{cu.fore.LIGHTCYAN_EX}Job Queue")
    else:
        print(f"{cu.fore.LIGHTCYAN_EX}Job Details")

    # Enumerate job list and get the number of the iteration
    for idx, (job) in enumerate(job_list, start=1):
        print(f"\n{cu.fore.LIGHTBLACK_EX}Job {idx}")
        print(f"{cu.fore.LIGHTBLUE_EX}Source file: {job.src_file}")
        print(f"{cu.fore.LIGHTYELLOW_EX}Destination file: {job.dst_file}")

        # Don't show field if value is None
        if job.sub_file is not None:
            print(f"{cu.fore.LIGHTCYAN_EX }Subtitle file: {job.sub_file}")

        if job.src_aud_track_id is not None:
            print(f"{cu.fore.LIGHTMAGENTA_EX}Audio Track ID: {job.src_aud_track_id}")

        if job.src_sub_track_id is not None:
            print(f"{cu.fore.LIGHTCYAN_EX}Subtitle Track ID: {job.src_sub_track_id}")

        if task == "job-queue":
            match job.status:
                case "Pending":
                    print(f"{cu.fore.LIGHTBLACK_EX}Status: Pending")
                case "Completed":
                    print(f"{cu.fore.LIGHTGREEN_EX}Status: Completed") 
                case "Failed":
                    print(f"{cu.fore.LIGHTRED_EX}Status: Status: Failed") 
                    print(f"{cu.fore.LIGHTRED_EX}Status: Error: {job.error_message}") 
                case other:
                    print(job.status)
        
    if task == "job-queue":
        handle_queue_options(task) # Show queue options
    else:
        handle_details_options(job_list, task) # Show queue options
    

# Handle queue options
def handle_queue_options(task):
    while True:
        # Show options based on current task
        print("\n1) Start queue \n2) Run selected jobs \n3) Remove selected jobs \n4) Clear queue \n5) Clear completed and failed jobs \n6) Return to main menu")

        # Get and confirm selected option (limit choice to range 1-5)
        choice = cu.get_choice(range(1, 6))

        # Clear output and show job queue if option is not confirmed
        if not cu.confirm_action():
            show_job_list()
    
        # Handle user-selected options
        match choice:
            case 1:
                # Run all pending jobs on queue
                sub_sync.shift_subs(job_queue)
            case 2:
                 # Run selected jobs
                selected_jobs = select_jobs("Select jobs to run (e.g: 1, 5-10): ", job_queue)
                if selected_jobs is not None and cu.confirm_action():
                    run_selected_jobs(selected_jobs, job_queue)
            case 3:
                # Remove selected jobs from queue
                selected_jobs = select_jobs("Select jobs to remove from queue (e.g: 1, 5-10): ", job_queue)
                if selected_jobs is not None and cu.confirm_action():
                    remove_jobs_queue(selected_jobs)
                    cu.clear_screen()  
                    print(f"{cu.fore.LIGHTGREEN_EX}{len(selected_jobs)} job(s) removed from queue.")
            case 4:
                # Clear queue
                job_queue.clear()
                cu.clear_screen() 
                print(f"{cu.fore.LIGHTGREEN_EX}Queue cleared.")
            case 5:
                # Remove failed and completed jobs from queue
                jobs_to_remove = []
                for idx, (job) in enumerate(job_queue, start=1):
                    # Add job to list if status is not Pending
                    if job.status != "Pending": 
                       jobs_to_remove.append(idx)
                remove_jobs_queue(jobs_to_remove)
            case others:
                cu.clear_screen()
        break


# Handle queue options
def handle_details_options(jobs_detail, task):
    while True:
        # Show options based on current task
        print("\n1) Run all jobs \n2) Run selected jobs \n3) Add all jobs to queue \n4) Add selected jobs to queue \n5) Return to main menu")

        # Get and confirm selected option (limit choice to range 1-5)
        choice = cu.get_choice(range(1, 5))

        # Clear output and show job queue if option is not confirmed
        if not cu.confirm_action():
            show_job_list(jobs_detail,task)
    
        # Handle user-selected options
        match choice:
            case 1:
                # Queue all jobs and start automatically
                add_jobs_queue("all", jobs_detail, task)
                sub_sync.shift_subs(jobs_detail)
            case 2:
                # Queue selected jobs and start automatically
                selected_jobs = select_jobs("Select jobs to run (e.g: 1, 5-10): ", jobs_detail)
                if selected_jobs is not None and cu.confirm_action():
                    add_jobs_queue(selected_jobs, jobs_detail, task)
                    run_selected_jobs(selected_jobs, jobs_detail)
            case 3:
                # Queue all jobs without starting them
                add_jobs_queue("all", jobs_detail, task)
                print(f"{cu.fore.LIGHTGREEN_EX}{len(jobs_detail)} job(s) added to queue.")
            case 4:
                # Queue selected jobs without starting them
                selected_jobs = select_jobs("Select jobs to add to the queue (e.g: all OR 1, 5-10): ", jobs_detail)
                if selected_jobs is not None and cu.confirm_action():
                    add_jobs_queue(selected_jobs, jobs_detail, task)
                    cu.clear_screen()
                    print(f"{cu.fore.LIGHTGREEN_EX}{len(selected_jobs)} job(s) added to queue.")
            case others:
                cu.clear_screen()
        break


# Run user-selected jobs
def run_selected_jobs(selected_jobs_idx, job_list):
    jobs_to_run = []
    # Add selected jobs to a new list
    for job_idx in selected_jobs_idx:
        jobs_to_run.append(job_list[job_idx - 1]) # Decrease job index by 1 to match real queue index
    sub_sync.shift_subs(jobs_to_run)


# Add selected jobs to queue
def add_jobs_queue(selected_jobs, jobs_detail, task):
    # Set audio and subtitle track id for video-sync tasks
    if task in ("vid-sync-dir", "vid-sync-fil"):
        if cu.confirm_action("Set custom audio and subtitle track for source file(s)? (Y/N): "):
            set_tracks_id(jobs_detail, task)
    # Queue all jobs
    if selected_jobs == "all":
        job_queue.extend(jobs_detail)
    # Queue jobs selected by user
    else:
        for job_idx in selected_jobs: 
            job = jobs_detail[job_idx - 1]
            job_queue.append(job)
    

# Remove selected jobs from queue
def remove_jobs_queue(selected_jobs_idx):
    # Remove jobs from queue in reverse order to avoid out of bounds error 
    print("")
    for job_idx in sorted(selected_jobs_idx, reverse=True):
        del job_queue[job_idx - 1] # Delete job object (decrease index by 1 to match real queue index)


# Select and validate jobs selected by user
def select_jobs(prompt, job_list):
    # Ask for user input
    user_input = input(f"{cu.fore.LIGHTBLACK_EX}{prompt}")
    selected_jobs_idx = user_input.replace(" ", "").split(",") 

    # Store job queue length for validations
    valid_job_indexes = []
    job_list_range = range(len(job_list) + 1)    

    for job in selected_jobs_idx:
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
        cu.print_error("Invalid choice! Please select valid jobs.")
        return None
    else:
        valid_job_indexes.sort() # Sort indexes
        print(f"{cu.fore.LIGHTYELLOW_EX}Selected jobs: {valid_job_indexes}")
        return valid_job_indexes


# Set custom track id for re-synchronization process
def set_tracks_id(job_list, task):
    # Ask for user to input track index
    def get_track_id(prompt):
        while True: 
            track_id = input(prompt)
            if track_id.isnumeric():
                return track_id
            cu.print_error("Please input a number!")

    jbl_len = len(job_list)

    # Allow setting default track indexes only if job list contains more than one job
    if jbl_len > 1 and cu.confirm_action("Set default audio and subtitle Track ID for all source files? (Y/N): "):
        src_audio_id = get_track_id("Audio Track ID: ")
        src_sub_id = get_track_id("Subtitle Track ID: ")
        for job in job_list:
            job.src_aud_track_id = src_audio_id
            job.src_sub_track_id = src_sub_id
    else:
        # Set track indexes per job
        for job in job_list:
            print(f"{cu.fore.LIGHTBLUE_EX}Source file: {job.src_file}")
            job.src_aud_track_id = get_track_id("Audio Track ID: ")
            job.src_sub_track_id = get_track_id("Subtitle Track ID: ")
            

# jobs=[]

# # TEST SETUP
# job1 = job.Job('C:\\Users\\rusbe\\Documents\\Test\\audio_src\\[QaS] Fullmetal Alchemist Brotherhood - 01 [BD 1080p HEVC x265 10bit Opus 5.1][Dual Audio]_track3_[jpn]_DELAY 0ms.opus', 'C:\\Users\\rusbe\\Documents\\Test\\audio_dst\\FMA - 01_track2_[jpn]_DELAY 0ms.flac', 'C:\\Users\\rusbe\\Documents\\Test\\audio_src\\[QaS] Fullmetal Alchemist Brotherhood - 01 [BD 1080p HEVC x265 10bit Opus 5.1][Dual Audio]_track6_[eng].ass','aud-sync-dir')
# job2 = job.Job('C:\\Users\\rusbe\\Documents\\Test\\audio_src\\[QaS] Fullmetal Alchemist Brotherhood - 02 [BD 1080p HEVC x265 10bit Opus 5.1][Dual Audio]_track3_[jpn]_DELAY 0ms.opus','C:\\Users\\rusbe\\Documents\\Test\\audio_dst\\FMA - 02_track2_[jpn]_DELAY 0ms.flac', 'C:\\Users\\rusbe\\Documents\\Test\\audio_src\\[QaS] Fullmetal Alchemist Brotherhood - 02 [BD 1080p HEVC x265 10bit Opus 5.1][Dual Audio]_track5_[eng].ass', 'aud-sync-dir')
# corrError = job.Job('C:\\Users\\rusbe\\Documents\\Test\\audio_src\\[QaS] Fullmetal Alchemist Brotherhood - 39 [BD 1080p HEVC x265 10bit Opus 5.1][Dual Audio]_track3_[jpn]_DELAY 0ms.opus','C:\\Users\\rusbe\\Documents\\Test\\audio_dst\\FMA - 39_track2_[jpn]_DELAY 0ms.flac','', 'aud-sync-dir')


# vid_task1 = job.Job('C:\\Users\\rusbe\\Documents\\Test\\wx2\\FMA - 39 QaS.mkv', 'C:\\Users\\rusbe\\Documents\\Test\\wx\\FMA - 39 VCB.mkv', None, 'vid-sync-fil')
# jobs.append(vid_task1)
# # # job_queue.append(job1)
# # # job_queue.append(corrError)
# # # job_queue.append(job2)

# # # jobs = job_queue

# # # #TEST
# show_job_list(jobs, 'vid-sync-fil')
# show_job_list()