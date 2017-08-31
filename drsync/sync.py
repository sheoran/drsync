__author__ = 'dsheoran'

import ConfigParser
import logging
import os
import threading
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# globals: 'sync' is prefix to avoid collision with other stuff
sync_config_parser = sync_config_file = sync_rsync_opt = sync_rsync_filter = sync_ignore_list = \
    sync_local_path = sync_local_dir = sync_remote_path = sync_remote_host = \
    sync_file_change_list_queue = sync_queue_lock = None


def sync(sync_conf_file, dry_run=True, live=False, reverse_direction=False):
    global sync_config_parser, sync_config_file, sync_rsync_opt, sync_rsync_filter, sync_ignore_list, sync_local_path, sync_local_dir, sync_remote_path, \
        sync_remote_host, sync_file_change_list_queue, sync_queue_lock

    sync_config_parser = ConfigParser.RawConfigParser()
    sync_config_file = sync_conf_file
    sync_config_parser.read(sync_config_file)

    sync_rsync_opt = sync_config_parser.get('global', 'rsyncOpt')
    sync_rsync_filter = sync_config_parser.get('global', 'rsyncFilter')
    sync_ignore_list = sync_config_parser.get('global', 'ignoreList').split(',')
    sync_local_path = sync_config_parser.get('localHost', 'local_path')
    sync_local_dir = sync_config_parser.get('localHost', 'local_dir')

    sync_remote_path = sync_config_parser.get('remoteHost', 'remote_path')
    sync_remote_host = sync_config_parser.get('remoteHost', 'remote_host')

    sync_file_change_list_queue = set()
    sync_queue_lock = threading.Lock()

    if dry_run:
        sync_rsync_opt += "n"

    if live:
        live_sync()
    else:
        sync_all(reverse_direction=reverse_direction)


def live_sync():
    logging.info('Live sync started')

    global sync_local_path, sync_remote_host, sync_remote_path, sync_file_change_list_queue, sync_local_dir, sync_queue_lock
    observer = Observer()
    observer.schedule(SyncHandler(), sync_local_path + sync_local_dir, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(6)
            sync_helper()
    except KeyboardInterrupt:
        observer.stop()
        observer.join()
    logging.info('')
    logging.info('Live sync stopped')


def sync_all(reverse_direction):
    global sync_local_path, sync_remote_host, sync_remote_path, sync_file_change_list_queue, sync_local_dir, sync_queue_lock

    if reverse_direction:
        source = sync_remote_host + ':' + sync_remote_path + sync_local_dir
        destination = sync_local_path
    else:
        source = sync_local_path + sync_local_dir
        destination = sync_remote_host + ':' + sync_remote_path

    cmd = "rsync %s --filter='%s' %s %s" % (sync_rsync_opt, sync_rsync_filter, source, destination)
    logging.info("Command Used: %s" % cmd)
    os.system(cmd)


class SyncHandler(FileSystemEventHandler):
    def _syncHelper(self, event):
        global sync_local_path, sync_remote_host, sync_remote_path, sync_file_change_list_queue, sync_local_dir, sync_queue_lock, sync_ignore_list
        filename = os.path.abspath(event.src_path)
        if os.path.islink(filename):
            return
        if not filename.startswith(sync_local_path + sync_local_dir):
            return

        for i in sync_ignore_list:
            if i in filename:
                return

        with sync_queue_lock:
            sync_file_change_list_queue.add(filename)

    def on_modified(self, event):
        self._syncHelper(event)

    def on_deleted(self, event):
        self._syncHelper(event)

    def on_created(self, event):
        self._syncHelper(event)


def sync_helper():
    global sync_local_path, sync_remote_host, sync_remote_path, sync_file_change_list_queue, sync_local_dir, sync_queue_lock
    with sync_queue_lock:
        if len(sync_file_change_list_queue) == 0:
            return

        logging.info(sync_file_change_list_queue)

        if len(sync_file_change_list_queue) > 10:
            sync_all(False)
            sync_file_change_list_queue.clear()
            return

        for filename in sorted(list(sync_file_change_list_queue)):
            source = ""
            destination = ""

            sync_file_change_list_queue.remove(filename)

            if not filename.startswith(sync_local_path + sync_local_dir):
                return

            if filename == sync_local_path + sync_local_dir:
                sync_all(False)
                sync_file_change_list_queue.clear()
                return

            if not os.path.exists(filename):
                sync_all(False)
                sync_file_change_list_queue.clear()
                return

            if os.path.isdir(filename):
                continue
            else:
                source = filename
                destination = sync_remote_host + ':' + sync_remote_path + source.replace(sync_local_path, '')

            cmd = "rsync %s --filter='%s' %s %s" % (sync_rsync_opt, sync_rsync_filter, source, destination)
            logging.info(cmd)
            logging.info("Syncing %s " % filename)
            os.system(cmd)
