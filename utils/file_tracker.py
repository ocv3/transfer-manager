import datetime
import os
import time
from typing import List, Optional


def get_complete_list() -> List[str]:
    with open("logs/complete.log", "r") as ls_file:
        return ls_file.read().splitlines()


def get_file_list() -> List[str]:
    with open("file-list.txt", "r") as ls_file:
        return ls_file.read().splitlines()


def record_complete_file(file_path: str, missing: bool = False) -> None:
    if missing:
        file_path += " [MISSING]"
    with open("logs/complete.log", "a") as logFile:
        logFile.write(file_path + "\n")


class DownloadTracker:
    def __init__(self, dwl_dir):
        self.dwl_dir = dwl_dir

        self.file_list = get_file_list()
        done_files = get_complete_list()
        self.done_count = len(done_files)
        self.total_count = len(self.file_list)
        self.file_list = self.file_list[self.done_count:]

        self._start_time = time.time()
        self._dwl_since = 0

        size = self._full_size_dir()
        self._size_at_start = size
        self._curr_size = size

        self.files_second = 0
        self.bytes_second = 0

    def record_download(self, file_path: str, dest_path: Optional[str], missing: bool = False) -> None:
        record_complete_file(file_path, missing)
        self.done_count += 1
        self._dwl_since += 1
        if dest_path:
            self._curr_size += self._calc_file_size(dest_path)
        self._update_rate()

    @property
    def is_done(self) -> bool:
        return self.done_count == self.total_count

    def get_current_file(self) -> str:
        return self.file_list.pop(0)

    @property
    def percent_done(self):
        return self.done_count / self.total_count * 100

    def _update_rate(self):
        seconds_since_start = self.seconds_since_start
        self.files_second = self._dwl_since / seconds_since_start
        self.bytes_second = self._size_since_start / seconds_since_start

    @property
    def time_remaining_fcount(self):
        if self.files_second == 0:
            return "N/A"
        seconds_remaining = (self.total_count - self.done_count) / self.files_second
        return datetime.timedelta(seconds=seconds_remaining)

    @property
    def time_remaining_bytes(self):
        if self.bytes_second == 0:
            return "N/A"
        seconds_remaining = (1.8723E+13 - self._curr_size) / self.bytes_second
        return datetime.timedelta(seconds=seconds_remaining)

    @property
    def _size_since_start(self):
        return self._curr_size - self._size_at_start

    def _full_size_dir(self):
        total_size = 0
        for dirpath, _, filenames in os.walk(self.dwl_dir):
            for f in filenames:
                total_size += self._calc_file_size(os.path.join(dirpath, f))
        return total_size

    @staticmethod
    def _calc_file_size(path):
        if not os.path.islink(path):
            return os.path.getsize(path)
        return 0

    @property
    def seconds_since_start(self):
        return max(int(time.time() - self._start_time), 1)

    @property
    def files_since_start(self):
        return self._dwl_since

    @property
    def bytes_since_start(self):
        return self._size_since_start