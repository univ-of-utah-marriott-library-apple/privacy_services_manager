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
