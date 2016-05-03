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

=========
 timekpr
=========

------------------------------
Keep control of computer usage
------------------------------

.. include:: header_data.inc
:Manual section: 8
:Manual group: User Manuals

SYNOPSIS
========

``timekpr``

DESCRIPTION
===========

**timekpr** tracks and controls the computer usage of user accounts. Using **timekpr-gui(8)**, the administrator can limit daily usage per user by configuring

- a daytime range (e.g. from 8am to 7pm) when the user is allowed to log on
- an elapsed time (e.g. 90 minutes) the user is allowed to log on per day

**timekpr** allows users to login or to stay logged in only as long as both limits are met. As long as a user hasn't any limits configured, **timekpr** does not do any monitoring or other
actions on that user.

To disallow logins outside the defined daytime range, timekpr relies on the settings in the configuration file for the time PAM-Module entered by **timekpr-gui**.

To disallow users to stay logged in over the defined daytime range, or to stay logged in over the defined elapsed time, **timekpr** checks the process tree at regular intervals. When a cer‐
tain user is logged in, the file `/var/lib/timekpr/<username>.time` is updated to contain the new elapsed time. This time is then checked against the total allowed (stored in
`/etc/timekpr/<username>`).


When **timekpr** discovers a user violating its limits, the user is warned and given a grace period to save his work. After this grace period, the user is kicked out by killing its pro‐
cesses. In addition, the file `/var/lib/timekpr/<username>.logout` is touched to state the fact that the user has been logged out forcibly by **timekpr**.

When the user tries to login again (within its daytime range, but all elapsed time used up), it is kicked out immediately and then locked by editing the config file for the access PAM-
Module. Now the user cannot login any more.


FILES
=====

`/etc/timekpr.conf`
      The system wide configuration file. See **timekpr.conf(5)** for further details.
`/etc/security/time.conf`, `/etc/security/access.conf`
      The system wide PAM Configuration files for the time and and access modules.


DIAGNOSTICS
===========

The logfile is quite verbose: `/var/log/timekpr.log`


BUGS
====

Please report bugs to the bugtracker at https://bugs.launchpad.net/timekpr/+bugs



.. include:: authors_seealso.inc

