import os
import subprocess
import universal

try:
    from management_tools.plist_editor import PlistEditor
    from management_tools.app_info import AppInfo
except ImportError as e:
    print("You need version 1.6.0 or greater of the 'Management Tools' module to be installed first.")
    print("https://github.com/univ-of-utah-marriott-library-apple/management_tools")
    raise e

class LSEdit(object):
    """
    Provides a class for modifying the Location Services permissions. This class
    was designed to be used in a 'with' statement to ensure proper updating of
    the locationd system. For example:
    
        with LSEdit() as e:
            # do some stuff to the database
            e.foo()
        # do more stuff
        bar(baz)
    """
    def __init__(self, logger, no_check=False, no_check_type=None):
        # Set the logger for output.
        self.logger = logger
    
        # Set the administrative override flag.
        self.no_check = no_check
        # Check what type of application we're adding.
        if self.no_check and no_check_type == 'app':
            raise RuntimeError("Location Services does not support adding applications with the `--no-check-app` flag.")

        # Only root may modify the Location Services system.
        if os.geteuid() != 0:
            raise RuntimeError("Must be root to modify Location Services!")

        # Check the version of OS X before continuing; only Darwin versions 10
        # and above support the location services system.
        try:
            version = int(os.uname()[2].split('.')[0])
        except:
            raise RuntimeError("Could not acquire the OS X version.")
        if version < 10:
            raise RuntimeError("Location Services is not supported in this version of OS X.")
        self.version = version

        # Disable the locationd launchd item. (Changes will not be properly
        # cached if this is not done.)
        self.__disable()
        # This is where the applications' authorizations are stored.
        self.plist = PlistEditor('/var/db/locationd/clients')
        self.logger.info("Modifying service 'location' at '{}'.".format(self.plist.path))

    def insert(self, target):
        """
        Enable the specified target for location services.
        
        :param target: an application or file to modify permissions for
        """
        # If no application is given, then we're modifying the global Location
        # Services system.
        if not target:
            self.logger.info("Enabling service 'location' globally.")
            enable_global(True, self.logger)
            self.logger.info("Globally enabled successfully.")
            return
        
        # If we're in admin mode, we can't look up the application as a bundle.
        if self.no_check:
            self.__insert_executable(target)
        else:
            self.__insert_app(target)

    def remove(self, target):
        """
        Remove an item from Location Services. If no item is given, then disable
        Location Services globally.

        :param target: an application or file to modify permissions for
        """
        # If no application is given, then we're modifying the global Location
        # Services system.
        if not target:
            self.logger.info("Disabling service 'location' globally...")
            enable_global(False, self.logger)
            self.logger.info("Globally disabled successfully.")
            return
        
        if self.no_check:
            name   = target
            target = 'com.apple.locationd.executable-{}'.format(target)
        else:
            name   = AppInfo(target).name
            target = AppInfo(target).bid

        # Verbosity
        self.logger.info("Removing '{}' from service 'location'...".format(target))

        # Otherwise, just delete its entry in the plist.
        result = self.plist.delete(target)
        if result:
            raise RuntimeError("Failed to remove {}.".format(name))
        self.logger.info("Removed successfully.")

    def disable(self, target):
        """
        Mark the application or file as being disallowed from utilizing Location
        Services. If the target is not already in the plist, it will be added
        and then disabled.

        :param target: an application or file to modify permissions for
        """
        # If no application is given, then we're modifying the global Location
        # Services system.
        if not target:
            self.logger.info("Disabling service 'location' globally...")
            enable_global(False, self.logger)
            self.logger.info("Globally disabled successfully.")
            return

        if self.no_check:
            name   = target
            target = 'com.apple.locationd.executable-{}'.format(target)
        else:
            name   = AppInfo(target).name
            target = AppInfo(target).bid

        # Verboseness
        self.logger.info("Disabling '{}' in service 'location'...".format(target))

        # If the application isn't already in locationd, add it.
        if not self.plist.read(target):
            self.insert(target)

        # Then deauthorize the application.
        result = self.plist.dict_add(target, "Authorized", "FALSE", "bool")
        if result:
            raise RuntimeError("Failed to disable {}.".format(name))
        self.logger.info("Disabled successfully.")

    def __insert_app(self, target):
        """
        Inserts the specified target application into the locationd plist.
        """
        # Get the AppInfo object for more information.
        app = AppInfo(target)

        # Verbosity!
        self.logger.info("Inserting '{}' into service 'location'...".format(app.bid))

        # This is used for... something. Don't know what, but it's necessary.
        requirement = ("identifier \"{}\" and anchor {}".format(
            app.bid, app.bid.split('.')[1]
        ))

        # Write the changes to the locationd plist.
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
            # Clearly there was an error...
            raise RuntimeError("Failed to insert {}.".format(app.name))
        self.logger.info("Inserted successfully.")

    def __insert_executable(self, target):
        """
        Inserts the specified target executable into the locationd plist.
        """
        # Verbosity!
        self.logger.info("Inserting executable '{}' into service 'location'...".format(target))
        
        # Reformat the target name.
        key = 'com.apple.locationd.executable-{}'.format(target)
        
        # Find the Code Directory Hash (CDHash).
        # If the command exits with a non-zero exit status, report to the user.
        # This generally indicates it does not have a code signature.
        try:
            codesign = subprocess.check_output(
                ['/usr/bin/codesign', '--display', '--verbose=4', target],
                stderr=subprocess.STDOUT
            ).split('\n')
        except subprocess.CalledProcessError:
            self.logger.warn("Executable '{}' is not signed. Adding anyway...".format(target))
            codesign = []
        
        # Filter the results.
        codesign = [x for x in codesign if x is not None and x != '']
        codesign = [x for x in codesign if '=' in x]
        # After this, 'cdhash' will either be an empty list (no match), or else
        # it should have one element with the cdhash in it.
        cdhash = [x.split('=')[1] for x in codesign if 'CDHash' in x]
        
        # Build the requirement string from the cdhash if we have one.
        if len(cdhash) == 1:
            requirement = ("cdhash H\"{cdhash}\"".format(cdhash=cdhash[0]))
        else:
            requirement = None
        
        # Write the changes to the locationd plist.
        result = 0
        result += self.plist.dict_add(key, "Authorized", "TRUE", "bool")
        result += self.plist.dict_add(key, "BundleID", key)
        result += self.plist.dict_add(key, "BundleId", key)
        result += self.plist.dict_add(key, "Executable", target)
        result += self.plist.dict_add(key, "Registered", target)
        result += self.plist.dict_add(key, "Hide", 0, "int")
        if requirement:
            result += self.plist.dict_add(key, "Requirement", requirement)
        result += self.plist.dict_add(key, "Whitelisted", "FALSE", "bool")
        if result:
            # There was an error.
            raise RuntimeError("Failed to insert executable {}.".format(target))
        self.logger.info("Inserted successfully.")

    def __enter__(self):
        """
        Allows for the LSEdit object to be used in a 'with' clause.
        """
        return self

    def __exit__(self, type, value, traceback):
        """
        Allows for the LSEdit object to be used in a 'with' clause.
        """
        # Make sure that the locationd launchd item is reactivated.
        self.__enable()

    def __enable(self):
        """
        Enables the locationd system.
        """
        enable()
        self.logger.info("Enabled locationd system.")

    def __disable(self):
        """
        Disables the locationd system.
        """
        disable()
        self.logger.info("Disabled locationd system. (This is normal. DON'T PANIC.)")

def enable_global(enable, logger):
    """
    Enables or disables the Location Services system globally.
    
    :param enable: a boolean describing whether the LS system should be enabled
    :param logger: a management_tools.loggers logger for recording output
    """
    # Get the Universally Unique Identifier for the hardware. This determines
    # the location of the locationd system.
    uuid = get_uuid()
    ls_dir = '/var/db/locationd/Library/Preferences/ByHost/'
    ls_plist = ls_dir + 'com.apple.locationd.' + str(uuid) + '.plist'
    logger.info("Modifying global values in '" + ls_plist + "'.")

    # Depending on settings, there may be a few possible files to use as the
    # locationd plist.
    if not os.path.isfile(ls_plist):
        ls_plist = None
        # Find everything starting with 'com.apple.locationd' and ending with
        # the '.plist' extension.
        potentials = [
            x.lstrip('com.apple.locationd.').rstrip('.plist')
            for x in os.listdir(ls_dir)
            if str(x).endswith('.plist')
            and str(x).startswith('com.apple.locationd.')
        ]
        potentials = [x for x in potentials if not x.find('.') >= 0]
        
        # Must handle things differently depending on the number of results.
        if len(potentials) > 1:
            # Out of all the matches, try to find the one that matches the UUID.
            for id in potentials:
                if uuid == id or uuid.lower() == id or uuid.upper() == id:
                    ls_plist = ('{}com.apple.locationd.{}.plist'.format(ls_dir, id))
                    break
                
                for part in uuid.split('-'):
                    if part == id or part.lower() == id or part.upper() == id:
                        ls_plist = ('{}com.apple.locationd.{}.plist'.format(ls_dir, id))
                        break
                
                # If we've found it, break out of this loop.
                if ls_plist:
                    break
        elif len(potentials) == 1:
            # Only one result - that's easy!
            ls_plist = (ls_dir + 'com.apple.locationd.{}.plist'.format(potentials[0]))
        else:
            raise RuntimeError("No Location Services global property list found at '{}'.".format(ls_plist))

    # Write the location services status (enabled or not).
    if ls_plist:
        ls_plist = PlistEditor(ls_plist)
        value = 1 if enable else 0
        ls_plist.write("LocationServicesEnabled", value, "int")
    else:
        raise RuntimeError("Could not locate Location Services plist file at '{}.".format(ls_plist))

def get_uuid():
    """
    Acquire the Universally Unique Identifier of the hardware.
    """
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

    return uuid[0].lstrip().rstrip('"').split('= "')[1]

def enable():
    """
    Fix permissions for the _locationd user, then load the locationd launchd
    daemon item.
    """
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
        '/bin/launchctl',
        'load',
        '/System/Library/LaunchDaemons/com.apple.locationd.plist'
    ]

    output = subprocess.check_output(
        launchctl,
        stderr=subprocess.STDOUT
    ).strip('\n')

    return output

def disable():
    """
    Unload the locationd launchd daemon item.
    """
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
