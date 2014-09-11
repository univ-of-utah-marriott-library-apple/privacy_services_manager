import location_services
import tcc_services

# Common attributes of the module and script.
attributes = {
    'long_name': "Privacy Services Manager",
    'name':      "privacy_services_manager",
    'version':   "1.4.0",
}

# This is a list of services which can be modified.
# Useful for scripts to call on for a neat list.
available_services = tcc_services.available_services.keys() + ['location']

def get_editor(service, user='', template=False, lang='English', logger=None):
    '''Returns the appropriate type of editor for the given service. This allows
    for a more generalized approach in other scripts, as opposed to having to
    handle all of this there.
    '''

    # Only return something if we have an editor for it!
    if service not in available_services:
        raise ValueError("Invalid service: " + str(service))
    else:
        if service in tcc_services.available_services.keys():
            # If it's in the TCC services, return a pre-formatted one of those.
            return tcc_services.TCCEdit(
                service  = service,
                user     = user,
                template = template,
                lang     = lang,
                logger   = logger,
            )
        else:
            # Otherwise, return an editor for Location Services.
            return location_services.LSEdit(logger=logger)

class Output(object):
    '''Relays information to the user, both through the console and through
    logging that information.
    '''

    def __init__(self, name, log, log_dest=''):
        try:
            from management_tools import loggers
        except ImportError as e:
            print(
                "You need the 'Management Tools' module to be installed first.")
            print(
                "https://github.com/univ-of-utah-marriott-library-apple/" +
                "management_tools")
            raise e

        if not log:
            self.logger = loggers.stream_logger(1)
        else:
            if log_dest:
                self.logger = loggers.file_logger(name, path=log_dest)
            else:
                self.logger = loggers.file_logger(name)

    def info(self, information, print_out=True, log=True):
        if print_out:
            print(information)
        if log:
            self.logger.info(information)

    def error(self, information, print_out=True, log=True):
        if print_out:
            print("Error: " + information)
        if log:
            self.logger.error(information)

class NullOutput(object):
    '''Doesn't do anything. Just has the methods so that nobody gets upset.'''

    def __init__(self):
        pass

    def info(self, information):
        pass

    def error(self, information):
        pass
