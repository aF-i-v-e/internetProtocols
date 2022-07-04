import my_parser
import socket
import traceroute

if __name__ == '__main__':
    args = my_parser.parse_args()
    destination = args.host
    try:
        tracer = traceroute.Tracer(destination)
        for result in tracer.trace():
            print(f'{result.get_string_representation()}\r\n')
        print("Tracing completed")
    except socket.gaierror:
        print(f'Address {destination} is invalid')
        exit(1)
    except PermissionError:
        print('Not enough rights')
        exit(1)
    except KeyboardInterrupt:
        print('Terminated.')
