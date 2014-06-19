import location_services
import tcc_services

available_services = tcc_services.available_services.keys() + ['location']

def get_editor(service, user='', template=False, lang='English'):
    if service not in available_services:
        raise ValueError("Invalid service: " + str(service))
    else:
        if service in tcc_services.available_services.keys():
            return tcc_services.TCCEdit(
                service  = service,
                user     = user,
                template = template,
                lang     = lang
            )
        else:
            return location_services.LSEdit()
