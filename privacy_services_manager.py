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

def main(apps, service, action, user, template, language):
    if action == 'add' or action == 'enable':
            with psm.universal.get_editor(service, user, template, language) as e:
                if len(apps) == 0:
                    e.insert(None)
                for app in apps:
                    if app:
                        e.insert(app)
                        entry = "Added '" + app + "' to service '" + service + "'"
                        if user:
                            entry += " for user '" + user + "'."
                        elif template:
                            entry += " for the User Template."
                        else:
                            entry += "."
                        logger.info(entry)
    elif action == 'remove':
        with psm.universal.get_editor(service, user, template, language) as e:
            if len(apps) == 0:
                e.remove(None)
            for app in apps:
                if app:
                    e.remove(app)
                    entry = ("Removed '" + app + "' from service '" +
                             service + "'")
                    if user:
                        entry += " for user '" + user + "'."
                    elif template:
                        entry += " for the User Template."
                    else:
                        entry += "."
                    logger.info(entry)
    elif action == 'disable':
        with psm.universal.get_editor(service, user, template, language) as e:
            if len(apps) == 0:
                e.disable(None)
            for app in apps:
                if app:
                    e.disable(app)
                    entry = ("Disabled '" + app + "' from service '" +
                             service + "'")
                    if user:
                        entry += " for user '" + user + "'."
                    elif template:
                        entry += " for the User Template."
                    else:
                        entry += "."
                    logger.info(entry)

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
Accessibility, and Locations.

    -h, --help
        Prints this help message and quits.
    -v, --version
        Prints the version information and quits.
    -n, --no-log
        Prevent logs from being written to files.
        (All information that would be logged is redirected to stdio.)
    --template
        Modify access only for Apple's User Template. Only applies to certain
        services.

    -l log, --log-dest log
        Redirect log output to 'log'.
    -u user, --user user
        Modify access only for 'user'. Only applies to certain services.
    --language lang
        Only functions when used with --template. Specifies which User Template
        is modified.\
'''.format(name=options['name']))

    if not short:
        print('''
ACTION
    add
        Adds applications to the service and enable them.
    enable
        Ensures applications are added to the service and enabled.
        (This is effectively the same as 'add'.)
    remove
        Removes all traces of the applications for the service.
    disable
        Deauthorizes the applications from the service but leaves their entries
        in place. This is useful if you want to explicitly prevent an
        application from using a service.

SERVICE
    contacts
        Access to the AddressBook feature. Used by applications that want to
        know who you know.
    accessibility
        Permission to modify system-level settings. Applications that integrate
        with your desktop require accessibility access.
        NOTE: Must be modified by root.
    icloud
        Permission to access iCloud storage? Unsure exactly - currently this is
        only used by Apple-built applications.
    location
        Modifies the Location Services system. Any application that wants to
        know your physical locations (e.g. Maps) will use this.
        NOTE: Must be modified by root.

APPLICATIONS
    Application names can be specified in a few ways, assuming the applications
    were produced properly:

    1. Short name
            If Spotlight can find something from a string, it'll work here. I
            don't really recommend depending on it in deployment environments,
            though.
                e.g. safari
    2. Bundle identifier
            A (supposedly) unique string in reverse-DNS format which identifies
            a particular application.
                e.g. com.apple.Safari
    3. Bundle path location
            The absolute path to an application's .app bundle.
                e.g. /Applications/Safari.app\
''')

class ArgumentParser(argparse.ArgumentParser):
    '''I like my own style of error-handling, thank you.'''

    def error(self, message):
        print("Error: {}\n".format(message))
        usage(short=True)
        self.exit(2)

def setup_logger(log, log_dest):
    global logger
    if not log:
        logger = loggers.stream_logger(1)
    else:
        if log_dest:
            logger = loggers.file_logger(options['name'], path=log_dest)
        else:
            logger = loggers.file_logger(options['name'])

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
    parser.add_argument('apps', nargs=argparse.REMAINDER)
    args = parser.parse_args()

    if args.help:
        usage()
    elif args.version:
        version()
    else:
        setup_logger(log = not args.no_log, log_dest = args.log_dest)
        if not args.action:
            print("Error: Must specify an action.")
            sys.exit(1)
        if not args.service:
            print("Error: Must specify a service to modify.")
            sys.exit(1)
        try:
            main(
                apps = args.apps if args.apps else [],
                service = args.service,
                action = args.action,
                user = args.user,
                template = args.template,
                language = args.language,
            )
        except:
            message = (
                str(sys.exc_info()[0].__name__) + ": " +
                str(sys.exc_info()[1].message)
            )
            print(message)
            logger.error(message)
            sys.exit(3)
