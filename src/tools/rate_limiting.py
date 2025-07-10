import time
import random
from typing import Callable, Any


def with_retry(
    func: Callable,
    max_retries: int = 3,
    rate_limit_delay: float = 60.0,
    backoff_multiplier: float = 1.5,
    jitter_range: float = 10.0
) -> Callable:
    """
    Decorator that adds retry logic with intelligent rate limiting.
    
    Args:
        func: The function to wrap with retry logic
        max_retries: Maximum number of retry attempts
        rate_limit_delay: Base delay for rate limit errors (seconds)
        backoff_multiplier: Multiplier for exponential backoff on rate limits
        jitter_range: Random jitter range to add to delays
    
    Returns:
        Wrapped function with retry logic
    """
    def wrapper(*args, **kwargs):
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_type = type(e).__name__
                print(f"❌ Attempt {attempt + 1}/{max_retries} failed: {error_type}")
                
                if attempt < max_retries - 1:
                    delay = calculate_delay(error_type, attempt, rate_limit_delay, backoff_multiplier, jitter_range)
                    print(f"⏳ Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                else:
                    print(f"❌ All retry attempts failed. Last error: {e}")
                    raise e
    
    return wrapper


def calculate_delay(
    error_type: str,
    attempt: int,
    rate_limit_delay: float = 60.0,
    backoff_multiplier: float = 1.5,
    jitter_range: float = 10.0
) -> float:
    """
    Calculate the delay for retry attempts based on error type.
    
    Args:
        error_type: Type of error that occurred
        attempt: Current attempt number (0-based)
        rate_limit_delay: Base delay for rate limit errors
        backoff_multiplier: Multiplier for exponential backoff
        jitter_range: Random jitter range to add
    
    Returns:
        Delay in seconds
    """
    if "RateLimitError" in error_type:
        # Longer delays for rate limit errors with exponential backoff
        delay = rate_limit_delay * (backoff_multiplier ** attempt)
        jitter = random.uniform(0, jitter_range)
        return delay + jitter
    else:
        # Standard exponential backoff for other errors
        delay = (2 ** attempt)
        jitter = random.uniform(0, 1)
        return delay + jitter


def rate_limited_processing_delay(
    current_index: int,
    total_items: int,
    delay_seconds: float = 10.0,
    message: str = "Waiting before next item..."
) -> None:
    """
    Add a delay between processing items to avoid rate limits.
    
    Args:
        current_index: Current item index (0-based)
        total_items: Total number of items to process
        delay_seconds: Delay in seconds
        message: Message to display during delay
    """
    if current_index < total_items - 1:  # Don't delay after last item
        print(f"⏳ {message}")
        time.sleep(delay_seconds)


def execute_with_retry(
    func: Callable,
    *args,
    max_retries: int = 3,
    rate_limit_delay: float = 60.0,
    backoff_multiplier: float = 1.5,
    jitter_range: float = 10.0,
    **kwargs
) -> Any:
    """
    Execute a function with retry logic applied.
    
    Args:
        func: Function to execute
        *args: Positional arguments for the function
        max_retries: Maximum number of retry attempts
        rate_limit_delay: Base delay for rate limit errors
        backoff_multiplier: Multiplier for exponential backoff
        jitter_range: Random jitter range
        **kwargs: Keyword arguments for the function
    
    Returns:
        Result of the function execution
    """
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_type = type(e).__name__
            print(f"❌ Attempt {attempt + 1}/{max_retries} failed: {error_type}")
            
            if attempt < max_retries - 1:
                delay = calculate_delay(error_type, attempt, rate_limit_delay, backoff_multiplier, jitter_range)
                print(f"⏳ Retrying in {delay:.1f} seconds...")
                time.sleep(delay)
            else:
                print(f"❌ All retry attempts failed. Last error: {e}")
                raise e