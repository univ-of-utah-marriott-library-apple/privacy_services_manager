import location_services
import tcc_services

# This is a list of services we can modify. Useful for scripts to call on.
available_services = tcc_services.available_services.keys() + ['location']

def get_editor(service, user='', template=False, lang='English'):
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
                lang     = lang
            )
        else:
            # Otherwise, return an editor for Location Services.
            return location_services.LSEdit()

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
                "https://github.com/univ-of-utah-marriott-library-apple/\
                management_tools")
            raise e

        if not log:
            self.logger = loggers.stream_logger(1)
        else:
            if log_dest:
                self.logger = loggers.file_logger(name, path=log_dest)
            else:
                self.logger = loggers.file_logger(name)

    def info(self, information):
        print(information)
        self.logger.info(information)

    def error(self, information):
        print("Error: " + information)
        self.logger.error(information)
