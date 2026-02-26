import os
from time import sleep
import pexpect
import re
from utils.credentials import IliyaHPCCredentials
from utils.file_tracker import DownloadTracker
from utils.logger import log

def download_file(file_path: str, log_dir: str, dwl_tracker: DownloadTracker) -> None:
    try:
        child = pexpect.spawn(
            command="rsync",
            args=[
                "-a",
                "-vv",
                "--inplace",
                "-P",
                "-h",
                "-r",
                f"--log-file={log_dir}/rsync.log",
                f"is525@rds.uis.cam.ac.uk:{file_path}",
                f"/home/ubuntu/volume-mount/full-transfer/{file_path}"
            ],
            logfile=open(f"{log_dir}/child.log", "ab")
        )
        child.logfile_read = open(f"{log_dir}/logfile_read.log", "ab")
        child.logfile_send = open(f"{log_dir}/logfile_send.log", "ab")

        child.expect(".*Password.*")
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
                rb".*data=.*"
            ],
            timeout=1300
        )

        if resp == 1 or resp == 2:
            dwl_tracker.record_download(file_path)
            child.close(force=True)
        elif resp == 0:
            dwl_tracker.record_download(file_path, missing=True)
            child.close(force=True)

    except Exception as e:
        log(e)
        raise e


if __name__ == "__main__":
    log("Loading File List")

    download_tracker = DownloadTracker(
        dwl_dir = "/home/ubuntu/volume-mount/full-transfer/"
    )
    while not download_tracker.is_done:
        file = download_tracker.get_current_file()
        log(f"Processing {download_tracker.done_count}: {file}")
        log(f"Files {download_tracker.done_count} / {download_tracker.total_count} : {download_tracker.percent_done}%")
        log(f"Rate: {download_tracker.files_second} files / second (since start): ~ {download_tracker.time_remaining_fcount} remaining")
        log(f"Rate: {download_tracker.bytes_second} bytes / second (since start): ~ {download_tracker.time_remaining_bytes} remaining")

        if file.endswith("/"):
            try:
                os.makedirs(f"/home/ubuntu/volume-mount/full-transfer/{file}")
            except OSError:
                log("Directory already exists")
            except Exception as e:
                raise e

            if os.path.exists(f"/home/ubuntu/volume-mount/full-transfer/{file}"):
                download_tracker.record_download(file)
        else:
            for e_count in range(10):
                try:
                    download_file(
                        file_path=file,
                        log_dir="/home/ubuntu/transfer/logs",
                        dwl_tracker=download_tracker
                    )
                    break
                except Exception as e:
                    if e_count == 9:
                        raise e
                    else:
                        log(e)
                        log(f"FAIL COUNT: {e_count + 1}")
                        sleep(600)