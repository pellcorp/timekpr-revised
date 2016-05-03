#!/bin/bash
UPD_LANG=$1
if [ "$UPD_LANG" = "" ];
then
	echo "Usage: update_pot.sh language"
	exit
fi

# if file does not exist, someone has to create it manually
if [ ! -f $UPD_LANG/LC_MESSAGES/timekpr.po ];
then
	echo "Please create a translation first!"
	exit
fi

xgettext -d timekpr ../src/gui/about_dialog.ui
xgettext --join-existing -d timekpr ../src/gui/client.ui
xgettext --join-existing -d timekpr ../src/gui/main_window.ui 
xgettext --join-existing -d timekpr ../src/timekpr-gui.py
xgettext --join-existing -d timekpr ../src/timekpr-client.py

msgmerge -U $UPD_LANG/LC_MESSAGES/timekpr.po ./timekpr.po
