from distutils.core import setup
from privacy_services_management import __version__

setup(
    name='Privacy Services Management',
    version=__version__,
    url='https://github.com/univ-of-utah-marriott-library-apple/privacy_services_manager',
    author='Pierce Darragh, Marriott Library IT Services',
    author_email='mlib-its-mac-github@lists.utah.edu',
    description=("A single management utility to administer Location Services, Contacts requests, Accessibility, and iCloud access in Apple's Mac OS X."),
    license='MIT',
    packages=['privacy_services_management'],
    package_dir={'privacy_services_management': 'privacy_services_management'},
    scripts=['privacy_services_manager.py'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: MacOS X',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: System :: Systems Administration'
    ],
)
