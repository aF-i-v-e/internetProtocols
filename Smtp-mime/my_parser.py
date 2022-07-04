from argparse import ArgumentParser
import os


def parse_args():
    parser = ArgumentParser(description='Sends to the recipient all images from the specified (or working) directory'
                                        ' as an attachment.')
    parser.add_argument('--ssl', action='store_true',
                        help='Use SSL connection')
    parser.add_argument('-s', '--server', default='smtp.mail.ru:25',
                        help='Server and port')
    parser.add_argument('-t', '--to', help='Recipient address')
    parser.add_argument('-f', '--login', '--from', default='<>',
                        metavar='sender', help='Sender address')
    parser.add_argument('--subject', default='Happy Pictures',
                        help='Subject of mail')
    parser.add_argument('--auth', action='store_true',
                        help='Request authentication')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbose mode')
    parser.add_argument('-d', '--directory', default=os.getcwd(),
                        help='Source of images')
    return parser.parse_args()
