import location_services
import tcc_services

# Common attributes of the module and script.
attributes = {
    'long_name': "Privacy Services Manager",
    'name':      "privacy_services_manager",
    'version':   "1.6.7",
}

# This is a list of services which can be modified.
# Useful for scripts to call on for a neat list.
available_services = tcc_services.available_services.keys() + ['location']

def get_editor(service, logger, user='', template=False, lang='English', forceroot=False, admin=False):
    """
    Returns the appropriate type of editor for the given service. This allows
    for a more generalized approach in other scripts, as opposed to having to
    handle all of this there.
    """

    # Only return something if we have an editor for it!
    if service not in available_services:
        raise ValueError("Invalid service: " + str(service))
    else:
        if service in tcc_services.available_services.keys():
            # If it's in the TCC services, return a pre-formatted one of those.
            return tcc_services.TCCEdit(
                service   = service,
                user      = user,
                template  = template,
                lang      = lang,
                logger    = logger,
                forceroot = forceroot,
                admin     = admin,
            )
        else:
            # Otherwise, return an editor for Location Services.
            return location_services.LSEdit(logger=logger, admin=admin)
