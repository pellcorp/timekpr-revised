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

=============
 timekpr-gui
=============

--------------------------------------
Graphical user interface for timekpr.
--------------------------------------

.. include:: header_data.inc
:Manual section: 8
:Manual group: User Manuals

SYNOPSIS
========

``timekpr-gui``

DESCRIPTION
===========

With this graphical user interface you can set the allowed `daytime range` and the allowed log on `time contingent` for `other` users.


FILES
=====

`/etc/timekpr.conf`
      The system wide configuration file. See **timekpr.conf(5)** for further details.
`/etc/security/time.conf`, `/etc/security/access.conf`
      The system wide PAM Configuration files for the time and and access modules.


.. include:: authors_seealso.inc

