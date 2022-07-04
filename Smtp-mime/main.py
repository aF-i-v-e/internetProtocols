from _socket import gaierror

import SMTPException
from my_parser import parse_args
from smtp import SMTP

if __name__ == '__main__':
    try:
        args = parse_args()
        smtp_client = SMTP(args.ssl, args.server, args.to, args.login, args.subject, args.auth
                           , args.verbose, args.directory)
        smtp_client.run()
    except (SMTPException, ValueError) as e:
        print(e)
        exit(1)
    except gaierror:
        print('SMTP server not found! (DNS Error)')
        exit(1)
    except ConnectionError:
        print('Server refuses connection')
        exit(1)
    except KeyboardInterrupt:
        print('Terminated\n')
        exit()
