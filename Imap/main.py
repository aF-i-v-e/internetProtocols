from IMAPException import IMAPException
from IMAPClient import IMAP
from socket import gaierror, timeout

from my_parser import parse_args

if __name__ == '__main__':
    try:
        args = parse_args()
        smtp_client = IMAP(args.ssl, args.server, args.n, args.user)
        # main.py --ssl -s imap.mail.ru:993 -n 5 -u ee-tester@mail.ru
        #smtp_client = IMAP(True, 'imap.mail.ru:993', '2', 'ee-tester@mail.ru')
        smtp_client.run()
    except (IMAPException, ValueError) as e:
        print(e)
        exit(1)
    except gaierror:
        print('Failed to connect server (DNS Error)')
        exit(1)
    except timeout:
        print('Failed to get response from server')
        exit(1)
    except KeyboardInterrupt:
        print('Terminated.\n')
        exit()