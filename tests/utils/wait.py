import asyncio
import inspect
import logging
import textwrap
import time
from inspect import getframeinfo
from inspect import stack
from pathlib import Path
from typing import Awaitable
from typing import Callable
from typing import Optional
from typing import Union


def wait_for(
    f: Callable[[], bool],
    timeout: float,
    tag: str = "",
    raise_timeout: bool = True,
    retry_duration: float = 0.1,
) -> bool:
    """Call function f() until it returns True or a timeout is reached. retry_duration specified the sleep time between
    calls. If the timeout is reached before f return True, the function will either raise a ValueError (the default),
    or, if raise_timeout==False, it will return False. Function f is guaranteed to be called at least once. If an
    exception is raised the tag string will be attached to its message.
    """
    now = time.time()
    until = now + timeout
    if now >= until:
        if f():
            return True
    while now < until:
        if f():
            return True
        now = time.time()
        if now < until:
            time.sleep(min(retry_duration, until - now))
            now = time.time()
    if raise_timeout:
        raise ValueError(
            f"ERROR. "
            f"[{tag}] wait_for() timed out after {timeout} seconds, wait function {f}"
        )
    else:
        return False


Predicate = Callable[[], bool]
AwaitablePredicate = Callable[[], Awaitable[bool]]
ErrorStringFunction = Callable[[], str]


async def await_for(
    f: Union[Predicate, AwaitablePredicate],
    timeout: float,
    tag: str = "",
    raise_timeout: bool = True,
    retry_duration: float = 0.1,
    err_str_f: Optional[ErrorStringFunction] = None,
    logger: Optional[logging.Logger] = None,
    error_dict: Optional[dict] = None,
) -> bool:
    """Similar to wait_for(), but awaitable. Instead of sleeping after a False resoinse from function f, await_for
    will asyncio.sleep(), allowing the event loop to continue. Additionally, f may be either a function or a coroutine.
    """
    now = start = time.time()
    until = now + timeout
    err_format = (
        "ERROR. [{tag}] wait_for() timed out after {seconds} seconds\n"
        "  [{tag}]\n"
        "  From {file}:{line}\n"
        "  wait function: {f}"
        "{err_str}"
    )
    if err_str_f is not None:
        def err_str_f_() -> str:
            return "\n" + textwrap.indent(err_str_f(), "  ")
    else:
        def err_str_f_() -> str:
            return ""
    f_is_async = inspect.iscoroutinefunction(f)
    result = False
    if now >= until:
        if f_is_async:
            result = await f()
        else:
            result = f()
    while now < until and result is False:
        if f_is_async:
            result = await f()
        else:
            result = f()
        if result is False:
            now = time.time()
            if now < until:
                await asyncio.sleep(min(retry_duration, until - now))
                now = time.time()
    if result is True:
        return True
    else:
        caller = getframeinfo(stack()[1][0])
        format_dict = dict(
            tag=tag,
            file=Path(caller.filename).name,
            line=caller.lineno,
            seconds=time.time() - start,
            f=f,
            err_str=err_str_f_()
        )
        err_str = err_format.format(**format_dict)
        if error_dict is not None:
            error_dict.update(
                format_dict,
                err_str=err_str,
            )
        if logger is not None:
            logger.error(err_str)
        if raise_timeout:
            raise ValueError(err_str)
        else:
            return False
