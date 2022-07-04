from argparse import ArgumentParser


def parse_args():
    parser = ArgumentParser(description='The program outputs the route (traceroute) and the numbers of'
                                        ' autonomous systems of intermediate nodes, using the responses of '
                                        'the whois service of regional registrars.')
    parser.add_argument('host', help='Host you want to trace')
    return parser.parse_args()
