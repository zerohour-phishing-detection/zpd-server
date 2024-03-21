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
        while len(self.scheduled_futures) > 0:
            for result in self.scheduled_futures:
                if result.done():
                    results.append(result)
                    self.scheduled_futures.remove(result)
        return results
    
    def contains_true_futures(self) -> bool:
        while len(self.scheduled_futures) > 0:
            for result in self.scheduled_futures:
                if result.done():
                    if result:
                        print("TRUE: ", result)
                        return True
                    self.scheduled_futures.remove(result)
        print("FALSE")
        return False

    def yield_results(self): #-> AsyncIterator: # what is return type?
        for result in as_completed(self.scheduled_futures):
            yield result

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
