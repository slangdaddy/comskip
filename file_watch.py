"""
File watch commercial remover
"""
import os
import subprocess
import logging
import shutil
import sys
import time
from threading import Thread
from queue import Queue

WORK_ROOT = "/config/"

_LOGGER = logging.getLogger(__name__)
logging.basicConfig(filename=WORK_ROOT+'watcher.log', filemode='a', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

IN_PROCESS = set()


class CommercialWorker(Thread):
    """Commercial process queue"""
    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            # Get paths
            pid_path, file_path = self.queue.get()
            try:
                find_commercials(pid_path, file_path)
            finally:
                self.queue.task_done()


def find_commercials(pid_path, file_path):
    """Call comchap to find commercials"""
    # file_path = file_path.rstrip()

    # print(pid_path)
    # print(file_path)
    # return

    # Check to make sure file exists first
    if os.path.isfile(file_path):
        _LOGGER.info("Processing: " + file_path)

        name = os.path.splitext(os.path.basename(file_path))[0]
        path = os.path.dirname(file_path)

        # Make backup of original in case something goes wrong and
        # store it's size for comparison later
        backup = os.path.join(path, name + ".mkv.bak")
        shutil.copy(file_path, backup)
        backup_size = os.path.getsize(backup)
        _LOGGER.info("Backup Created (%s): %s", backup_size, backup)

        # Start commercial processing
        cmd = ['/opt/comchap/comchap',
               '--keep-edl',
               '--comskip=/opt/Comskip/comskip',
               '--comskip-ini=/opt/Comskip/comskip.ini',
               file_path]
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, timeout=1800)
        _LOGGER.debug("Subprocess finished (code: %s) for: %s", result.returncode, file_path)
        if result.returncode == 0:
            _LOGGER.info("Commercial chapters inserted into: " + file_path)
            # Explicitly set new file permissions
            shutil.chown(file_path, 99, 100)

            # Make sure new file exists and is in the size ballpark
            if os.path.isfile(file_path):
                new_size = os.path.getsize(file_path)
                if new_size > (backup_size*.9):
                    # New is at least 90% of backup, we can move on
                    # Remove path from process set and delete file
                    try:
                        os.remove(pid_path)
                        IN_PROCESS.remove(file_path)
                        os.remove(backup)
                    except OSError as err:
                        _LOGGER.error("File removal error: " + err)
                else:
                    _LOGGER.error("New file size incorrect (B: %s, N: %s) Restoring Backup.", backup_size, new_size)
                    # New file size isn't what we expect, restore the backup
                    shutil.move(backup, file_path)
                    # Remove working indicators
                    os.remove(pid_path)
                    IN_PROCESS.remove(file_path) # Only removing this would allow a retry
            else:
                _LOGGER.error("New file doesn't exist, restoring backup.")
                shutil.move(backup, file_path)
                # Remove working indicator from set to try again
                IN_PROCESS.remove(file_path)
        else:
            if result.stderr:
                # Something went wrong in commercial processing
                _LOGGER.error("Comchap error: %s", result.stderr)
            else:
                _LOGGER.error("Unknown Comchap error for file: %s, Restoring backup.", file_path)
            # If we end up here we need to make sure the backup is restored
            shutil.move(backup, file_path)
            # Remove working indicator
            os.remove(pid_path)
            IN_PROCESS.remove(file_path)
    else:
        # File doesn't exist, we can't do anything
        _LOGGER.info("%s does not exist, nothing to do...", file_path)
        # Remove working indicator
        os.remove(pid_path)
        IN_PROCESS.remove(file_path)


def main():
    """Main function."""
    watch_path = os.fsencode(sys.argv[1])

    queue = Queue()

    for xwork in range(5):
        worker = CommercialWorker(queue)
        worker.daemon = True
        worker.start()

    queue.join()

    _LOGGER.info("Starting Loop...")

    while True:
        # Check folder for new file tasks
        for item in os.scandir(watch_path):
            if item.is_file():
                pid = item.path.decode('utf-8')
                if pid.endswith(".comm"):
                    # New comm task to process
                    with open(pid) as fop:
                        fpath = fop.readline().rstrip()
                    if fpath not in IN_PROCESS:
                        IN_PROCESS.add(fpath)
                        queue.put((pid, fpath))

        # Check every 5s to limit I/O
        time.sleep(5)

if __name__ == '__main__':
    main()
