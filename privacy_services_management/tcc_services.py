import os
import sqlite3
import universal

try:
    from management_tools.app_info import AppInfo
except ImportError as e:
    print "You need the 'Management Tools' module to be installed first."
    print "https://github.com/univ-of-utah-marriott-library-apple/management_tools"
    raise e

# The services have particular names and databases.
# The tuplet is (Service Name, TCC database, Darwin version introduced)
available_services = {
    'accessibility': ('kTCCServiceAccessibility', 'root',  13),
    'contacts':      ('kTCCServiceAddressBook',   'local', 12),
    'icloud':        ('kTCCServiceUbiquity',      'local', 13)
}

class TCCEdit(object):
    '''A class to help with editing the TCC databases. This ought to be used
    in a 'with' statement to ensure proper closing of connections! e.g.

    with TCCEdit() as e:
        # do some stuff to the database
        e.foo()
    # do more stuff to other things
    bar(baz)
    '''

    def __init__(
        self,
        service,
        user      = '',
        template  = False,
        lang      = 'English',
        logger    = None,
        forceroot = False,
    ):
        # Set the logger for output.
        if logger:
            self.logger = logger
        else:
            self.logger = universal.NullOutput()

        # If a service is given, stick with that.
        self.service = service

        # If no user is specified, use the current user instead.
        if not user:
            import getpass
            user = getpass.getuser()

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
            self.local_path = (
                '/System/Library/User Template/' +
                lang +
                '.lproj/Library/Application Support/com.apple.TCC/TCC.db'
            )
            local_log_entry = (
                "Set to modify local permissions for the '" + lang +
                "' User Template at ")
        else:
            if (user == 'root' and
                not forceroot and
                available_services[service][1] != 'root'):
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
                self.local_path = os.path.expanduser(
                    '~' +
                    user +
                    '/Library/Application Support/com.apple.TCC/TCC.db'
                )
                local_log_entry = (
                    "Set to modify local permissions for user '" + user + "' at "
                )

        # Check the user didn't supply a bad username.
        if not self.local_path.startswith('/'):
            # The path to the home directory of 'user' couldn't be found by the
            # system. Maybe the user exists but isn't registered as a user?
            # Try looking in /Users/ just to see:
            if os.path.isdir('/Users/' + user):
                self.local_path = (
                    '/Users/' +
                    user +
                    '/Library/Application Support/com.apple.TCC/TCC.db'
                )
            else:
                raise ValueError("Invalid username supplied: " + user)

        self.logger.info(local_log_entry + "'" + self.local_path + "'.")
        self.root_path = '/Library/Application Support/com.apple.TCC/TCC.db'
        self.logger.info(
            "Set to modify global permissions for all users at '" +
            self.root_path + "'.")

        # Ensure the databases exist properly.
        if os.geteuid() == 0 and not os.path.exists(self.root_path):
            self.__create(self.root_path)
        if not os.path.exists(self.local_path):
            if (user == 'root' and forceroot) or user != 'root':
                self.__create(self.local_path)

        # Check there is write access to user's local TCC database.
        if not os.access(self.local_path, os.W_OK):
            if (user == 'root' and forceroot) or user != 'root':
                raise ValueError(
                    "You do not have permission to modify " + user +
                    "'s TCC database."
                )

        # Create the connections.
        # Only root may modify the global TCC database.
        if os.geteuid() == 0:
            self.root = sqlite3.connect(self.root_path)
        else:
            self.root = None
        if os.geteuid() != 0 or (os.geteuid() == 0 and forceroot):
            self.local = sqlite3.connect(self.local_path)
        else:
            self.local = None
        self.connections = {'root': self.root, 'local': self.local}

    def __enter__(self):
        return self

    def insert(self, app, service=None):
        '''Adds 'app' to the specified service.

        app     - an application identifier
        service - a service name to add to
        '''

        # Validate that they didn't pass us something dumb.
        if app is None:
            return
        else:
            bid = AppInfo(app).bid
        if service is None and self.service:
            service = self.service
        else:
            return

        # Don't beat up the user for doing something like "AcCeSsIbILITy".
        service = service.lower()

        # Check that the service is known to the program; I do not intend to
        # support unsupported services here.
        if not service in available_services.keys():
            raise ValueError("Invalid service provided: " + service)

        # Version checking for the current service.
        if self.version < available_services[service][2]:
            raise RuntimeError(
                "Service '" + service +
                "' does not exist on this version of OS X.")

        self.logger.info("Inserting '" + bid + "' in service '" + service + "'...")

        # Establish a connection with the TCC database.
        connection = self.connections[available_services[service][1]]

        # Clearly you tried to modify something you weren't supposed to!
        # For shame.
        if not connection:
            raise ValueError("Must be root to modify '" + service + "'")

        c = connection.cursor()

        # Add the entry!
        # In OS X 10.9, Apple introduced a "blob". It doesn't seem to be very
        # useful since you can just give it the value "NULL" with no ill
        # effects, but it is necessary in Darwin versions 13 and greater (yet it
        # cannot be given in previous versions without incurring errors).
        values = (available_services[service][0], bid)
        if self.version == 12:
            c.execute(
                'INSERT or REPLACE into access values(?, ?, 0, 1, 0)',
                values
            )
        else:
            c.execute(
                'INSERT or REPLACE into access values(?, ?, 0, 1, 0, NULL)',
                values
            )
        connection.commit()

        self.logger.info("Inserted successfully.")

    def remove(self, app, service=None):
        '''Removes 'app' from the specified service.

        app     - an application identifier
        service - a service name to remove from
        '''

        if app is None:
            return
        else:
            bid = AppInfo(app).bid
        if service is None and self.service:
            service = self.service
        else:
            return

        # Be nice to the user.
        service = service.lower()

        # Check the service is recognized.
        if not service in available_services.keys():
            raise ValueError("Invalid service provided: " + service)

        self.logger.info(
            "Removing '" + bid + "' from service '" + service + "'...")

        # Establish a connection with the TCC database.
        connection = self.connections[available_services[service][1]]

        # Validate that the connection was successful.
        if not connection:
            raise ValueError("Must be root to modify this service!")

        c = connection.cursor()

        # Perform the deletion.
        values = (available_services[service][0], bid)
        c.execute('DELETE FROM access WHERE service IS ? AND client IS ?',
                  values)
        connection.commit()

        self.logger.info("Removed successfully.")

    def disable(self, app, service=None):
        '''Disables 'app' for the specified service, but leaves the entry in the
        TCC database.

        app     - an application identifier
        service - a service name to disable within
        '''

        if app is None:
            return
        else:
            bid = AppInfo(app).bid
        if service is None and self.service:
            service = self.service
        else:
            return

        # Be nice to the user.
        service = service.lower()

        # Check the service is recognized.
        if not service in available_services.keys():
            raise ValueError("Invalid service provided: " + service)

        self.logger.info(
            "Disabling '" + bid + "' in service '" + service + "'...")

        # Establish a connection with the TCC database.
        connection = self.connections[available_services[service][1]]

        # Validate that the connection was successful.
        if not connection:
            raise ValueError("Must be root to modify this service!")

        c = connection.cursor()

        # Disable the application for the given service.
        # The 'prompt_count' must be 1 or else the system will ask the user
        # anyway. This is the only time it seems to really matter.
        values = (available_services[service][0], bid)
        c.execute(
            'SELECT count(*) FROM access WHERE service IS ? and client IS ?',
            values
        )
        count = c.fetchone()[0]
        if count:
            if self.version == 12:
                c.execute(
                    'INSERT or REPLACE into access values(?, ?, 0, 0, 1)',
                    values
                )
            else:
                c.execute(
                    'INSERT or REPLACE into access values(?, ?, 0, 0, 1, NULL)',
                    values
                )
        connection.commit()

        self.logger.info("Disabled successfully.")

    def __create(self, path):
        '''Creates a database in the event that it does not already exist. These
        databases are formatted in a particular way. Don't change this!

        path - the path to the TCC database file to be created
        '''

        self.logger.info(
            "TCC.db file was expected at '" + path +
            "' but was not found. Creating new TCC.db file...")

        # Make sure our directory tree exists.
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path), int('700', 8))

        # Form an SQL connection with the file.
        connection = sqlite3.connect(path)
        c = connection.cursor()

        # Create the tables.
        c.execute('''
                CREATE TABLE admin
                (key TEXT PRIMARY KEY NOT NULL, value INTEGER NOT NULL)'''
        )

        c.execute('''
                INSERT INTO admin VALUES ('version', 7)'''
        )

        # In OS X 10.9, Apple changed the formatting for this table a bit.
        if self.version == 12:
            c.execute('''
                CREATE TABLE access
                (service TEXT NOT NULL,
                client TEXT NOT NULL,
                client_type INTEGER NOT NULL,
                allowed INTEGER NOT NULL,
                prompt_count INTEGER NOT NULL,
                CONSTRAINT key PRIMARY KEY (service, client, client_type))'''
            )

        else:
            c.execute('''
                CREATE TABLE access
                (service TEXT NOT NULL,
                client TEXT NOT NULL,
                client_type INTEGER NOT NULL,
                allowed INTEGER NOT NULL,
                prompt_count INTEGER NOT NULL,
                csreq BLOB,
                CONSTRAINT key PRIMARY KEY (service, client, client_type))'''
            )

        c.execute('''
                CREATE TABLE access_times
                (service TEXT NOT NULL,
                client TEXT NOT NULL,
                client_type INTEGER NOT NULL,
                last_used_time INTEGER NOT NULL,
                CONSTRAINT key PRIMARY KEY (service, client, client_type))'''
        )
        c.execute('''
                CREATE TABLE access_overrides
                (service TEXT PRIMARY KEY NOT NULL)'''
        )

        connection.commit()
        connection.close()

        self.logger.info("TCC.db file created successfully.")

    def __exit__(self, type, value, traceback):
        '''This handles the closing of connections when the object is closed.

        If the object is put inside a with statement (as suggested above), this
        will be called automatically when the 'with' is left.
        '''

        if self.root:
            self.root.close()
        if self.local:
            self.local.close()
