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
        """
        Schedule a task using the worker associated to this FutureGroup.
        Returnes scheduled future, also stores in scheduled futures in this class.
        """
        scheduled_future = self.worker.run_task(task)
        self.scheduled_futures.append(scheduled_future)
        return scheduled_future

    def get_scheduled_futures(self) -> list[Future]:
        """
        Get list of scheduled futures.
        """
        return self.scheduled_futures
    
    def get_results(self) -> list:
        """
        Get list of result of scheduled futures in order of completion.
        """
        results = []
        for future in as_completed(self.scheduled_futures):
            results.append(future)
        return results
    
    def cancel(self):
        """
        Cancelling the scheduled futures that have not been executed.
        """
        for future in self.scheduled_futures:
            future.cancel()
    
    def any(self, f = lambda x: x) -> bool:
        """
        In order of completion, checking for function return true on ANY result.
        Returning this boolean.
        """
        for future in as_completed(self.scheduled_futures):
            if f(future.result()):
                return True
        return False

    async def generate(self) -> AsyncIterator:
        """
        Async generator of the futures that have been scheduled, in order of completion.
        """
        for future in as_completed(self.scheduled_futures):
            yield future.result()

class ThreadWorker:
    """
    Thread worker handling running tasks concurrently.
    FutureGroup should be used to schedule tasks and get the results.
    Can be created with preprocessor for example to create objects to be used for each thread.
    """
    executor: ThreadPoolExecutor
    preprocessor = None
    threadlocal: threading.local

    def __init__(self, init = None, preprocessor = lambda task, *localdata: task(*localdata)):
        self.threadlocal = threading.local()
        # Use custom initializer for using localdata on local thread.
        # For example the localdata can be a class used on each thread.
        if init is not None:
            def initwrap():
                self.threadlocal.mydata = init()
        else:
            initwrap = None
        self.executor = ThreadPoolExecutor(initializer=initwrap)
        self.preprocessor = preprocessor

    def new_future_group(self) -> FutureGroup:
        """
        Create a futurgroup that is able to use this worker.
        """
        return FutureGroup(self)
    
    def run_task(self, task) -> Future:
        """
        Apply the preprocessor with localdata on the task.
        Using the executor the task is run, returning a future.
        """
        def task_wrapper():
            # localdata is put from potential dictionary to array,
            # such that it can be expended as argument possibly empty.
            localdata = []
            if 'mydata' in self.threadlocal.__dict__:
                localdata = [self.threadlocal.mydata]

            return self.preprocessor(task, *localdata)
            
        return self.executor.submit(task_wrapper)
    
    def close(self):
        self.executor.shutdown()

async def async_first(agen, default=None):
    """
    Get first element of async generator, if empty return default or None.
    """
    async for x in agen:
        return x
    return default
