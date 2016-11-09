__author__ = 'dsheoran'

import hashlib
import logging
import os
from plumbum import cli
from plumbum.cmd import pwd, mkdir
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


class Drsync(cli.Application):
    """
    Syncs directories between hosts
    """

    register = cli.Flag(['r', 'register'],
                        help='Register given directory with drsync',
                        group='Mutually Exclusive')
    livesync = cli.Flag(['l', 'livesync'],
                        help='Sync local changes real time to remote directory',
                        group='Mutually Exclusive')

    send = cli.Flag(['s', 'send'],
                    help='Sync local changes to remote',
                    default=False,
                    group='Mutually Exclusive')

    send_test = cli.Flag(['S', 'sendtest'],
                         help='Show what will be sent',
                         default=False,
                         group='Mutually Exclusive')

    get = cli.Flag(['g', 'get'],
                   help='Sync remote changes to local',
                   default=False,
                   group='Mutually Exclusive')

    get_test = cli.Flag(['G', 'gettest'],
                        help='Show what will be fetched',
                        default=False,
                        group='Mutually Exclusive')

    working_dir = cli.SwitchAttr(['p', 'path'],
                                 str,
                                 default=str(os.path.abspath((pwd().strip()))),
                                 help='Override which directory will be synced',
                                 group='Mutually Exclusive')

    log_level = cli.SwitchAttr(['loglevel'],
                               int,
                               default=20,
                               help="Set logging level",
                               group='Optional')

    def main(self):
        # init
        logging.root.setLevel(self.log_level)
        self.working_dir = os.path.abspath(self.working_dir)
        dir_profile = WK_SYN_DIR_FORMAT.format(USER_HOME,
                                               WK_BASE_DIR,
                                               os.path.split(self.working_dir)[1],
                                               hashlib.md5(self.working_dir).hexdigest()
                                               )
        rsync_filter_file = WK_RSYNC_FILTER_FILE.format(dir_profile)
        wk_conf_file = WK_CONF_FILE.format(dir_profile)

        # register given directory
        if self.register:
            if not os.path.exists(dir_profile):
                self.register_directory(dir_profile, rsync_filter_file, wk_conf_file)
                return

            logging.error("Directory {} is registered,config can be found at {}".format(
                self.working_dir,
                dir_profile
            ))

        elif not os.path.exists(dir_profile):

            logging.error(
                "Directory {} is not registered with drsync, run with '-r' to register".format(self.working_dir))
            return

        # sync given directory
        logging.info("Synchronizing directory")
        sync(wk_conf_file,
             dry_run=(self.send_test or self.get_test),
             live=self.livesync,
             reverse_direction=(self.get or self.get_test))

    def register_directory(self, dir_profile, rsync_filter_file, wk_conf_file):
        """
        Configures a directory to work with drsync
        :param dir_profile:
        :param rsync_filter_file:
        :param wk_conf_file:
        """
        # create directory
        logging.info("Registering directory {0}".format(self.working_dir))
        mkdir['-p', dir_profile]()

        # write rsync filter file
        logging.info('Writing filter file to {0}'.format(rsync_filter_file))
        with open(rsync_filter_file, 'w') as f:
            f.write(get_file_content('rsync_filter.txt'))

        # Ask Questions and write wk sync conf file
        config = dict()
        config['dir_profile'] = dir_profile
        config['working_dir_parent'] = os.path.dirname(self.working_dir)
        config['working_dir_name'] = os.path.split(self.working_dir)[-1]

        # ask questions to user
        response = raw_input('Enter remote absolute path where data will sent/received:')
        config['remote_working_dir_parent'] = os.path.abspath(response)
        response = raw_input('Enter remote system hostname:')
        config['remote_host_name'] = response
        logging.info("Writing configuration data to {0}".format(wk_conf_file))
        with open(wk_conf_file, 'w') as f:
            f.write(get_file_content('drsync_conf.txt').format(**config))
        logging.info(get_file_content('post_reg_msg.txt'))
