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

xgettext --add-comments=TRANSLATORS -o timekpr.pot ../src/gui/about_dialog.ui
xgettext --add-comments=TRANSLATORS --join-existing -o timekpr.pot ../src/gui/client.ui
xgettext --add-comments=TRANSLATORS --join-existing -o timekpr.pot ../src/gui/main_window.ui 
xgettext --add-comments=TRANSLATORS --join-existing -o timekpr.pot ../src/timekpr-gui.py
xgettext --add-comments=TRANSLATORS --join-existing -o timekpr.pot ../src/timekpr-client.py

msgmerge -U $UPD_LANG/LC_MESSAGES/timekpr.po ./timekpr.pot
