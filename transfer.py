import datetime
import os
from time import sleep
from typing import Tuple

import byte_formatter
import pexpect
import re
from utils.credentials import IliyaHPCCredentials
from utils.email import send_email
from utils.file_tracker import DownloadTracker
from utils.logger import log

class DataStreamError(Exception):
    def __init__(self):
        super().__init__("Data Stream (Code 12) Error")

class NotFoundError(Exception):
    def __init__(self):
        super().__init__("File not found on remote error")

class TimeoutError(Exception):
    def __init__(self):
        super().__init__("Download Timeout Error")

def download_file(file_path: str, log_dir: str, whole_file: bool) -> Tuple[str, str]:
    try:
        args = [
            "rsync",
            "-a",
            "-vv",
            "--inplace",
            "-P",
            "-h",
            "-r",
            f"--log-file={log_dir}/rsync.log",
            f"is525@rds.uis.cam.ac.uk:{file_path}",
            f"/home/ubuntu/volume-mount/full-transfer/{file_path}"
        ]

        if whole_file:
            args.insert(5, "-W")

        child = pexpect.spawn(
            command="/usr/bin/sudo",
            args=args,
            logfile=open(f"{log_dir}/child.log", "ab")
        )
        child.logfile_read = open(f"{log_dir}/logfile_read.log", "ab")
        child.logfile_send = open(f"{log_dir}/logfile_send.log", "ab")

        child.expect(re.compile(rb".*\(is525@rds.uis.cam.ac.uk\) Password:.*"))
        child.sendline(IliyaHPCCredentials.get_pwd())

        resp = child.expect_list(
            pattern_list=[
                re.compile(rb".*TOTP Verification Code.*"),
                re.compile(rb".*receiving incremental file list.*")
            ])

        if resp == 0:
            child.sendline(IliyaHPCCredentials.get_2fa_code())

        resp = child.expect(
            pattern=[
                rb".*No such file or directory.*",
                rb".*uptodate.*",
                rb".*data=.*",
                rb".*error in rsync protocol data stream.*"
            ],
            timeout=3600
        )

        if resp == 1 or resp == 2:
            return file_path, f"/home/ubuntu/volume-mount/full-transfer/{file_path}"
        elif resp == 0:
            raise NotFoundError
        elif resp == 3:
            raise DataStreamError
        else:
            raise TimeoutError

    except Exception as e:
        log(e)
        raise e

    finally:
        try:
            child.close(force=True)
        except NameError:
            pass

if __name__ == "__main__":
    log("Loading File List")

    download_tracker = DownloadTracker(
        dwl_dir="/home/ubuntu/volume-mount/full-transfer/"
    )
    while not download_tracker.is_done:
        file = download_tracker.get_current_file()

        log_step = (f"Processing {download_tracker.done_count}: {file}\n"
                    f"Files {download_tracker.done_count} / {download_tracker.total_count} : {download_tracker.percent_done}%\n"
                    
                    f"Time Since download started {datetime.timedelta(seconds=download_tracker.abs_seconds_since_start)}:\n"
                    f"\tFiles downloaded since: {download_tracker.done_count}\n"
                    f"\tBytes downloaded since: {byte_formatter.format_size(download_tracker.curr_size)}\n"
                    f"Rate: {download_tracker.abs_files_second} files / second (since start): ~ {download_tracker.abs_time_remaining_fcount} remaining\n"
                    f"Rate: {byte_formatter.format_size(download_tracker.abs_bytes_second)} / second (since start): ~ {download_tracker.abs_time_remaining_bytes} remaining\n"
                    
                    f"Script running for {datetime.timedelta(seconds=download_tracker.seconds_since_start)}:\n"
                    f"\tFiles downloaded since: {download_tracker.files_since_start}\n"
                    f"\tBytes downloaded since: {byte_formatter.format_size(download_tracker.bytes_since_start)}\n"
                    f"Rate: {download_tracker.files_second} files / second (since start): ~ {download_tracker.time_remaining_fcount} remaining\n"
                    f"Rate: {byte_formatter.format_size(download_tracker.bytes_second)} / second (since start): ~ {download_tracker.time_remaining_bytes} remaining")

        log(log_step)

        if file.endswith("/"):
            try:
                os.makedirs(f"/home/ubuntu/volume-mount/full-transfer/{file}")
            except OSError:
                log("Directory already exists")
            except Exception as e:
                raise e

            if os.path.exists(f"/home/ubuntu/volume-mount/full-transfer/{file}"):
                download_tracker.record_download(file, None, False)
        else:
            if " -> " in file:
                split = " -> "
                file_ls = file.split(split)
                file_ls.pop()
                file = split.join(file_ls)
            whole_file = False

            for e_count in range(10):
                try:
                    file_path, dest_path = download_file(
                        file_path=file,
                        log_dir="/home/ubuntu/transfer/logs",
                        whole_file=whole_file
                    )
                    download_tracker.record_download(
                        file_path=file_path,
                        dest_path=dest_path,
                        missing=False
                    )
                    break
                except Exception as e:
                    if isinstance(e, DataStreamError):
                        if whole_file:
                            download_tracker.record_download(file, None, True)
                            break
                        whole_file = True

                    if e_count == 9:
                        log(e)
                        if download_tracker.missing_files_since_start <= 100:
                            download_tracker.record_download(file, None, True)
                        else:
                            send_email(
                                'ov3@sanger.ac.uk',
                                "TRANSFER STOPPED",
                                f"On processing:\n{log_step}\n\n{e}"
                            )
                            raise e

                    else:
                        text_to_log = (f"Processing {download_tracker.done_count}: {file}\n"
                                       f"Files {download_tracker.done_count} / {download_tracker.total_count} : {download_tracker.percent_done}%\n"

                                       f"Time Since download started {datetime.timedelta(seconds=download_tracker.abs_seconds_since_start)}:\n"
                                       f"\tFiles downloaded since: {download_tracker.done_count}\n"
                                       f"\tBytes downloaded since: {byte_formatter.format_size(download_tracker.curr_size)}\n"
                                       f"Rate: {download_tracker.abs_files_second} files / second (since start): ~ {download_tracker.abs_time_remaining_fcount} remaining\n"
                                       f"Rate: {byte_formatter.format_size(download_tracker.abs_bytes_second)} / second (since start): ~ {download_tracker.abs_time_remaining_bytes} remaining\n"
                                       f"FAIL COUNT: {e_count + 1}\n"
                                       f"ERROR:\n{e}")
                        log(text_to_log)
                        sleep(600)
