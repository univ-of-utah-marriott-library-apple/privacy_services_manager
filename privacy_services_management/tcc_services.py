import os
import sqlite3
import universal

try:
    from management_tools.app_info import AppInfo
except ImportError as e:
    print("You need version 1.6.0 or greater of the 'Management Tools' module to be installed first.")
    print("https://github.com/univ-of-utah-marriott-library-apple/management_tools")
    raise e

# The services have particular names and databases.
# The tuplet is (Service Name, TCC database, Darwin version introduced)
available_services = {
    'accessibility': ('kTCCServiceAccessibility', 'root',  13),
    'contacts':      ('kTCCServiceAddressBook',   'local', 12),
    'icloud':        ('kTCCServiceUbiquity',      'local', 13),
    'calendar':      ('kTCCServiceCalendar',      'local', 13),
    'reminders':     ('kTCCServiceReminders',     'local', 13)
}

class TCCEdit(object):
    """
    Provides a class for modifying the Privacy Services permissions. This class
    was designed to be used in a 'with' statement to ensure proper updating of
    the locationd system. For example:
    
        with TCCEdit() as e:
            # do some stuff to the database
            e.foo()
        # do more stuff
        bar(baz)
    """
    def __init__(
        self,
        service,
        logger,
        user      = '',
        template  = False,
        lang      = 'English',
        forceroot = False,
        admin     = False,
    ):
        # Set the logger for output.
        self.logger = logger

        # If a service is given, stick with that.
        self.service = service

        # If no user is specified, use the current user instead.
        if not user:
            import getpass
            user = getpass.getuser()
        
        # Set the administrative override flag.
        self.admin = admin

        # Check the version of OS X before continuing; only Darwin versions 12
        # and above support the TCC database system.
        try:
            version = int(os.uname()[2].split('.')[0])
        except:
            raise RuntimeError("Could not acquire the OS X version.")
        if version < 12:
            raise RuntimeError("No TCC functionality on this version of OS X.")
        self.version = version

        # Establish database locations.
        local_log_entry = ''
        if template:
            # This script supports the use of the User Template provided by
            # Apple, but only root may modify anything therein.
            if not os.geteuid() == 0:
                raise ValueError("Only root user may modify the User Template.")
            self.local_path = ('/System/Library/User Template/{}.lproj/Library/Application Support/com.apple.TCC/TCC.db'.format(lang))
            
            # This is the beginning of the log entry. It'll be completed below.
            local_log_entry = ("Set to modify local permissions for the '{}' User Template at ".format(lang))
        else:
            if user == 'root' and not forceroot:
                if available_services[service][1] != 'root':
                    # Prevent the root user from creating or modifying their own
                    # local TCC database. This is to prevent confusion. The file
                    # can be forced to be used by the `--forceroot` option.
                    #
                    # If the service being modified is root-level, don't bother
                    # checking for the local TCC database file because it is
                    # irrelevant.
                    error = '''\
Will not create a TCC database file for root.

Creating a TCC database for the root user is generally not helpful, and
there is really no good reason to do it.

If you intended to change the permissions for a particular user as root,
instead use the `--user` option. For example:

    privacy_services_manager.py --user "username" add contacts com.apple.Safari

If you really want to create a TCC database file for root, run the
command with the `--forceroot` option:

    privacy_services_manager.py --forceroot add contacts com.apple.Safari'''
                    raise ValueError(error)
                else:
                    self.local_path = None
            else:
                self.local_path = os.path.expanduser('~{}/Library/Application Support/com.apple.TCC/TCC.db'.format(user))
                
                # This is the beginning of the log entry. It'll be completed
                # below.
                local_log_entry = ("Set to modify local permissions for user '{}' at ".format(user))

        # Check the user didn't supply a bad username.
        if self.local_path and not self.local_path.startswith('/'):
            # The path to the home directory of 'user' couldn't be found by the
            # system. Maybe the user exists but isn't registered as a user?
            # Try looking in /Users/ just to see:
            if os.path.isdir('/Users/{}'.format(user)):
                self.local_path = ('/Users/{}/Library/Application Support/com.apple.TCC/TCC.db'.format(user))
            else:
                raise ValueError("Invalid username supplied: " + user)

        if self.local_path:
            self.logger.info(local_log_entry + "'" + self.local_path + "'.")
        self.root_path = '/Library/Application Support/com.apple.TCC/TCC.db'
        self.logger.info("Set to modify global permissions for all users at '{}'.".format(self.root_path))

        # Ensure the databases exist properly.
        if os.geteuid() == 0 and not os.path.exists(self.root_path):
            self.__create(self.root_path)
        if self.local_path and not os.path.exists(self.local_path):
            if (user == 'root' and forceroot) or user != 'root':
                self.__create(self.local_path)

        # Check there is write access to user's local TCC database.
        if self.local_path and not os.access(self.local_path, os.W_OK):
            if (user == 'root' and forceroot) or user != 'root':
                raise ValueError("You do not have permission to modify {}'s TCC database.".format(user))

        # Create the connections.
        # Only root may modify the global TCC database.
        if os.geteuid() == 0:
            self.root = sqlite3.connect(self.root_path)
        else:
            self.root = None
        if self.local_path:
            self.local = sqlite3.connect(self.local_path)
        else:
            self.local = None
        self.connections = {'root': self.root, 'local': self.local}

    def insert(self, target, service=None):
        """
        Enable the specified target for the given service.
        
        :param target: an application or file to modify permissions for
        :param service: a service name to modify
        """
        # Validate that they didn't pass us something nonexistent.
        if target is None:
            return
        
        # If not using admin override mode, look up a bundle identifier.
        client_type = 0
        if not self.admin:
            target = AppInfo(target).bid
        else:
            target = os.path.abspath(target)
            # We'll treat this as a command line executable.
            client_type = 1
        
        # If the service was not specified, get the original.
        if service is None and self.service:
            service = self.service
        else:
            return

        # Don't beat up the user for doing something like "AcCeSsIbILITy".
        service = service.lower()

        # Check that the service is known to the program; I do not intend to
        # support unsupported services here.
        if not service in available_services.keys():
            raise ValueError("Invalid service provided: {}".format(service))

        # Version checking for the current service.
        if self.version < available_services[service][2]:
            raise RuntimeError("Service '{}' does not exist on this version of OS X.".format(service))

        # Proceed.
        self.logger.info("Inserting '{}' in service '{}'...".format(target, service))

        # Establish a connection with the TCC database.
        connection = self.connections[available_services[service][1]]

        # Clearly you tried to modify something you weren't supposed to!
        # For shame.
        if not connection:
            if os.geteuid() != 0:
                raise ValueError("Must be root to modify '{}'".format(service))
            else:
                raise ValueError("Unable to connect to '{}'".format(service))

        c = connection.cursor()

        # Add the entry!
        # Prior to OS X 10.8 (Darwin 12) there was no TCC database.
        # In OS X 10.9 (Darwin 13) Apple added a 'csreq' field.
        # In OS X 10.11 (Darwin 15) Apple added a 'policy_id' field.
        values = (available_services[service][0], target, client_type)
        if self.version == 12:
            c.execute('INSERT or REPLACE into access values(?, ?, ?, 1, 0)', values)
        elif 15 > self.version > 12:
            c.execute('INSERT or REPLACE into access values(?, ?, ?, 1, 0, NULL)', values)
        elif self.version >= 15:
            c.execute('INSERT or REPLACE into access values(?, ?, ?, 1, 0, NULL, NULL)', values)
        connection.commit()

        self.logger.info("Inserted successfully.")

    def remove(self, target, service=None):
        """
        Remove an item from Privacy Services for the given service.

        :param target: an application or file to modify permissions for
        :param service: a particular service to modify the permissions within
        """
        # Validate that they didn't pass us something nonexistent.
        if target is None:
            return
        
        # If not using admin override mode, look up a bundle identifier.
        if not self.admin:
            target = AppInfo(target).bid
        else:
            target = os.path.abspath(target)
        
        # If the service was not specified, get the original.
        if service is None and self.service:
            service = self.service
        else:
            return

        # Be nice to the user.
        service = service.lower()

        # Check the service is recognized.
        if not service in available_services.keys():
            raise ValueError("Invalid service provided: " + service)

        self.logger.info("Removing '{}' from service '{}'...".format(target, service))

        # Establish a connection with the TCC database.
        connection = self.connections[available_services[service][1]]

        # Validate that the connection was successful.
        if not connection:
            raise ValueError("Must be root to modify this service!")

        c = connection.cursor()

        # Perform the deletion.
        values = (available_services[service][0], target)
        c.execute('DELETE FROM access WHERE service IS ? AND client IS ?', values)
        connection.commit()

        self.logger.info("Removed successfully.")

    def disable(self, target, service=None):
        """
        Mark the application or file as being disallowed from utilizing Privacy
        Services. If the target is not already in the database, it will be added
        and then disabled.

        :param target: an application or file to modify permissions for
        :param service: the service to modify
        """
        # Validate that they didn't pass us something nonexistent.
        if target is None:
            return
        
        # If not using admin override mode, look up a bundle identifier.
        client_type = 0
        if not self.admin:
            target = AppInfo(target).bid
        else:
            target = os.path.abspath(target)
            # We'll treat this as a command line executable.
            client_type = 1
        
        # If the service was not specified, get the original.
        if service is None and self.service:
            service = self.service
        else:
            return

        # Be nice to the user.
        service = service.lower()

        # Check the service is recognized.
        if not service in available_services.keys():
            raise ValueError("Invalid service provided: {}".format(service))

        self.logger.info("Disabling '{}' in service '{}'...".format(target, service))

        # Establish a connection with the TCC database.
        connection = self.connections[available_services[service][1]]

        # Validate that the connection was successful.
        if not connection:
            raise ValueError("Must be root to modify this service!")

        c = connection.cursor()

        # Disable the application for the given service.
        # The 'prompt_count' must be 1 or else the system will ask the user
        # anyway. This is the only time it seems to really matter.
        values = (available_services[service][0], target, client_type)
        c.execute('SELECT count(*) FROM access WHERE service IS ? and client IS ?', values[0:2])
        count = c.fetchone()[0]
        if count:
            if self.version == 12:
                c.execute('INSERT or REPLACE into access values(?, ?, ?, 0, 1)', values)
            elif 15 > self.version > 12:
                c.execute('INSERT or REPLACE into access values(?, ?, ?, 0, 1, NULL)', values)
            elif self.version >= 15:
                c.execute('INSERT or REPLACE into access values(?, ?, ?, 0, 1, NULL, NULL)', values)
        connection.commit()

        self.logger.info("Disabled successfully.")

    def __create(self, path):
        """
        Creates a fresh TCC database at the given path.
        
        These databases have a very particular format - don't change this!
        
        :param path: where to build the database
        """

        self.logger.info("TCC.db file was expected at '{}' but was not found. Creating new TCC.db file...".format(path))

        # Make sure our directory tree exists.
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path), int('700', 8))

        # Form an SQL connection with the file.
        connection = sqlite3.connect(path)
        c = connection.cursor()

        # Create the tables.
        c.execute("CREATE TABLE admin (key TEXT PRIMARY KEY NOT NULL, value INTEGER NOT NULL)")

        if self.version < 15:
            c.execute("INSERT INTO admin VALUES ('version', 7)")
        else:
            c.execute("INSERT INTO admin VALUES ('version', 8)")

        # This table's formatting is version-sensitive.
        access_table = (
            "CREATE TABLE access "
            "(service TEXT NOT NULL, "
            "client TEXT NOT NULL, "
            "client_type INTEGER NOT NULL, "
            "allowed INTEGER NOT NULL, "
            "prompt_count INTEGER NOT NULL, "
        )
        if 15 > self.version > 12:
            access_table += "csreq BLOB, "
        if self.version >= 15:
            access_table += (
                "policy_id INTEGER, "
                "PRIMARY KEY (service, client, client_type), "
                "FOREIGN KEY (policy_id) REFERENCES policies(id) "
                "ON DELETE CASCADE "
                "ON UPDATE CASCADE)"
            )
        else:
            access_table += "CONSTRAINT key PRIMARY KEY (service, client, client_type))"
        c.execute(access_table)

        c.execute(
                "CREATE TABLE access_times "
                "(service TEXT NOT NULL, "
                "client TEXT NOT NULL, "
                "client_type INTEGER NOT NULL, "
                "last_used_time INTEGER NOT NULL, "
                "CONSTRAINT key PRIMARY KEY (service, client, client_type))"
        )
        c.execute(
                "CREATE TABLE access_overrides "
                "(service TEXT PRIMARY KEY NOT NULL)"
        )
        
        if self.version >= 15:
            # There are some extra tables to add.
            c.execute(
                "CREATE TABLE policies "
                "(id INTEGER NOT NULL PRIMARY KEY, "
                "bundle_id TEXT NOT NULL, "
                "uuid TEXT NOT NULL, "
                "display TEXT NOT NULL, "
                "UNIQUE (bundle_id, uuid))"
            )
            c.execute(
                "CREATE TABLE active_policy "
                "(client TEXT NOT NULL, "
                "client_type INTEGER NOT NULL, "
                "policy_id INTEGER NOT NULL, "
                "PRIMARY KEY (client, client_type), "
                "FOREIGN KEY (policy_id) REFERENCES policies(id) "
                "ON DELETE CASCADE "
                "ON UPDATE CASCADE)"
            )
            c.execute("CREATE INDEX active_policy_id ON active_policy(policy_id)")

        connection.commit()
        connection.close()

        self.logger.info("TCC.db file created successfully.")

    def __enter__(self):
        """
        Allows for the TCCEdit object to be used in a 'with' clause.
        """
        return self

    def __exit__(self, type, value, traceback):
        """
        Allows for the TCCEdit object to be used in a 'with' clause.
        
        Properly closes all connections when the item is trashed.
        """
        if self.root:
            self.root.close()
        if self.local:
            self.local.close()
