import asyncio
from concurrent.futures import ThreadPoolExecutor


class ProcessGroup:
    """
        Handles interaction with ThreadWorker by keeping track of scheduled tasks and returning them.
    """
    scheduled_processes: list[asyncio.Future]
    worker: "ThreadWorker"

    def __init__(self, worker: "ThreadWorker"):
        self.scheduled_processes = []
        self.worker = worker

    def schedule(self, task):
        scheduled_process = self.worker.run_task(task)
        self.scheduled_processes.append(scheduled_process)

    def get_scheduled_processes(self) -> list[asyncio.Future]: # Look into which future to use, this one or concurrent.future
        return self.scheduled_processes

class ThreadWorker: #Look at how many threads and what lifetime should be of thread.
    """
        Thread worker handling running tasks concurrently. ProcessGroup should be used to schedule tasks and get the results.
    """
    executor: ThreadPoolExecutor
    loop: asyncio.BaseEventLoop

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=5) # Look into how many workers
        self.loop = asyncio.get_running_loop()
    
    def new_process_group(self) -> ProcessGroup:
        return ProcessGroup(self)
    
    def run_task(self, task):
        return self.loop.run_in_executor(self.executor, lambda: task)
    
    def close(self):
        self.executor.shutdown()
