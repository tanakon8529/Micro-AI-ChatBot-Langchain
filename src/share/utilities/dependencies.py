# utilities/dependencies.py

import asyncio
from fastapi import HTTPException, status

from settings.configs import REQUEST_QUEUE_SIZE

# Initialize the semaphore with the desired concurrency limit
semaphore = asyncio.Semaphore(REQUEST_QUEUE_SIZE)  # e.g., REQUEST_QUEUE_SIZE = 10

async def limit_concurrency():
    # Attempt to acquire the semaphore without waiting
    acquired = semaphore.locked() and semaphore._value <= 0
    if acquired:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests, please try again later."
        )
    await semaphore.acquire()
    return semaphore