Privacy Services Manager
========================

A single management utility to administer Location Services, Contacts requests, Accessibility, and iCloud access in Apple's Mac OS X.

## Contents

* [Purpose](#purpose) - what is this command for?
* [History](#history) - how it came to be
* [Usage](#usage) - details of invocation
  * [Options](#options)
  * [Actions](#actions)
  * [Applications](#applications)
* [Service Specifics](#service-specifics) - some odds and ends
* [Technical](#technical) - information on how it all works
  * [TCC Services](#tcc-services)
  * [Location Services](#location-services)

## Download

[Download the latest installer here!](../../releases/)

## Purpose

Simply put, this script will help you to manually adjust the values in the various security and privacy databases. This means you can give or restrict access to any of the supported services by hand, instead of having to run whatever application and wait for it to poll the system for permission. In particular this is useful in a distributed lab environment, such as the university where it was first deployed, as it allows the administrators to prematurely grant access to certain applications without the users needing to request permission. This is especially helpful because some services (Location Services, Accessibility) require privileged access to complete the request, which regular users do not have.

## History

Since Mac OS X 10.8 "Mountain Lion", Apple has introduced systems to handle access to certain features of the computer. Among these are Contacts (AddressBook), iCloud (Ubiquity), Accessibility, and Location Services. The first three are managed through one method (SQLite databases called `TCC.db` hidden throughout the system), while the latter is handled by the `locationd` daemon through property list files. Originally I created two separate scripts to accommodate the manual modification of these systems. However, eventually I realized that while the internal workings were different, the desired effect was more or less the same. This Privacy Services Manager is a compilation (and mild reformation) of those two scripts.

## Usage

The script is fairly straightforward, though there are some options:

```
$ privacy_services_manager.py [-hvn] [-l log] [-u user] [--template]
                              [--language] action service applications
```

### Options

| Option | Purpose |
|--------|---------|
| `-h`, `--help` | Prints help information. |
| `-v`, `--version` | Prints version information. |
| `-n`, `--no-log` | Redirects logging to stdio. |
| `--template` | Modify permissions for Apple's User Template. Only applies to certain services. |
| `-l log`, `--log-dest log` | Redirect logging to the specified file. (This can be overridden by `--no-log`.) |
| `-u user`, `--user user` | Modify permissions for `user`, not yourself. (Requires root privileges.) |
| `--language lang` | When changing permissions for the User Template, modify the `lang` template. |

### Actions

There are four actions available:

* `add` will create an entry for the specified application and enable the application for the service.
* `enable` effectively just calls `add`, ensuring that the application has been added and enabled.
* `remove` will *delete* the application's entry within the service. There will no longer be a record of that application therein.
* `disable` will leave the application's record intact, but will disallow the application from utilizing the given service.

### Applications

Applications are looked up using the [Management Tools](https://github.com/univ-of-utah-marriott-library-apple/management_tools) `app_lookup.py`. This means that there are a few ways to specify applications:
https://github.com/univ-of-utah-marriott-library-apple/management_tools

1. By path to the `.app` folder, e.g. `/Applications/Safari.app`, `/Longer/Path/To/MyApp.app`
2. By bundle identifier, e.g. `com.apple.Safari`, `com.me.myapp`
3. By shortname as it would be found by Spotlight, e.g. `safari`, `myapp`

Personally I would stick to either **1** or **2** for scripting purposes, since those are specific and verifiable. Use **3** informally in single-time invocations for sake of ease, though.

## Service Specifics

The `--user`, `--template`, and `--language` flags only affect those services which use the TCC system, i.e. Contacts, iCloud, and Accessibility. Providing these options for Location Services will have no effect.

If no application is given and Location Services is being modified, the Location Services system will be affected at-large. That is, if you were to run

```
$ privacy_services_manager.py enable location
```

Then the Location Services system would be enabled globally, without adding any applications to it.

## Technical

Here are some of the details of what goes on behind-the-scenes.

### TCC Services

Apple in fact has multiple TCC.db database files in any given installation of OS X 10.8 or newer (though none of them exist until the appropriate service is requested access to).  There is one for each user, in their `~/Library/Application Support/com.apple.TCC` folder, and there is one root database, located in `/Library/Application Support/com.apple.TCC`.  The local databases (those in each user's directory) are responsible for *Contacts* access and *iCloud* access.  The settings for these applications are granted on a per-user, per-application basis this way.  However, *Accessibility* permissions are stored (and must be stored) in the `/Library/...` database.  I assume this is due to the nature of those types of applications that request *Accessibility* access (they are granted some freedoms to the machine that could potentially be undesirable, so administrative access is required to add them).

This script will add *Accessibility* requests to the `/Library/...` database (assuming it is run with root permissions).  The other requests will be added to the TCC database file located at `~/Library/Application Support/com.apple.TCC/TCC.db`.  This is Apple's default directory for an individual user's settings.

#### Attribution

Much of the code used in the TCC section of the script was copy/pasted and then adapted from the `tccmanager.py` script written by Tim Sutton and published to his [GitHub repository](http://github.com/timsutton/scripts/tree/master/tccmanager).  We're very grateful to Tim for posting his code online freely; it has been very helpful to us.

### Location Services

Location Services stores all of its preferences in property list files (files with the `.plist` extension).  The global Location Services settings (i.e. whether or not Location Services is even enabled) are stored in `/private/var/db/locationd/Library/Preferences/ByHost/com.apple.locationd.$UUID.plist`, where "$UUID" refers to the Universally Unique Identifier of your computer.  The rest of the preferences, which consist of a list of what applications are allowed to access Location Services, are stored in `/private/var/db/locationd/clients.plist`.

If you've worked with plist files before in OS X 10.9 "Mavericks", then you know that they cannot be modified through direct text editing like previous versions of OS X.  Mavericks caches various plist preferences and writes asynchronously to disk.  This means that if you were to open `foo.plist` in your favorite plaintext editor (ne, nano, vi, etc.) and modify the key `bar`, there is no guarantee that it would keep the value you assigned it!  This is not ideal.  Instead, Apple insists that you use the `defaults` command to modify plist values directly.  `defaults` is supposed to write the changes, and then synchronize the caches with the new values to maintain whatever it is you wrote to them.

This section of the script is essentially an interface to the `defaults` command.  This is fast and reliable, and even better is that `defaults` is officially supported, which means it shouldn't be going away any time soon.
