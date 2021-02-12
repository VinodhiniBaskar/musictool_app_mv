import asyncio
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import partial

thread_pool_executor = ThreadPoolExecutor()


def thread_pool(f):
    async def wrapper(*args, **kwagrgs):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(thread_pool_executor, partial(f, *args, **kwagrgs))

    return wrapper
