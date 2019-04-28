"""
Socket server commercial remover
"""
import os
import subprocess
import logging
import shutil

import socket
import selectors
import types
from threading import Thread
from queue import Queue

WORK_ROOT = "/config/"

_LOGGER = logging.getLogger(__name__)
logging.basicConfig(filename=WORK_ROOT+'watcher.log', filemode='a', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

HOST = '0.0.0.0'  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)


class CommercialWorker(Thread):
    """Commercial process queue"""
    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            # Get paths
            file_path = self.queue.get()
            try:
                find_commercials(file_path)
            finally:
                self.queue.task_done()


def accept_wrapper(sel, sock):
    """Accept connections"""
    conn, addr = sock.accept()  # Should be ready to read
    _LOGGER.info('Accepted connection from: ' + str(addr))
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)


def service_connection(sel, key, mask, queue):
    """Service connections"""
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if recv_data:
            data.outb += recv_data
        else:
            queue.put(data.outb.decode('utf-8'))
            data.outb = ""
            _LOGGER.info('Closing connection to: ' + str(data.addr))
            sel.unregister(sock)
            sock.close()


def find_commercials(file_path):
    """Call comchap to find commercials"""
    file_path = file_path.rstrip()
    _LOGGER.info("Finding Commercials in: " + file_path)

    name = os.path.splitext(os.path.basename(file_path))[0]
    path = os.path.dirname(file_path)

    mkv_out = os.path.join(WORK_ROOT, "working", name + ".mkv")
    new_final = os.path.join(path, name + ".mkv")

    # Convert to mkv first
    cmd = ['usr/bin/ffmpeg',
           '-nostdin',
           '-i', file_path,
           '-map', '0',
           '-c', 'copy',
           mkv_out]
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL)

    _LOGGER.info("MKV file created...")

    cmd = ['/opt/comchap/comchap',
           '--comskip=/opt/Comskip/comskip',
           '--comskip-ini=/config/comskip.ini',
           mkv_out]
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL)

    _LOGGER.info("Commercial chapters inserted...")

    shutil.copy2(mkv_out, path)
    # Explicitly set new file permissions
    shutil.chown(new_final, 99, 100)

    _LOGGER.info("New commercial marked file copied...")

    # Make sure new file exists, then Remove old files
    if os.path.isfile(new_final):
        try:
            os.remove(mkv_out)
            os.remove(file_path)
        except OSError as err:
            _LOGGER.info("File removal error: " + err)
    else:
        _LOGGER.info("New file not created, keeping original.")

    _LOGGER.info("Job Complete.")


def main():
    """Main function."""

    sel = selectors.DefaultSelector()

    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.bind((HOST, PORT))
    lsock.listen()
    _LOGGER.info('Listening on: ' + str(HOST) + ":" + str(PORT))
    lsock.setblocking(False)
    sel.register(lsock, selectors.EVENT_READ, data=None)

    queue = Queue()

    for xwork in range(5):
        worker = CommercialWorker(queue)
        worker.daemon = True
        worker.start()

    queue.join()

    _LOGGER.info("Starting Loop...")

    while True:
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                accept_wrapper(sel, key.fileobj)
            else:
                service_connection(sel, key, mask, queue)


if __name__ == '__main__':
    main()
