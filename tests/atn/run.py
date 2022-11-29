import time
import sys
from typing import Optional
from typing import Sequence

try:
    from tests.atn import Atn2
except ImportError as e:
    raise ImportError(
        f"ERROR. ({e})\n\n"
        "Running the test atn requires an *extra* entry on the pythonpath, the base directory of the repo.\n"
        "Set this with:\n\n"
        "export PYTHONPATH=`pwd`/gw_spaceheat:`pwd`"
    )


def main(argv: Optional[Sequence[str]] = None):
    if argv is None:
        argv = sys.argv[1:]
    a = Atn2.get_atn(argv)
    try:
        time.sleep(1)
        a.snap()
        time.sleep(1)
        while True:
            text = input("> ? ")
            if text:
                # noinspection PyProtectedMember
                a._logger.info(f"eval(\"{text}\")")
                # noinspection PyBroadException
                try:
                    eval(text)
                except:
                    # noinspection PyProtectedMember
                    a._logger.exception(f"Error with [eval(\"{text}\")]")
    finally:
        a.stop_and_join_thread()


if __name__ == "__main__":
    main()
