import threading
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

    def get_scheduled_futures(self) -> list[Future]:
        return self.scheduled_futures
    
    def get_results(self) -> list:
        results = []
        for future in as_completed(self.scheduled_futures):
            results.append(future)
        return results
    
    def cancel(self):
        for future in self.scheduled_futures:
            future.cancel()
    
    def any(self, f = lambda x: x) -> bool:
        for future in as_completed(self.scheduled_futures):
            if f(future.result()):
                return True
        return False

    async def generate(self) -> AsyncIterator:
        for future in as_completed(self.scheduled_futures):
            yield future.result()

class ThreadWorker:
    """
    Thread worker handling running tasks concurrently. FutureGroup should be used to schedule tasks and get the results.
    Can be created with preprocessor for example to create objects to be used for each thread.
    """
    executor: ThreadPoolExecutor
    preprocessor = None
    threadlocal: threading.local

    def __init__(self, init = None, preprocessor = None):
        self.threadlocal = threading.local()
        if init is not None:
            def initwrap():
                self.threadlocal.mydata = init()
        else:
            initwrap = None
        self.executor = ThreadPoolExecutor(initializer=initwrap)
        self.preprocessor = preprocessor

    def new_future_group(self) -> FutureGroup:
        return FutureGroup(self)
    
    def run_task(self, task) -> Future:
        def task_wrapper():
            localdata = []
            if 'mydata' in self.threadlocal.__dict__:
                localdata = [self.threadlocal.mydata]

            if self.preprocessor is not None:
                return self.preprocessor(*localdata, *task)
            else:
                return task(*localdata)
            
        return self.executor.submit(task_wrapper)
    
    def close(self):
        self.executor.shutdown()
