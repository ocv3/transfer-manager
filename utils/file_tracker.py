from typing import List

def get_complete_list() -> List[str]:
    with open("logs/complete.log", "r") as ls_file:
        return ls_file.read().splitlines()

def get_file_list() -> List[str]:
    with open("file-list.txt", "r") as ls_file:
        return ls_file.read().splitlines()

def record_complete_file(file_path: str, missing:bool = False) -> None:
    if missing:
        file_path += " [MISSING]"
    with open("logs/complete.log", "a") as logFile:
        logFile.write(file_path + "\n")

class DownloadTracker:
    def __init__(self):
        self.file_list = get_file_list()
        done_files = get_complete_list()
        self.done_count = len(done_files)
        self.total_count = len(self.file_list)

        for file in done_files:
            if self.file_list[0] == file or file.endswith("[MISSING]"):
                self.file_list.pop(0)

    def record_download(self, file_path:str, missing:bool = False) -> None:
        record_complete_file(file_path, missing)
        self.done_count += 1

    @property
    def is_done(self) -> bool:
        return self.done_count != self.total_count

    def get_current_file(self) -> str:
        return self.file_list.pop(0)

    @property
    def percent_done(self):
        return self.done_count / self.total_count * 100