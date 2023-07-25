from colorama import Fore
import os
import sub_sync
import console_utils as cu


# Initialize queue with values: source files dest files, sub files, tasks
job_queue = [[], [], [], []]


# Show Job Queue
def show_job_queue(job_list=job_queue, task="job-queue"):
    
    if task == "job-queue":
        print(f"{Fore.LIGHTMAGENTA_EX}Job Queue")

    # Zip iterables and get the number of the iteration
    for idx, (src, dst, sub, _) in enumerate(zip(*job_list), start=1):
        print(f"\n{Fore.LIGHTBLACK_EX}Job {idx}")
        print(f"{Fore.LIGHTBLUE_EX}Source file: {src}")
        print(f"{Fore.LIGHTYELLOW_EX}Destination file: {dst}")

        # Don't show subtitle if job is a video-sync task
        if sub != "":
            print(f"{Fore.LIGHTRED_EX}Subtitle file: {sub}")

    # Show queue options
    handle_queue_options(job_list, task)
        

# Handle queue options
def handle_queue_options(job_list, task):
    while True:
        if task == "job-queue":
            print("\n1) Run queue \n2) Remove job fom queue \n3) Return to main menu")
        else:
            print("\n1) Add job(s) to queue \n2) Run Job(s) \n3) Return to main menu")

        # Get and confirm selected option
        choice = cu.get_choice(range(1, 4))
        if not cu.confirm_action():
            break

        match choice:
            case 1:
                if task == "job-queue":
                    sub_sync.shift_subs(job_list)
                    clear_job_queue()
                else:
                    add_jobs(job_list)
                break
            case 2:
                if task == "job-queue":
                    remove_jobs()
                else:
                    sub_sync.shift_subs(job_list)
                break
            case others:
                cu.clear_screen()
                break


# Add jobs to queue
def add_jobs(job_list):
    
    # Skip jobs selection if list contains only one job
    if len(job_list[0]) == 1:
        jobs_to_add =  [1]
        confirm = True 
    else:
        jobs_to_add = validate_selected_jobs(input("Select jobs (e.g: 1, 5-10): "), job_list)
        confirm = cu.confirm_action()

    # Add selected jobs to queue if list is not empty
    if jobs_to_add is not None and confirm:
        for job_idx in sorted(jobs_to_add):
            for item in range(4):
                job_queue[item].append(job_list[item][job_idx - 1])  
        cu.clear_screen()
        print(f"{Fore.LIGHTGREEN_EX}{len(jobs_to_add)} job(s) added to queue.")  # CHECK


# Remove jobs from queue
def remove_jobs():
    jobs_to_remove = validate_selected_jobs(input("Select jobs (e.g: 5, 2-10): "))

    if jobs_to_remove is not None and cu.confirm_action():
        # Remove jobs from queue in reverse order
        for job_idx in sorted(jobs_to_remove, reverse=True):
            for item in range(4):
                job_queue[item].pop(job_idx - 1)  # Reduce input index by 1 to match real queue index
        cu.clear_screen()   # CHECK 
        print(f"{Fore.LIGHTGREEN_EX}{len(jobs_to_remove)} job(s) removed from queue.")  # CHECK


# Validate jobs selected by user
def validate_selected_jobs(user_input, job_list=job_queue):
    valid_job_indexes = []
    selected_jobs = user_input.replace(" ", "").split(",")  # Split user input into list elements
    job_list_range = range(len(job_list[0]) + 1) # Store job queue length for validations

    for job in selected_jobs:
        # Check if element is a number
        if job.isnumeric():
            job_index = int(job) 
            # Add job index to valid list if a match is found
            if job_index - 1 in job_list_range: # Decrease index by 1 to match real queue index
                valid_job_indexes.append(job_index)

        else:
            # Check if element is a range of jobs (e.g., "15-20")
            if "-" in job:
                start, end = map(int, job.split("-"))
                for job_index in range(start, end + 1): # Increase end index by 1 to match input range
                    if job_index in job_list_range:  
                        valid_job_indexes.append(job_index)

    # Check if valid index list is empty
    if not valid_job_indexes:
        print(f"{Fore.LIGHTRED_EX}Invalid choice! Please select valid jobs.")
        return None
    else:
        print(f"Selected jobs: {valid_job_indexes}")
        return valid_job_indexes

# Clear queue sublists
def clear_job_queue():
    for item in job_queue:
        item.clear()