from collections.abc import AsyncIterator
from concurrent.futures import Future, ThreadPoolExecutor, as_completed


class FutureGroup:
    """
    Handles interaction with ThreadWorker by keeping track of scheduled tasks and returning them.
    """
    scheduled_futures: list[Future]
    worker: "ThreadWorker"

    def __init__(self, worker: "ThreadWorker"):
        self.scheduled_futures = []
        self.worker = worker

    def schedule(self, task) -> Future:
        scheduled_future = self.worker.run_task(task)
        self.scheduled_futures.append(scheduled_future)
        return scheduled_future

    def get_scheduled_futures(self) -> list[Future]: # Using concurrent.futures.Future as it is thread safe.
        return self.scheduled_futures
    
    def get_array_results(self) -> list:
        results = []
        for future in as_completed(self.scheduled_futures):
            results.append(future)
        return results
    
    # Change to be more reusable with 'any' containing comparison to argument
    def any(self) -> bool:
        for future in as_completed(self.scheduled_futures):
            if future.result():
                return True
        return False

    async def generate(self) -> AsyncIterator:
        for future in as_completed(self.scheduled_futures):
            yield future.result()

class ThreadWorker:
    """
    Thread worker handling running tasks concurrently. FutureGroup should be used to schedule tasks and get the results.
    """
    executor: ThreadPoolExecutor

    def __init__(self):
        self.executor = ThreadPoolExecutor() # Standard amount of workers is fine (Logical CPU's + 4)
    
    def new_future_group(self) -> FutureGroup:
        return FutureGroup(self)
    
    def run_task(self, task) -> Future:
        return self.executor.submit(task)
    
    def close(self):
        self.executor.shutdown()
