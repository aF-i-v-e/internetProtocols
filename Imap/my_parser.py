from argparse import ArgumentParser


def parse_args():
    parser = ArgumentParser(description='Displays information about messages in the mailbox')
    parser.add_argument('--ssl', action='store_true',
                        help='Use SSL connection')
    parser.add_argument('-s', '--server', default='imap.mail.ru:143',
                        help='Server and port')
    parser.add_argument('-n', nargs='*', default=['-1'],
                        help='Number (interval) of letters')
    parser.add_argument('-u', '--user', help='User name')
    return parser.parse_args()
