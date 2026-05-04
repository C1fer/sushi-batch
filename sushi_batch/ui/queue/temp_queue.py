from ...models import settings as s
from ...models.enums import Task
from ...models.job_queue import JobQueue, JobQueueContents
from ...services.queue_execution_service import QueueExecutionService
from ...utils import utils
from ...utils.constants import DynamicMenuItem, MenuItem
from ...utils import console_utils as cu
from ..prompts import choice_prompt, confirm_prompt
from . import queue_manager as qm

TEMP_QUEUE_TOP_OPTIONS: list[MenuItem | DynamicMenuItem] = [
    (1, "Run and Add to Main Queue"),
    (2, "Run and Add to Main Queue (Include Advanced Sushi Args)", lambda args: args["enable_advanced_sushi_args"]),
    (3, "Queue Without Running"),
    (4, "Return to Main Menu"),
]

TEMP_QUEUE_SUB_OPTIONS: dict[str, list[MenuItem]] = {
    "run_add": [
        (1, "All"),
        (2, "Selected"),
        (3, "Go Back"),
    ],
}

TO_ADD_SELECTED_PROMPT = "Select which jobs to queue:"


def _run_and_queue_all(temp_queue: JobQueue, task: Task, use_advanced_sushi_args: bool= False) -> bool:
    current_queue_length: int = len(qm.main_queue.contents)
    qm.main_queue.add_jobs(temp_queue.contents, task)
    to_run: JobQueueContents = qm.main_queue.contents[current_queue_length:] # Run the new jobs that were added to the main queue
    QueueExecutionService.run_jobs(to_run, use_advanced_sushi_args=use_advanced_sushi_args, parent_queue=qm.main_queue)
    return True

def _queue_without_running_all(temp_queue: JobQueue, task: Task) -> bool:
    qm.main_queue.add_jobs(temp_queue.contents, task)
    qm.show_continue_confirmation(temp_queue.contents)
    return True

def _handle_run_and_queue_multiple(temp_queue: JobQueue, task: Task, use_advanced_sushi_args: bool = False) -> bool:
    run_choice: int = choice_prompt.get(message=qm.TO_RUN_SELECTED_PROMPT, options=TEMP_QUEUE_SUB_OPTIONS["run_add"], nl_before=False)
    match run_choice:
        case 1 if confirm_prompt.get():
            return _run_and_queue_all(temp_queue, task, use_advanced_sushi_args=use_advanced_sushi_args)
        case 2:
            selected_jobs: JobQueueContents = temp_queue.select_jobs(prompt_message=qm.TO_RUN_SELECTED_PROMPT)
            if selected_jobs and confirm_prompt.get("Run selected jobs and add to main queue?", nl_after=True):
                qm.main_queue.add_jobs(selected_jobs, task)
                QueueExecutionService.run_jobs(selected_jobs, use_advanced_sushi_args=use_advanced_sushi_args)
                return True
    return False

def _handle_queue_without_running_multiple(temp_queue: JobQueue, task: Task) -> bool:
    add_choice: int = choice_prompt.get(message=TO_ADD_SELECTED_PROMPT, options=TEMP_QUEUE_SUB_OPTIONS["run_add"], nl_before=False)
    match add_choice:
        case 1:
            return _queue_without_running_all(temp_queue, task)
        case 2:
            selected_jobs: JobQueueContents = temp_queue.select_jobs(prompt_message=TO_ADD_SELECTED_PROMPT)
            if selected_jobs and confirm_prompt.get("Add selected jobs to main queue?", nl_after=True):
                qm.main_queue.add_jobs(selected_jobs, task)
                qm.show_continue_confirmation(selected_jobs)
                return True
    return False

def _show_temp_queue(temp_queue: JobQueue, task: Task) -> bool:
    """Handle options for the temporary job queue created after file selection."""
    validations: dict[str, bool] = { "enable_advanced_sushi_args": bool(s.config.sync_workflow["enable_sushi_advanced_args"]) }
    visible_options: list[MenuItem] = cu.get_visible_options(TEMP_QUEUE_TOP_OPTIONS, validations)

    while True:
        qm.show_queue_items(temp_queue.contents, is_main_queue=False)
        is_single_job: bool = len(temp_queue.contents) == 1
        
        top_lvl_choice: int = choice_prompt.get(options=visible_options, nl_before=True)
        match top_lvl_choice:
            case 1 | 2:
                use_advanced_sushi_args: bool = top_lvl_choice == 2
                exit_loop: bool = _run_and_queue_all(temp_queue, task, use_advanced_sushi_args=use_advanced_sushi_args) if is_single_job else _handle_run_and_queue_multiple(temp_queue, task, use_advanced_sushi_args=use_advanced_sushi_args)
                if exit_loop:
                    return True
            case 3:
                exit_loop: bool = (
                    _queue_without_running_all(temp_queue, task)
                    if is_single_job
                    else _handle_queue_without_running_multiple(temp_queue, task)
                )
                if exit_loop:
                    return True
            case _:
                return False

def show_temp_queue(temp_queue: JobQueue, task: Task) -> bool:
    return utils.interrupt_signal_handler(_show_temp_queue)(temp_queue, task)