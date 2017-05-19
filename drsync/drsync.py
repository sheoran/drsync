"""Drsync.

Usage:
    drsync (-r | --lr ) [--loglevel LEVEL | -p PATH]
    drsync (-s | -S | -f | -F | -l) [--loglevel LEVEL | -p PATH] SYNCLOCAITON

Options:
    -r --register       Register a new sync location
    --lr                List registered sync location
    -l --livesync       Send local changes in realtime
    -s --send           Send local changes
    -S --sendtest       Send local changes test only
    -f --fetch          Fetch remote changes
    -F --fetchtest      Fetch remote changes test only

    --loglevel LEVEL    Set logging level [default: 20]
    -p PATH --path      Override which directory will be synced, default is current directory
    -h --help           Show this screen
"""
from dotmap import DotMap

__author__ = 'dsheoran'

import hashlib
import logging
import os

from docopt import docopt

from .sync import sync

# Globals
WK_BASE_DIR = '.drsync'
WK_SYN_DIR_FORMAT = '{0}/{1}/{2}_{3}'
WK_RSYNC_FILTER_FILE = '{0}/rsyncfilter'
WK_CONF_FILE = '{0}/drsync.conf'
WK_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
USER_HOME = os.path.abspath(os.environ['HOME'])


def get_file_content(filename):
    """
    Returns the content of file. Existence of same file under app directory in user home overrides the default
    :param filename:
    :return: content of file
    """
    # check if user have overridden anything
    filepath = "{}/{}/{}".format(USER_HOME, WK_BASE_DIR, filename)
    if os.path.exists(filepath):
        return open(filepath).read()

    # read default file content
    filepath = "{}/{}/{}".format(WK_SCRIPT_DIR, 'data', filename)
    if os.path.exists(filepath):
        return open(filepath).read()

    raise RuntimeError("Invalid filename given or doesn't exists, filename: {}".format(filename))


class Drsync:
    """
    Syncs directories between hosts
    """

    def main(self):
        arguments = docopt(__doc__)

        # convert args to dotmap
        args = DotMap(_dynamic=False)
        for k, v in arguments.iteritems():
            args[k.replace('--', '')] = v

        # Add default and convert data types if needed
        args.loglevel = int(args.loglevel)
        args.path = os.path.abspath(args.path).rstrip('/') if args.path else os.path.abspath((os.getcwd()))

        logging.root.setLevel(args.loglevel)
        # register given directory
        if args.register:
            self.register_directory(args)
            exit(0)

        working_dir = args.path
        dir_profile = WK_SYN_DIR_FORMAT.format(
            USER_HOME,
            WK_BASE_DIR,
            os.path.split(working_dir)[1],
            hashlib.md5(working_dir).hexdigest()
        )
        if not os.path.exists(dir_profile):
            logging.error(
                "Directory {} is not registered with drsync, run with '-r' to register".format(working_dir))
            exit(1)

        if args.lr:
            logging.info("Following sync location are available.\n\t{}".format(
                '\n\t'.join(os.listdir(dir_profile))
            ))
            exit(0)

        _dir_profile = "{}/{}".format(dir_profile, args.SYNCLOCAITON)
        if not os.path.exists(_dir_profile):
            logging.error("Invalid sync location name, valid names are:\n\t{}".format(
                '\t\n'.join(os.listdir(dir_profile))))
            exit(1)
        else:
            dir_profile = _dir_profile

        # sync given directory
        logging.info("Synchronizing directory")
        wk_conf_file = WK_CONF_FILE.format(dir_profile)

        sync(wk_conf_file,
             dry_run=(args.sendtest or args.fetchtest),
             live=args.livesync,
             reverse_direction=(args.fetch or args.fetchtest))

    def register_directory(self, args):
        """Configures a directory to work with drsync."""
        # Ask Questions and write wk sync conf file
        working_dir = args.path
        config = dict()
        config['working_dir_parent'] = os.path.dirname(working_dir)
        config['working_dir_name'] = os.path.split(working_dir)[-1]

        host_path = raw_input(
            'Enter <user>@<host>:<path>, where path is parent directory where directory to  be synced will be created:')

        remote_host, remote_working_dir_parent = host_path.rsplit(':')
        remote_working_dir_parent = remote_working_dir_parent.rstrip('/')

        sync_task_name = raw_input("Enter a name which you would like to identify above path as sync_task:")

        dir_profile = WK_SYN_DIR_FORMAT.format(
            USER_HOME,
            WK_BASE_DIR,
            os.path.split(working_dir)[1],
            hashlib.md5(working_dir).hexdigest()
        )
        dir_profile = "{}/{}".format(dir_profile, sync_task_name)

        config['dir_profile'] = dir_profile
        config['remote_host_name'] = remote_host
        config['remote_working_dir_parent'] = remote_working_dir_parent

        # create directory
        logging.info("Registering directory {} as sync task {}".format(working_dir, sync_task_name))
        os.makedirs(dir_profile)

        # write rsync filter file
        rsync_filter_file = WK_RSYNC_FILTER_FILE.format(dir_profile)
        wk_conf_file = WK_CONF_FILE.format(dir_profile)
        logging.info('Writing filter file to {0}'.format(rsync_filter_file))
        with open(rsync_filter_file, 'w') as f:
            f.write(get_file_content('rsync_filter.txt'))

        logging.info("Writing configuration data to {0}".format(wk_conf_file))
        with open(wk_conf_file, 'w') as f:
            f.write(get_file_content('drsync_conf.txt').format(**config))

        logging.info(get_file_content('post_reg_msg.txt'))
