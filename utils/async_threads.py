import asyncio
from concurrent.futures import Future, ThreadPoolExecutor


class ProcessGroup:
    """
        Handles interaction with ThreadWorker by keeping track of scheduled tasks and returning them.
    """
    scheduled_processes: list[Future]
    worker: "ThreadWorker"

    def __init__(self, worker: "ThreadWorker"):
        self.scheduled_processes = []
        self.worker = worker

    def schedule(self, task):
        scheduled_process = self.worker.run_task(task)
        self.scheduled_processes.append(scheduled_process)

    def get_scheduled_processes(self) -> list[Future]: # Using concurrent.futures.Future as it is thread safe.
        return self.scheduled_processes

class ThreadWorker:
    """
        Thread worker handling running tasks concurrently. ProcessGroup should be used to schedule tasks and get the results.
    """
    executor: ThreadPoolExecutor
    loop: asyncio.BaseEventLoop

    def __init__(self):
        self.executor = ThreadPoolExecutor() # Standard amount of workers is fine (Logical CPU's + 4)
        self.loop = asyncio.get_running_loop()
    
    def new_process_group(self) -> ProcessGroup:
        return ProcessGroup(self)
    
    def run_task(self, task):
        return self.loop.run_in_executor(self.executor, task)
    
    def close(self):
        self.executor.shutdown()
