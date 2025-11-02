from ..models.job_queue import JobQueue
from ..external.mkv_merge import MKVMerge
from ..models.enums import JobSelection

from . import console_utils as cu


main_queue = JobQueue()


def main_queue_options(task):
    while True:
        options = {
            "1": "Start queue",
            "2": "Run selected jobs",
            "3": "Remove selected jobs",
            "4": "Merge video with synced sub on completed jobs",
            "5": "Clear queue",
            "6": "Clear completed and failed jobs",
            "7": "Return to main menu",
        }
        main_queue.show(task)
        cu.show_menu_options(options)

        choice = cu.get_choice(1, 7)

        match choice:
            case 1 if cu.confirm_action():
                main_queue.run_jobs(JobSelection.ALL)
            case 2:
                selected_jobs = main_queue.select_jobs("Select jobs to run (e.g: 1, 5-10): ")
                if selected_jobs and cu.confirm_action():
                    main_queue.run_jobs(selected_jobs)
            case 3:
                selected_jobs = main_queue.select_jobs("Select jobs to remove from queue (e.g: 1, 5-10): ")
                if selected_jobs and cu.confirm_action():
                    main_queue.remove_jobs(selected_jobs)
                    cu.print_success(f"{len(selected_jobs)} job(s) removed from queue.")
                    if not main_queue.contents:
                        break
            case 4 if cu.confirm_action():
                if MKVMerge.is_installed:
                    main_queue.merge_completed_video_tasks(main_queue.contents)
                else:
                    cu.print_error("\nMKVMerge could not be found!")
            case 5 if cu.confirm_action():
                main_queue.clear()
                cu.print_success("Queue cleared.")
                break
            case 6 if cu.confirm_action():
                main_queue.clear_completed_jobs()
                if not main_queue.contents:
                    break
            case 7:
                break


def temp_queue_options(temp_queue, task):
    """Handle options for the temporary job queue returned after file selection."""
    while True:
        options = {
            "1": "Run all jobs",
            "2": "Run selected jobs",
            "3": "Add all jobs to queue",
            "4": "Add selected jobs to queue",
            "5": "Return to main menu",
        }
        temp_queue.show(task)
        cu.show_menu_options(options)

        choice = cu.get_choice(1, 5)

        match choice:
            case 1 if cu.confirm_action():
                main_queue.add_jobs(JobSelection.ALL, temp_queue.contents, task)
                temp_queue.run_jobs(JobSelection.ALL)
                break
            case 2:
                selected_jobs = temp_queue.select_jobs("Select jobs to run (e.g: 1, 5-10): ")
                if selected_jobs and cu.confirm_action():
                    main_queue.add_jobs(selected_jobs, temp_queue.contents, task)
                    temp_queue.run_jobs(selected_jobs)
                    break
            case 3 if cu.confirm_action():
                main_queue.add_jobs(JobSelection.ALL, temp_queue.contents, task)
                cu.print_success(f"{len(temp_queue.contents)} job(s) added to queue.")
                break
            case 4:
                selected_jobs = temp_queue.select_jobs("Select jobs to add to the queue (e.g: 1, 5-10): ")
                if selected_jobs and cu.confirm_action():
                    main_queue.add_jobs(selected_jobs, temp_queue.contents, task)
                    cu.print_success(f"{len(selected_jobs)} job(s) added to queue.")
                    break
            case 5 if cu.confirm_action():
                break
