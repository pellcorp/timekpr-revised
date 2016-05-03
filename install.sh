#!/bin/bash
PREFIX="${1:-/}"

_CONTINUE () {
	#Ask to continue
	echo "This will install the latest version of timekpr,"
	read -p "is this what you want to do? [Y]/n: " CHOICE
	if [ "$CHOICE" = "y" ] || [ "$CHOICE" = "Y" ] || [ "$CHOICE" = "" ] ; then
		_COPYSTUFF
	elif [ "$CHOICE" = "n" ]; then
		echo ""
		echo "You have chosen not to continue. Exiting..."
		exit 1
	else
		echo ""
		echo "Invalid selection! Try again."
		echo ""
		_CONTINUE
	fi
}

_COPYSTUFF() {
	cat debian/install | while read a b; do
		d="/$b"
		if [ ! -d $d ]; then
			echo "Making directory $d"
			mkdir -p $d
		fi
		f=`basename $a`
		echo "Copying $a to $PREFIX$b$f"
		cp $a $PREFIX$b$f
	done
	echo ""
	echo "timekpr has been updated!"
	echo "Please report any bugs at http://bugs.launchpad.net/timekpr"
	echo ""
}

echo ""
_CONTINUE
echo ""
