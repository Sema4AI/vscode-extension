import requests

from sema4ai.actions import Secret, action


@action(is_consequential=False)
def get_time_now() -> str:
    """
    Returns the current time.

    Returns:
        The current time.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
