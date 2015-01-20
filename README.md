Privacy Services Manager
========================

A single management utility to administer Location Services, Contacts requests, Accessibility, and iCloud access in Apple's Mac OS X.

## Contents

* [Contact](#contact) - how to reach us
* [System Requirements](#system-requirements) - what you need
* [Install](#install) - instructions for installing Privacy Services Manager
* [Uninstall](#uninstall) - removal of Privacy Services Manager
* [Purpose](#purpose) - what is this command for?
* [Background](#background) - how this script came to be
* [Usage](#usage) - details of invocation
  * [Options](#options)
  * [Actions](#actions)
  * [Applications](#applications)
  * [Simple Usage Walkthrough](#simple-usage-walkthrough) - brief instructions to get you started
* [Service Specifics](#service-specifics) - some odds and ends
* [Technical](#technical) - information on how it all works
  * [TCC Services](#tcc-services)
  * [Location Services](#location-services)
* [Update History](#update-history) - version information to see what got put in when

## Contact

If you have any comments, questions, or other input, either [file an issue](../../issues) or [send an email to us](mailto:mlib-its-mac-github@lists.utah.edu). Thanks!

## System Requirements

* OS X 10.8 or newer
  * Note that the **Accessibility** and **Ubiquity (iCloud)** systems were not added until OS X 10.9. Attempts to modify these settings will not have any effect in OS X 10.8.
* Python 2.7.x (which you can download [here](https://www.python.org/download/))
* [Management Tools](https://github.com/univ-of-utah-marriott-library-apple/management_tools)

### OS X 10.10 "Yosemite" Notes

OS X Yosemite is now fully supported (from Developer Preview 7 onward). If you find any irregularites or anomalies, please [contact us](#contact). Thank you!

## Install

First, check that you meet all the requirements and have the prerequisites outlined in the [System Requirements](#system-requirements) section.

[Then download the latest installer for Privacy Services Manager here!](../../releases/)

Once the download has completed, double-click the `.dmg` file. This will open a window in Finder where you should see two packages (files ending in `.pkg`). Double click the one named "Privacy Services Management [x.x.x].pkg" (where *x.x.x* represents the current version number). This will launch the installer, which will guide you through the installation process. (Follow the on-screen instructions to complete the installation.)

## Uninstall

To remove Privacy Services Manager from your system, download the .dmg and run the "Uninstall Privacy Services Management [x.x.x]" package to uninstall it, where *x.x.x* represents the version number. The version is not relevant, as all of the Privacy Services Management uninstallers will work on any version of Privacy Services Manager.

At the end it will say "Installation Successful" but don't believe it - this will only remove files.

## Purpose

This script will help you to manually adjust the values in the various security and privacy databases in Apple's Mac OS X. This means you can give or restrict access to any of the supported services manually via the terminal, instead of having to run whatever application and wait for it to poll the system for permission. In particular this is useful in an administrated lab environment, such as the university where it was first deployed, as it allows the administrators to prematurely grant access to certain applications without the users needing to request permission. This is especially helpful because some services (Location Services, Accessibility) require privileged (root) access to complete the request, which regular users do not have.

## Background

Since Mac OS X 10.8 "Mountain Lion", Apple has introduced systems to handle access to certain features of the computer. Among these are Contacts (AddressBook), iCloud (Ubiquity), Accessibility, and Location Services. The first three are managed through one method (SQLite databases called `TCC.db` hidden throughout the system), while the latter is handled by the `locationd` daemon through property list files. Originally I created two separate scripts to accommodate the manual modification of these systems. However, eventually I realized that while the internal workings were different, the desired effect was more or less the same. This Privacy Services Manager is a compilation (and mild reformation) of those two scripts.

## Usage

The script is fairly straightforward, though there are some options:

```
$ privacy_services_manager.py [-hvn] [-l log] [-u user] [--template]
                              [--language] action service applications
```

For a brief tutorial, skip ahead to the [Simple Usage Walkthrough](#simple-usage-walkthrough).

### Options

| Option | Purpose |
|--------|---------|
| `-h`, `--help` | Prints help information and quits. |
| `-v`, `--version` | Prints version information and quits. |
| `-n`, `--no-log` | Redirects logging to standard output (stdout, i.e. the console). |
| `--template` | Modify privacy services for Apple's User Template. Only applies to certain services. |
| `--forceroot` | Force the script to allow the creation/modification of the root user's own TCC database file. |
| `-l log`, `--log-dest log` | Redirect logging to the specified file. (This can be overridden by `--no-log`.) |
| `-u user`, `--user user` | Modify privacy services for a specific user named "`user`". (Requires root privileges.) |
| `--language lang` | When changing privacy services for the Apple's User Template, modify the `lang` template. (Apple provides many User Template folder for different languages.) |

### Actions

There are four actions available:

* `add` will create an entry for the specified application and enable the application for the service.
* `enable` effectively just calls `add`, ensuring that the application has been added and enabled.
* `remove` will *delete* the application's entry within the service. There will no longer be a record of that application therein.
* `disable` will leave the application's record intact, but will disallow the application from utilizing the given service.

### Services

There are three* services that can be modified:

1. `contacts` handles requests to access a user's address book. Many web browsers use this to store login information for various websites. This service is handled on a per-user basis, so any user has the ability to modify this service for themselves.
2. `accessibility` deals with behind-the-scenes systems that Apple believes require extra privileges to enable. Applications that interface with your computer experience, such as BetterSnapTool or the Steam in-game overlay, require access through this service. These privileges must be granted by a privileged user via `sudo`.
3. `calendar` is the service responsible for allowing applications to inject events into your calendar. This can be used to schedule recurring events, among other things.
4. `reminders` gives an application the ability to access your Reminders (which are usually handled manually via the Reminders application).
5. `location` manages any application that desires to report on your physical location. Apple's own Maps application will request access to this, as well as web browsers once you visit a website that asks for your location (such as Google Maps). This system must also be handled by a privileges user via `sudo`.

\*There is actually a sixth service, called "Ubiquity" that can be administered with Privacy Services Manager, though it is referred to as `icloud` in the script (to ensure that you realize what it's accessing). It can be modified by non-privileged users for themselves, like `contacts`. Applications that request permissions with this service want to be able to access a user's iCloud storage and settings. Examples would be any text editing application that is able to save to your iCloud, such as TextEdit or iA Writer. Because of the nature of this request (access to a user's personal files and settings), I recommend against setting this service's permissions manually. This service is not as thoroughly tested.

### Applications

Applications are looked up using the [Management Tools](https://github.com/univ-of-utah-marriott-library-apple/management_tools) `app_lookup.py` script. This means that there are a few ways to specify applications for Privacy Services Manager:

1. By path to the `.app` folder, e.g. `/Applications/Safari.app`, `/Longer/Path/To/MyApp.app`
2. By bundle identifier, e.g. `com.apple.Safari`, `com.me.myapp`
3. By shortname as it would be found by Spotlight, e.g. `safari`, `myapp`

Personally I would stick to either **1** or **2** for scripting purposes, since those are specific and verifiable. Use **3** informally in single-time invocations for sake of ease, though.

To find an application's bundle identifier or bundle path, use the `app_lookup.py` script in the Management Tools suite. As an example, I will lookup the information on Safari:

```
$ app_lookup.py safari
```

This will return the following output (on a standard installation of OS X):

```
Safari
    BID:        com.apple.Safari
    Path:       /Applications/Safari.app
    Info.plist: /Applications/Safari.app/Contents/Info.plist
    Executable: /Applications/Safari.app/Contents/MacOS/Safari
```

As you can see, this will return the application's identifiable short name (Safari), bundle identifier (com.apple.Safari), and some paths to a few aspects of the application (its root path, the path to its `Info.plist` file, and the path to its binary executable).

If you want to know more about finding bundle identifiers yourself, look at the [relevant section of the Management Tools README](https://github.com/univ-of-utah-marriott-library-apple/management_tools/blob/master/README.md#finding-bundle-identifiers-manually).

### Simple Usage Walkthrough

This is a short walkthrough to get you started using Privacy Services Manager. See the [Full Usage](#full-usage) section below for more detailed information.

During this walkthrough, I will show you how to add an application to various services. The final step will undo all of the actions, leaving the system in effectively the same state as when we started.

***NOTE:*** You must have administrative access to install the necessary components and to be able to use these scripts to their fullest extents.

#### 1. Download and Install Management Tools

As specified above, you must download and install the Management Tools suite prior to using Privacy Services Manager. Go to the [Management Tools Releases](https://github.com/univ-of-utah-marriott-library-apple/management_tools/releases) page and download the most recent version. Double-click the download `.dmg` file, double-click the Installer, follow the on-screen instructions, and you should be good to go!

#### 2. Download and Install Privacy Services Manager

Go to the [Privacy Services Manager releases](../../releases/) page and download the most recent version. Follow the same installation instructions as for Management Tools in the previous step.

#### 3. Launch a Terminal window

The Privacy Services Manager is designed to be scriptable for use in administrated environments. I have not developed a graphical frontend for it, and there currently are not plans to add one. That being said, you're going to be using the Terminal to interact with it.

To open Terminal, look in the `/Applications/Utilities/` folder for a program called `Terminal.app` (or just `Terminal`). To get here, you can click Finder in the dock, then use the menubar at the top to click `Go` -> `Go to Folder...`. In the box that pops up, put `/Applications/Utilities`. A folder will appear; search it for `Terminal` and launch it by double-clicking.

Alternatively, if you are comfortable with Spotlight you can use that to launch Terminal.

#### 4. Add an application to your own `contacts` service permissions

I know through my own experience that, at some point or another, most web browsers will ask you for permission to look at your contacts. They can store things like your usernames and passwords here, among other things. Let's add Safari as a trusted application for your own account!

Within the Terminal, simply execute the following command (only put in everything after the `$`, and then press `return` or `enter`, depending on your keyboard):

```
$ /usr/local/bin/privacy_services_manager.py add contacts safari
```

The application can actually be specified in three different ways: either by short name ('`safari`'), bundle identifier ('`com.apple.Safari`'), or path to the `.app` folder ('`/Applications/Safari.app`'). For general one-time use I just use the short name, because it's generally specific enough, but if you intend to script this functionality then I would stick to one of the other two methods since they're more precise.

To make sure that this worked, open System Preferences (click the Apple icon in the top-left of the screen, then choose System Preferences). From the System Preferences window, click (in OS X 10.9) "Security & Privacy", then go to the "Privacy" tab at the top, then the "Contacts" section on the left. You should now see an entry for "Safari.app" with a check in the box. This indicates that the application was successfully added to the database.

#### 5. Add an application to the global `location` service permissions

Two of the services supported by Privacy Services Manager require administrative privileges to modify: *Accessibility* and *Location Services*. For this part of the walkthrough we will be adding Apple's Maps application to Location Services, but know that the process is the same for Accessibility.

First, because Location Services is handled a bit differently under-the-hood, we have to enable the system globally. To accomplish this, you must utilize your administrative privileges. In Unix-like systems, this is done by putting `sudo` in front of your commands. (This actually is an entirely separate command, but the nuances of `sudo` invocation are not the subject of this tutorial.)

```
$ sudo /usr/local/bin/privacy_services_manager.py enable location
```

This will turn on the Location Services system globally. To test that it is working properly, open up System Preferences, go to "Privacy & Security", and under the "Privacy" tab select "Location Services". At the top, you should see a check in the box next to "Enable Location Services."

Now we will add Maps to the database. To do this, simply do:

```
$ sudo /usr/local/bin/privacy_services_manager.py add location maps
```

Now in the "Location Services" submenu from before, you should be able to see "Maps.app".

#### 6. Add an application to another user's `contacts` service permissions

You've just installed some great program on the computer for your grandma, and you know it's going to ask for permission to leaf through her address book the first time she launches it. Because your grandma isn't terribly computer-savvy, she might think this is some sort of virus or scam or something! To prevent her from this headache, you decide to preemptively add permission for this application to her `contacts` service.

Let's say the application is called "MyApp". To give MyApp permission to access your grandma's contacts database, you need administrative privileges again. Then do:

```
$ sudo /usr/local/bin/privacy_services_manager.py --user grandma add contacts MyApp
```

This should add MyApp to your grandmother's contacts permissions, preventing any issues with her launching MyApp for the first time.

## Service Specifics

The `--user`, `--template`, and `--language` flags only affect those services which use the TCC system, i.e. Contacts, iCloud, and Accessibility. Providing these options for Location Services will have no effect.

If no application is given and Location Services is being modified, the Location Services system will be affected at-large. That is, if you were to run

```
$ sudo privacy_services_manager.py enable location
```

Then the Location Services system would be enabled globally, without adding any applications to it.

## Technical

Here are some of the details of what goes on behind-the-scenes.

### TCC Services

In any given installation of OS X 10.8 or newer, there can be multiple TCC.db database files (though none of these files exists until the appropriate service is requested access to).  There is one for each user, in their `~/Library/Application Support/com.apple.TCC/` folder, and there is one root database, located in `/Library/Application Support/com.apple.TCC/`.  The local databases (those in each user's directory) are responsible for *Contacts* access and *iCloud (Ubiquity)* access.  The settings for these applications are granted on a per-user, per-application basis this way.  However, *Accessibility* permissions are stored (and must be stored) in the `/Library/...` database.  I assume this is due to the nature of those types of applications that request *Accessibility* access (they are granted some freedoms to the machine that could potentially be undesirable, so administrative access is required to add them).

This script will add *Accessibility* requests to the `/Library/...` database (assuming it is run with root permissions).  The other requests will be added to the TCC database file located at `~/Library/Application Support/com.apple.TCC/TCC.db`.  This is Apple's default directory for an individual user's settings.

#### Attribution

Much of the code used in the TCC section of the script was copy/pasted and then adapted from the `tccmanager.py` script written by Tim Sutton and published to his [GitHub repository](http://github.com/timsutton/scripts/tree/master/tccmanager).  We're very grateful to Tim for posting his code online freely; it has been very helpful to us.

### Location Services

Location Services stores all of its preferences in property list files (files with the `.plist` extension).  The global Location Services settings (i.e. whether or not Location Services is even enabled) are stored in `/private/var/db/locationd/Library/Preferences/ByHost/com.apple.locationd.$UUID.plist`, where "$UUID" refers to the Universally Unique Identifier of your computer.  The rest of the preferences, which consist of a list of what applications are allowed to access Location Services, are stored in `/private/var/db/locationd/clients.plist`.

If you've worked with plist files before in OS X 10.9 "Mavericks", then you know that they cannot be modified through direct text editing like previous versions of OS X.  Mavericks caches various plist preferences and writes asynchronously to disk.  This means that if you were to open `foo.plist` in your favorite plaintext editor (ne, nano, vi, etc.) and modify the key `bar`, there is no guarantee that it would keep the value you assigned it!  This is not ideal.  Instead, Apple insists that you use the `defaults` command to modify plist values directly.  `defaults` is supposed to write the changes, and then synchronize the caches with the new values to maintain whatever it is you wrote to them.

This section of the script is essentially an interface to the `defaults` command.  This is fast and reliable, and even better is that `defaults` is officially supported, which means it shouldn't be going away any time soon.

## Update History

This is a reverse-chronological list of updates to this project.

| Date | Version | Update |
|------|:-------:|--------|
| 2014-09-19 | 1.5.0 | Updated to include the `calendar` and `reminders` services. Updated documentation to reflect these changes. |
| 2014-09-11 | 1.4.0 | Finished verbosity updates. Now very informational. Bugfixes to address Yosemite issue. |
| 2014-09-05 | 1.3.1 | First update for increased verbosity of console output and file logging. Easier to see what exactly is going on. |
| 2014-08-14 | 1.3.0 | Yosemite Update. Now (mostly) functional on OS X 10.10 "Yosemite". Some issues with global location services toggling. |
| 2014-07-16 | 1.2.4 | Bug fix: usage of name `bid` in code undefined. |
| 2014-06-26 | 1.2.3 | New packaging format: .pkg files distributed in .dmg. |
| 2014-06-25 | 1.2.3 | Bug fix: more robust ability to find location services plist files. Also updated documentation. |
| 2014-06-24 | 1.1 | The script now comes in an easy-to-use package installer. Help documentation updated. |
| 2014-06-20 | 1.0 | Ability to 'disable' applications added. Usage information (`--help`) and documentation updated. |
| 2014-06-19 | 0.7 | After rewriting the TCC database and Location Services modules, editor classes were created for simpler integration. |
| Pre-2014-06-18 | 0.1 | Decision made to combine *TCC Database Manager* and *Location Services Manager* projects. |
