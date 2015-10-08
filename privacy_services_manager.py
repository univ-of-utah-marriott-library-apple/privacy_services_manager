#!/usr/bin/env python

import argparse
import privacy_services_management as psm
import sys

# Check that management_tools is installed.
try:
    from management_tools import loggers
    from management_tools.app_info import AppInfo
except ImportError as e:
    print("You need version 1.6.0 or greater of the 'Management Tools' module to be installed first.")
    print("https://github.com/univ-of-utah-marriott-library-apple/management_tools")
    raise e

def main(apps, service, action, user, template, language, logger, forceroot, no_check, no_check_type):
    # Output some information.
    output = '#' * 80 + '\n' + version() + '''
    service:  {service}
    action:   {action}
    app(s):   {apps}
'''.format(
        service = service,
        action  = action,
        apps    = apps
)
    if user:
        output += '''\
    user:     {user}
'''.format(user = user)
    else:
        output += '''\
    template: {template}
    language: {language}
'''.format(
        template = template,
        language = language
)
    logger.info(output, print_out = False)

    # Do the actual modifying of the services.
    if len(apps) == 0:
        apps.append(None)
    with psm.universal.get_editor(
        service         = service,
        logger          = logger,
        user            = user,
        template        = template,
        lang            = language,
        forceroot       = forceroot,
        no_check        = no_check,
        no_check_type   = no_check_type,
    ) as e:
        if action == 'add' or action == 'enable':
            for app in apps:
                e.insert(app)
        elif action == 'remove':
            for app in apps:
                e.remove(app)
        elif action == 'disable':
            for app in apps:
                e.disable(app)
        else:
            logger.error("Invalid action '" + action + "'.")

    # Notify of successful completion.
    logger.info("Successfully completed.")

def version():
    """
    :return: the version information for this program
    """
    return (
        "{name}, version {version}\n".format(
        name=psm.universal.attributes['long_name'],
        version=psm.universal.attributes['version'])
    )

def usage(short=False):
    """
    Prints out usage information.
    """

    if not short:
        print(version())

    print('''\
usage: {name} [-hvn] [-l log] [-u user]
         [--template] [--language] action service applications

Modify access to the various privacy services of OS X, such as Contacts, iCloud,
Accessibility, Calendars, Reminders, and Locations.

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
    --forceroot
        Force the script to allow the creation or modification of the root
        user's own TCC database file.
    --no-check-app, --no-check-bin
        Enables administrative override, which allows you to modify services
        for non-bundled applications (such as binary programs used from the
        command line) or applications which maybe don't exist at execution time
        (useful for sysadmins looking to prematurely grant permissions to apps
        which are not yet installed on the system).
            Use `--no-check-app` for applications, and `--no-check-bin` for
        binaries. (This distinction is actually very important.)

    -l log, --log-dest log
        Redirect log output to 'log'.
    -u user, --user user
        Modify access only for 'user'. Only applies to certain services.
    --language lang
        Only functions when used with --template. Specifies which User Template
        is modified.\
'''.format(name=psm.universal.attributes['name']))

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
    calendar
        Modify access to your Calendar. This can be used by applications that
        want to set up recurring tasks or perform scheduling.
    reminders
        Allow applications to send you reminders. Permission to use this service
        is often requested along with 'calendar' access.
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
    """
    Custom argument parser for handling error messages nicely.
    """
    def error(self, message):
        print("Error: {}\n".format(message))
        usage(short=True)
        self.exit(2)

#---------------------#
# Program Entry Point #
#---------------------#
if __name__ == '__main__':
    # Create an argument parser and the valid arguments.
    parser = ArgumentParser(add_help=False)
    parser.add_argument('-h', '--help', action='store_true')
    parser.add_argument('-v', '--version', action='store_true')
    parser.add_argument('-n', '--no-log', action='store_true')
    parser.add_argument('-l', '--log-dest')
    parser.add_argument('-u', '--user', default='')
    parser.add_argument('--template', action='store_true')
    parser.add_argument('--language', default='English')
    parser.add_argument('--forceroot', action='store_true')
    parser.add_argument('--no-check-app', action='store_true')
    parser.add_argument('--no-check-bin', action='store_true')
    parser.add_argument('--admin', action='store_true', dest='no_check_bin')
    parser.add_argument('action', nargs='?',
                        choices=['add', 'remove', 'enable', 'disable'],
                        default=None)
    parser.add_argument('service', nargs='?',
                        choices=psm.universal.available_services)
    parser.add_argument('apps', nargs=argparse.REMAINDER)
    
    # Parse the arguments.
    args = parser.parse_args()

    # Print help information and quit.
    if args.help:
        usage()
        sys.exit(0)
    
    # Print version information and quit.
    if args.version:
        print(version())
        sys.exit(0)

    # Set up the logger.
    logger = loggers.get_logger(
        name = psm.universal.attributes['name'],
        log  = not args.no_log,
        path = args.log_dest
    )

    apps      = args.apps if args.apps else []
    service   = args.service
    action    = args.action
    user      = args.user
    template  = args.template
    language  = args.language
    
    if args.no_check_app and args.no_check_bin:
        parser.error("Cannot give both --no-check-app and --no-check-bin.")
    
    if args.no_check_app:
        no_check = True
        no_check_type = 'app'
    elif args.no_check_bin:
        no_check = True
        no_check_type = 'bin'
    else:
        no_check = False
        no_check_type = None
        
    # Output some information.
    output = (
        "{bar}\n"
        "{version}\n"
        "    service:  {service}\n"
        "    action:   {action}\n"
        "    app(s):   {apps}\n"
        "    user:     {user}\n"
        "    template: {template}\n"
        "    language: {language}\n"
    ).format(
        bar      = '#' * 80,
        version  = version(),
        service  = service,
        action   = action,
        apps     = apps,
        user     = user if user else "N/A",
        template = template,
        language = language if template else "N/A"
    )
    
    # Perform checks for necessary bits of information.
    if not args.action:
        print("Error: Must specify an action.")
        logger.error(output)
        sys.exit(1)
    if not args.service:
        print("Error: Must specify a service to modify.")
        logger.error(output)
        sys.exit(1)
    if args.no_check_bin or args.no_check_app:
        logger.warn("Administrative override enabled. Be careful!")
        
    # Run the program!
    try:
        logger.info(output)
        main(
            apps            = args.apps if args.apps else [],
            service         = args.service,
            action          = args.action,
            user            = args.user,
            template        = args.template,
            language        = args.language,
            logger          = logger,
            forceroot       = args.forceroot,
            no_check        = no_check,
            no_check_type   = no_check_type
        )
    except:
        message = (
            str(sys.exc_info()[0].__name__) + ": " +
            str(sys.exc_info()[1].message)
        )
        logger.error(message)
        sys.exit(3)
