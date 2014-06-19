import location_services
import tcc_services

def get_editor(service, user='', template=False, lang='English'):
    if service == 'accessibility':
        return tcc_services.AccessibilityEdit(
            user     = user,
            template = template,
            lang     = lang
        )
    else if service == 'contacts':
        return tcc_services.ContactsEdit(
            user     = user,
            template = template,
            lang     = lang
        )
    else if service == 'icloud':
        return tcc_services.UbiquityEdit(
            user     = user,
            template = template,
            lang     = lang
        )
    else if service == 'location':
        return location_services.LSEdit()
    else:
        raise ValueError("Invalid service: " + str(service))
