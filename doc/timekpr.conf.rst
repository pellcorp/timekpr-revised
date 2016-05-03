.. Manual page for timekpr daemon written in rst.
.. Can be converted using rst2man, which in trusty is in the package "python-docutils"
.. 
.. rst Reference: http://docutils.sf.net/docs/user/rst/quickref.html
.. 
.. man-pages can have these parts:
.. NAME
.. SYNOPSIS
.. CONFIGURATION	 [Normally only in Section 4]
.. DESCRIPTION
.. OPTIONS.. [Normally only in Sections 1, 8]
.. EXIT STATUS		[Normally only in Sections 1, 8]
.. RETURN VALUE	 [Normally only in Sections 2, 3]
.. ERRORS.. [Typically only in Sections 2, 3]
.. ENVIRONMENT
.. FILES
.. VERSIONS		 [Normally only in Sections 2, 3]
.. CONFORMING TO
.. NOTES
.. BUGS
.. EXAMPLE
.. SEE ALSO

==============
 timekpr.conf
==============

------------------------------------
configuration file for **timekpr**.
------------------------------------

.. include:: header_data.inc
:Manual section: 5
:Manual group: File Formats Manual


DESCRIPTION
===========
The file `/etc/timekpr.conf` contains defaults for **timekpr(8)** and the associated programs. 
The file consists of multiple sections.
Each line holds a single value pair in the form `option` = `value`.
Double or single quotes are allowed around the value, as is whitespace around the equals sign. Comment lines must have a hash sign (#) in the first column.

The valid sections and configuration options are:

SECTION [general]
-----------------
VERSION
    The version of this config file.

SECTION [variables]
-------------------
GRACEPERIOD
    The grace period, where a notification pops up letting the users know that
    their time usage will be over soon. By default users are given 120 seconds to
    finish up their work (in seconds, e.g. 120 means 2 minutes).
    Default value "120".

POLLTIME
    How often should the timelogs be checked (in seconds).
    Default value "30".

DEBUGME
    `True` keeps a logfile, `False` does not.
    Default value "True".

LOCKLASTS
    Default lock period, can be `day(s)`, `hour(s)`, `minute(s)`, `month(s)`.
    Default value "30 minutes".


SECTION [directories]
---------------------
TIMEKPRDIR
    Default directory for per-user configuration and `.lock` files.
    Default value "/etc/timekpr".

TIMEKPRWORK
    Default working directory for `.time`, `.logout`, and `.late` files.
    Default value "/var/lib/timekpr".

TIMEKPRSHARED
    Default directory for shared files (e.g. images and gui definitions).
    Default value "/usr/share/timekpr".

LOGFILE
    Location of the logfile.
    Default value "/var/log/timekpr.log".


SECTION [speech]
----------------
COMMAND
    The command to execute for speech output.
    The following patterns will be substituted before executing the command:

    - `{language}` the current locale setting (e.g. 'de')
    - `{message}` the message text

    Default value "espeak -v{language} {message}".


FILES
=====

`/etc/timekpr.conf`


.. include:: authors_seealso.inc

