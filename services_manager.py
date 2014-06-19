#!/usr/bin/env python

import argparse
import privacy_services_management as psm
import sys

def main():
    set_globals()
    parse_options()

    for key in options:
        print("{:>20}: {}".format(key, options[key]))

def set_globals():
    global options
    options = {}
    options['long_name'] = "OS X Privacy Services Manager"
    options['name'] = '_'.join(options['long_name'].lower().split())
    options['version'] = psm.__version__

def version():
    '''Prints the version information.'''

    print("{name}, version {version}\n".format(name=options['long_name'],
                                               version=options['version']))

def usage(short=False):
    '''Usage information.'''

    if not short:
        version()

    print('''\
usage: {name} [-hvn] [-l log] [-u user]
         [--template] [--language] action service applications

Modify access to the various privacy services of OS X, such as Contacts, iCloud,
Accessibility, and Locations.\
'''.format(name=options['name']))

class ArgumentParser(argparse.ArgumentParser):
    '''I like my own style of error-handling, thank you.'''

    def error(self, message):
        print("ERROR: {}\n".format(message))
        usage(short=True)
        self.exit(2)

def parse_options():
    '''Parse the command-line options.'''

    available_services = psm.tcc_services.available_services.keys()
    available_services += ['location']

    parser = ArgumentParser(add_help=False)
    parser.add_argument('-h', '--help', action='store_true')
    parser.add_argument('-v', '--version', action='store_true')
    parser.add_argument('-n', '--no-log', action='store_true')
    parser.add_argument('-l', '--log')
    parser.add_argument('-u', '--user')
    parser.add_argument('--template', action='store_true')
    parser.add_argument('--language', default='English')
    parser.add_argument('action', nargs='?',
                        choices=['add', 'remove'], default=None)
    parser.add_argument('service', nargs='?', available_services)
    parser.add_argument('apps', nargs=argparse.REMAINDER)
    args = parser.parse_args()

    if args.help:
        usage()
        sys.exit(0)
    if args.version:
        version()
        sys.exit(0)

    options['log']      = not args.no_log
    options['log_dest'] = args.log
    options['user']     = args.user
    options['template'] = args.template
    options['language'] = args.language
    options['action']   = args.action
    options['service']  = args.service
    options['apps']     = args.apps

if __name__ == '__main__':
    main()
