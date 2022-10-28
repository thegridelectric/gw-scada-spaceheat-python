import abc
import re
import shutil
from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple
from typing import Optional

import pendulum
from pendulum import DateTime
from result import Err
from result import Ok
from result import Result


class Problems(ValueError):
    MAX_PROBLEMS = 10

    errors: list[BaseException]
    warnings: list[BaseException]
    max_problems: Optional[int] = MAX_PROBLEMS

    def __init__(
            self,
            msg: str = "",
            warnings: Optional[list[BaseException]] = None,
            errors: Optional[list[BaseException]] = None,
            max_problems: Optional[int] = MAX_PROBLEMS
    ):
        self.errors = errors or []
        self.warnings = warnings or []
        self.max_problems = max_problems
        super().__init__(msg)

    def __bool__(self) -> bool:
        return bool(self.errors) or bool(self.warnings)

    def add_error(self, error: BaseException) -> "Problems":
        if len(self.errors) < self.max_problems:
            self.errors.append(error)
        return self

    def add_warning(self, warning: BaseException) -> "Problems":
        if len(self.warnings) < self.max_problems:
            self.warnings.append(warning)
        return self

    def add_problems(self, other: "Problems") -> "Problems":
        self.errors.extend(other.errors[:self.max_problems - len(self.errors)])
        self.warnings.extend(other.warnings[:self.max_problems - len(self.warnings)])
        return self

    def __str__(self) -> str:
        if bool(self):
            s = f"Problems: {len(self.errors)} errors, {len(self.warnings)} warnings, max: {self.max_problems}"
            for attr_name in ["errors", "warnings"]:
                lst = getattr(self, attr_name)
                if lst:
                    s += f"\n{attr_name.capitalize()}:\n"
                    for i, entry in enumerate(lst):
                        s += f"  {i:2d}: {entry}\n"
            return s
        return ""

    def __repr__(self) -> str:
        return str(self)

class PersisterException(Exception):
    path: Optional[Path] = None
    uid: str = ""

    def __init__(self, msg: str = "", uid: str = "", path: Optional[Path] = None):
        self.path = path
        self.uid = uid
        super().__init__(msg)

    def __str__(self):
        s =  self.__class__.__name__
        super_str = super().__str__()
        if super_str:
            s += f" [{super_str}]"
        s += f"  for uid: {self.uid}  path:{self.path}"
        return s


class PersisterError(PersisterException):
    ...


class PersisterWarning(PersisterException):
    ...


class WriteFailed(PersisterError):
    ...


class ContentTooLarge(PersisterError):
    ...


class FileMissing(PersisterError):
    ...


class ReadFailed(PersisterError):
    ...


class TrimFailed(PersisterError):
    ...


class ReindexError(PersisterError):
    ...


class UIDExistedWarning(PersisterWarning):
    ...


class FileExistedWarning(PersisterWarning):
    ...


class FileMissingWarning(PersisterWarning):
    ...


class UIDMissingWarning(PersisterWarning):
    ...


class PersisterInterface(abc.ABC):

    @abstractmethod
    def persist(self, uid: str, content: bytes) -> Result[bool, Problems]:
        """Persist content, indexed by uid"""

    @abstractmethod
    def clear(self, uid: str) -> Result[bool, Problems]:
        """Delete content persisted for uid. It is error to clear a uid which is not currently persisted."""

    @abstractmethod
    def pending(self) -> list[str]:
        """Get list of pending (persisted and not cleared) uids"""

    @property
    @abstractmethod
    def num_pending(self) -> int:
        """Get number of pending uids"""

    @abstractmethod
    def __contains__(self, uid: str) -> bool:
        """Check whether a uid is pending"""

    @abstractmethod
    def retrieve(self, uid: str) -> Result[Optional[bytes], Problems]:
        """Load and return persisted content for uid"""

    @abstractmethod
    def reindex(self) -> Result[Optional[bool], Problems]:
        """Re-created pending index from persisted storage"""


@dataclass
class _PersistedItem(NamedTuple):
    uid: str
    path: Path


class TimedRollingFilePersister(PersisterInterface):
    DEFAULT_MAX_BYTES: int = 500 * 1024 * 1024
    FILENAME_RGX: re.Pattern = re.compile(r"(?P<dt>.*)\.uid\[(?P<uid>.*)].json$")

    _base_dir: Path
    _max_bytes: int = DEFAULT_MAX_BYTES
    _pending: dict[str, Path]
    _curr_dir: Path
    _curr_bytes: int

    def __init__(
        self,
        base_dir: Path | str,
        max_bytes: int = DEFAULT_MAX_BYTES
    ):
        self._base_dir = Path(base_dir).resolve()
        self._max_bytes = max_bytes
        self._curr_dir = self._today_dir()
        self.reindex()

    @property
    def max_bytes(self) -> int:
        return self._max_bytes

    @property
    def curr_bytes(self) -> int:
        return self._curr_bytes

    @property
    def base_dir(self) -> Path:
        return self._base_dir

    @property
    def curr_dir(self) -> Path:
        return self._curr_dir

    def persist(self, uid: str, content: bytes) -> Result[bool, Problems]:
        problems = Problems()
        try:
            if len(content) > self._max_bytes:
                return Err(
                    problems.add_error(
                        ContentTooLarge(
                            f"content bytes ({len(content)} > max bytes {self._max_bytes}",
                            uid=uid,
                        )
                    )
                )
            if len(content) + self._curr_bytes > self._max_bytes:
                trimmed = self._trim_old_storage(len(content))
                match trimmed:
                    case Err(trim_problems):
                        problems.add_problems(trim_problems)
                        if problems.errors:
                            return Err(problems.add_error(TrimFailed(uid=uid)))
            existing_path = self._pending.pop(uid, None)
            if existing_path is not None:
                problems.add_warning(UIDExistedWarning(uid=uid, path=existing_path))
                if existing_path.exists():
                    self._curr_bytes -= existing_path.stat().st_size
                    problems.add_warning(FileExistedWarning(uid=uid, path=existing_path))
                else:
                    problems.add_warning(FileMissingWarning(uid=uid, path=existing_path))
            self._roll_curr_dir()
            self._pending[uid] = self._curr_dir / self._make_name(pendulum.now("utc"), uid)
            try:
                with self._pending[uid].open("wb") as f:
                    f.write(content)
                self._curr_bytes += len(content)
            except BaseException as e: # pragma: no cover
                return Err(
                    problems.add_error(e).add_error(
                        WriteFailed(f"Open or write failed", uid=uid, path=existing_path)
                    )
                )
        except BaseException as e:
            return Err(problems.add_error(e).add_error(PersisterError(
                f"Unexpected error", uid=uid
            )))
        if problems:
            return Err(problems)
        else:
            return Ok()

    def _trim_old_storage(self, needed_bytes: int) -> Result[bool, Problems]:
        problems = Problems()
        last_day_dir: Optional[Path] = None
        items = list(self._pending.items())
        for uid, path in items:
            try:
                match self.clear(uid):
                    case Err(other):
                        problems.add_problems(other)
                day_dir = path.parent
                if last_day_dir is not None and last_day_dir != day_dir:
                    shutil.rmtree(last_day_dir, ignore_errors=True)
                last_day_dir = day_dir
            except BaseException as e:
                problems.add_error(e)
                problems.add_error(PersisterError("Unexpected error", uid=uid, path=path))
            if self._curr_bytes <= self._max_bytes - needed_bytes:
                break
        try:
            if last_day_dir is not None:
                if not self._pending or next(iter(self._pending.values())).parent != last_day_dir:
                    shutil.rmtree(last_day_dir, ignore_errors=True)
        except BaseException as e: # pragma: no cover
            problems.add_error(e)
            problems.add_error(PersisterError("Unexpected error"))
        if problems:
            return Err(problems)
        else:
            return Ok()

    def clear(self, uid: str) -> Result[bool, Problems]:
        problems = Problems()
        path = self._pending.pop(uid, None)
        if path:
            if path.exists():
                self._curr_bytes -= path.stat().st_size
                path.unlink()
                if next(path.parent.iterdir(), None) is None:
                    shutil.rmtree(path.parent, ignore_errors=True)
            else:
                problems.add_warning(FileMissingWarning(uid=uid, path=path))
        else:
            problems.add_warning(UIDMissingWarning(uid=uid, path=path))
        if problems:
            return Err(problems)
        else:
            return Ok()

    def pending(self) -> list[str]:
        return list(self._pending.keys())

    @property
    def num_pending(self) -> int:
        return len(self._pending)

    def __contains__(self, uid: str) -> bool:
        return uid in self._pending

    def get_path(self, uid: str) -> Optional[Path]:
        return self._pending.get(uid, None)

    def retrieve(self, uid: str) -> Result[Optional[bytes], Problems]:
        problems = Problems()
        content: Optional[bytes] = None
        path = self._pending.get(uid, None)
        if path:
            if path.exists():
                try:
                    with path.open("rb") as f:
                        content: bytes = f.read()
                except BaseException as e: # pragma: no cover
                    problems.add_error(e).add_error(
                        ReadFailed(f"Open or read failed", uid=uid, path=path)
                    )
            else:
                problems.add_error(FileMissing(uid=uid, path=path))
        if problems:
            return Err(problems)
        else:
            return Ok(content)

    def reindex(self) -> Result[bool, Problems]:
        problems = Problems()
        self._curr_bytes = 0
        paths: list[_PersistedItem] = []
        for base_dir_entry in self._base_dir.iterdir():
            # noinspection PyBroadException
            try:
                if base_dir_entry.is_dir() and self._is_iso_parseable(base_dir_entry):
                    for day_dir_entry in base_dir_entry.iterdir():
                        # noinspection PyBroadException
                        try:
                            if persisted_item := self._persisted_item_from_file_path(day_dir_entry):
                                self._curr_bytes += persisted_item.path.stat().st_size
                                paths.append(persisted_item)
                        except BaseException as e:
                            problems.add_error(e).add_error(ReindexError(path=day_dir_entry))
            except BaseException as e:
                problems.add_error(e).add_error(ReindexError())
        self._pending = dict(sorted(paths, key=lambda item: item.path))
        if problems:
            return Err(problems)
        else:
            return Ok()

    def _today_dir(self) -> Path:
        return self._base_dir / pendulum.today("utc").isoformat()

    def _roll_curr_dir(self):
        today_dir = self._today_dir()
        if today_dir != self._curr_dir:
            self._curr_dir = today_dir
        if not self._curr_dir.exists():
            self._curr_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def _make_name(cls, dt: DateTime, uid: str) -> str:
        return f"{dt.isoformat()}.uid[{uid}].json"

    @classmethod
    def _persisted_item_from_file_path(cls, filepath: Path) -> Optional[_PersistedItem]:
        item = None
        # noinspection PyBroadException
        try:
            match = cls.FILENAME_RGX.match(filepath.name)
            if match and cls._is_iso_parseable(match.group("dt")):
                item = _PersistedItem(match.group("uid"), filepath)
        except: # pragma: no cover
            pass
        return item

    @classmethod
    def _is_iso_parseable(cls, s: str | Path) -> bool:
        # noinspection PyBroadException
        try:
            if isinstance(s, Path):
                s = s.name
            return isinstance(pendulum.parse(s), DateTime)
        except:
            return False
