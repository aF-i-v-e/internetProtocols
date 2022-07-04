from port_scanner import PortScanner
from argparse import *

parser = ArgumentParser(description='Port Scanner')
parser.add_argument('host', action='store', help='Host for scan')
parser.add_argument('-t', action='store_true', help='TCP port scan')
parser.add_argument('-u', action='store_true', help='UDP port scan')
parser.add_argument('-p', '--ports', action='store', nargs=2, type=int,
                    default=[1, 65535], help='Port scan range. Default from 1 to 65535')

if __name__ == "__main__":
    args = parser.parse_args()
    scanner = PortScanner(args)
    scanner.scan()
