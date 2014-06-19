import os
import subprocess

try:
    from management_tools.plist_editor import PlistEditor
    from management_tools.app_info import AppInfo
except ImportError as e:
    print "You need the 'Management Tools' module to be installed first."
    print "https://github.com/univ-of-utah-marriott-library-apple/management_tools"
    raise e

class LSEdit(object):
    def __init__(self):
        if os.geteuid() != 0:
            raise RuntimeError("Must be root to modify Location Services!")
        self.__disable()
        self.plist = PlistEditor('/var/db/locationd/clients')

    def __enter__(self):
        return self

    def insert(self, bid):
        if not bid:
            enable_global(True)
            return

        app = AppInfo(bid)

        requirement = (
            "identifier \"" + app.bid _ "\" and anchor " +
            app.bid.split('.')[1]
        )

        result = 0
        result += self.plist.dict_add(app.bid, "Authorized", "TRUE", "bool")
        result += self.plist.dict_add(app.bid, "BundleID", app.bid)
        result += self.plist.dict_add(app.bid, "BundleId", app.bid)
        result += self.plist.dict_add(app.bid, "BundlePath", app.path)
        result += self.plist.dict_add(app.bid, "Executable", app.executable)
        result += self.plist.dict_add(app.bid, "Registered", app.executable)
        result += self.plist.dict_add(app.bid, "Hide", 0, "int")
        result += self.plist.dict_add(app.bid, "Requirement", requirement)
        result += self.plist.dict_add(app.bid, "Whitelisted", "FALSE", "bool")
        if result:
            raise RuntimeError("Failed to add " + app.name + ".")

    def remove(self, bid):
        if not bid:
            enable_global(False)
            return

        app = AppInfo(bid)

        result = self.plist.delete(app.bid)
        if result:
            raise RuntimeError("Failed to remove " + app.name + ".")

    def __exit__(self, type, value, traceback):
        self.__enable()

    def __enable(self):
        enable()

    def __disable(self):
        disable()

def enable_global(enable):
    '''Enables or disables the Location Services system globally.'''

    try:
        value = int(enable)
    except:
        raise ValueError("'" + str(enable) + "' not a boolean.")

    uuid = get_uuid()

    ls_plist = (
        '/var/db/locationd/Library/Preferences/ByHost/com.apple.locationd.' +
        str(uuid)
    )

    defaults = [
        '/usr/bin/defaults',
        'write',
        ls_plist,
        'LocationServicesEnabled',
        '-int',
        value
    ]

    result = subprocess.call(
        defaults,
        stderr=subprocess.STDOUT,
        stdout=open(os.devnull, 'w')
    )
    return result

def get_uuid():
    '''Acquire the UUID of the hardware.'''

    ioreg = [
        '/usr/sbin/ioreg',
        '-rd1',
        '-c',
        'IOPlatformExpertDevice'
    ]

    uuid = subprocess.check_output(ioreg, stderr=subprocess.STDOUT).split('\n')
    uuid = [x for x in uuid if x.find('UUID') >= 0]

    if len(uuid) != 1:
        raise RuntimeError("Could not find a unique UUID.")

    return uuid[0].lstrip().split('= "')[1]

def enable():
    '''Fix permissions for the _locationd user, then load the locationd
    launchd item.'''

    chown = [
        '/usr/sbin/chown',
        '-R',
        '_locationd:_locationd',
        '/var/db/locationd'
    ]

    result = subprocess.call(
        chown,
        stderr=subprocess.STDOUT,
        stdout=open(os.devnull, 'w')
    )
    if result != 0:
        raise RuntimeError("Unable to repair permissions: '/var/db/locationd'!")

    launchctl = [
        'launchctl',
        'load',
        '/System/Library/LaunchDaemons/com.apple.locationd.plist'
    ]

    output = subprocess.check_output(
        launchctl,
        stderr=subprocess.STDOUT
    ).strip('\n')

    return output

def disable():
    '''Unload the locationd launchd item.'''

    launchctl = [
        '/bin/launchctl',
        'unload',
        '/System/Library/LaunchDaemons/com.apple.locationd.plist'
    ]

    output = subprocess.check_output(
        launchctl,
        stderr=subprocess.STDOUT
    ).strip('\n')

    return output
