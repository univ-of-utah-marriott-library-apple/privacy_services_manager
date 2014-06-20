#!/usr/bin/env python

import argparse
import privacy_services_management as psm
import sys

try:
    from management_tools import loggers
except ImportError as e:
    print "You need the 'Management Tools' module to be installed first."
    print "https://github.com/univ-of-utah-marriott-library-apple/management_tools"
    raise e

options = {}
options['long_name'] = "Privacy Services Manager"
options['name']      = '_'.join(options['long_name'].lower().split())
options['version']   = psm.__version__

def main(apps, service, action, user, template, language, log, log_dest):
    if not log:
        logger = loggers.stream_logger(1)
    else:
        if log_dest:
            logger = loggers.file_logger(options['name'], path=log_dest)
        else:
            logger = loggers.file_logger(options['name'])

    if action == 'add' or action == 'enable':
        try:
            with psm.universal.get_editor(service, user, template, language) as e:
                for app in apps:
                    try:
                        e.insert(app)
                    except:
                        logger.error(sys.exc_info()[1].message)
                        continue
                    if app:
                        entry = "Added '" + app + "' to service '" + service + "'"
                        if user:
                            entry += " for user '" + user + "'."
                        elif template:
                            entry += " for the User Template."
                        else:
                            entry += "."
                        logger.info(entry)
        except:
            logger.error(sys.exc_info()[1].message)
            return
    elif action == 'remove':
        try:
            with psm.universal.get_editor(service, user, template, language) as e:
                for app in apps:
                    try:
                        e.remove(app)
                    except:
                        logger.error(sys.exc_info()[1].message)
                        continue
                    if app:
                        entry = ("Removed '" + app + "' from service '" +
                                 service + "'")
                        if user:
                            entry += " for user '" + user + "'."
                        elif template:
                            entry += " for the User Template."
                        else:
                            entry += "."
                        logger.info(entry)
        except:
            logger.error(sys.exc_info()[1].message)
            return
    elif action == 'disable':
        try:
            with psm.universal.get_editor(service, user, template, language) as e:
                for app in apps:
                    try:
                        e.disable(app)
                    except:
                        logger.error(sys.exc_info()[1].message)
                        continue
                    if app:
                        entry = ("Disabled '" + app + "' from service '" +
                                 service + "'")
                        if user:
                            entry += " for user '" + user + "'."
                        elif template:
                            entry += " for the User Template."
                        else:
                            entry += "."
                        logger.info(entry)
        except:
            logger.error(sys.exc_info()[1].message)
            return

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
        print("Error: {}\n".format(message))
        usage(short=True)
        self.exit(2)

if __name__ == '__main__':
    '''Parse the command-line options since this was invoked as a script.'''

    parser = ArgumentParser(add_help=False)
    parser.add_argument('-h', '--help', action='store_true')
    parser.add_argument('-v', '--version', action='store_true')
    parser.add_argument('-n', '--no-log', action='store_true')
    parser.add_argument('-l', '--log-dest')
    parser.add_argument('-u', '--user', default='')
    parser.add_argument('--template', action='store_true')
    parser.add_argument('--language', default='English')
    parser.add_argument('action', nargs='?',
                        choices=['add', 'remove', 'enable', 'disable'],
                        default=None)
    parser.add_argument('service', nargs='?',
                        choices=psm.universal.available_services)
    parser.add_argument('apps', nargs=argparse.REMAINDER, const=None)
    args = parser.parse_args()

    if args.help:
        usage()
    elif args.version:
        version()
    else:
        if not args.action:
            print("Error: Must specify an action.")
            sys.exit(1)
        if not args.service:
            print("Error: Must specify a service to modify.")
            sys.exit(1)
        main(
            apps = args.apps if args.apps else [None],
            service = args.service,
            action = args.action,
            user = args.user,
            template = args.template,
            language = args.language,
            log = not args.no_log,
            log_dest = args.log_dest
        )
