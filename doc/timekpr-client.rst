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

================
 timekpr-client
================

-------------------------------------
Show timekpr constraints for the user
-------------------------------------

.. include:: header_data.inc
:Manual section: 8
:Manual group: User Manuals

SYNOPSIS
========

``timekpr-client``

DESCRIPTION
===========

timekpr-client is automatically started if you log on and displays a status icon in the system tray.

In the pop-up menu you can select if you want to skip the logon notification 
('`Your time is not limited today`' if your user is not restricted) 
and if you want to be notified via speech output 
(provided that a text to speech command e.g. `espeak` is installed and configured in the system wide configuration file).


FILES
=====

`~/.config/timekpr/timekpr-client.conf`
      The user specific timekpr-client configuration file.
`/etc/timekpr.conf`
      The system wide configuration file. See **timekpr.conf(5)** for further details.


.. include:: authors_seealso.inc

