#!/usr/bin/env python
""" The graphical user interface for timekpr configuration.
    Copyright / License: See COPYRIGHT.txt
"""

import re
from os import remove, mkdir, geteuid, getenv
from os.path import isdir, isfile, realpath, dirname, join
from time import strftime, sleep
from pwd import getpwnam
from spwd import getspall

from gi.repository import Gtk
from gi.repository import GObject

import gettext
from gettext import gettext as _
from gettext import ngettext
import sys

#If DEVACTIVE is true, it uses files from local directory
DEVACTIVE = False

if DEVACTIVE:
    from sys import path
    path.append('.')

from common.timekprpam import *
from common.timekprcommon import *

#timekpr.conf variables (dictionary variable)
VAR = getvariables(DEVACTIVE)
VERSION = getversion()


#translation stuff
def init_locale():
    locale_domain = "timekpr" # must match locale domain set in *.ui files
    locale_path = '/usr/share/locale'

    # init python gettext
    gettext.bindtextdomain(locale_domain, locale_path)
    gettext.textdomain(locale_domain)


#Check if admin/root
def check_if_admin():
    if geteuid() != 0:
        dlg = Gtk.MessageDialog(None, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CLOSE, _("You need to have administrative privileges to run timekpr-gui"))
        dlg.set_default_response(Gtk.ResponseType.CLOSE)
        dlg.run()
        dlg.destroy()
        exit("Error: You need to have administrative privileges to run timekpr")


#Create configuration folder if not existing
def create_dirs():
    if not isdir(VAR['TIMEKPRDIR']):
        mkdir(VAR['TIMEKPRDIR'])
    if not isdir(VAR['TIMEKPRWORK']):
        mkdir(VAR['TIMEKPRWORK'])
    if not isdir(VAR['TIMEKPRSHARED']):
        exit('Error: Could not find the shared directory %s' % VAR['TIMEKPRSHARED'])


#Check if it is a regular user, with userid within UID_MIN and UID_MAX.
def is_regular_user(user_name):
    #FIXME: Hide active user - bug #286529
    if getenv('SUDO_USER') and user_name == getenv('SUDO_USER'):
        return False

    try:
        password_database_entry = getpwnam(user_name)
        user_id = int(password_database_entry[2])
        logindefs = open('/etc/login.defs')
        uid_limits = [int(x) for x in re.compile('^UID_(?:MIN|MAX)\s+(\d+)', re.M).findall(logindefs.read())]
    except (KeyError, ValueError):
        return False

    return min(uid_limits) <= user_id <= max(uid_limits)


def rm(filename):
    try:
        remove(filename)
    except OSError:
        pass


class timekprGUI(object):

    def __init__(self):
        ui_file = join(VAR['TIMEKPRSHARED'], 'main_window.ui')

        self.builder = Gtk.Builder()
        self.builder.add_from_file(ui_file)

        #connect signals to python methods
        self.builder.connect_signals(self)
        
        #connect gtk objects to python variables
        for obj in self.builder.get_objects():
            if issubclass(type(obj), Gtk.Buildable):
                name = Gtk.Buildable.get_name(obj)
                setattr(self, name, obj)

        self.mainwindow.set_title(_('Timekpr Control Panel'))

        #create lists of limit and boundary gtk objects
        self.limitSpins = [self.builder.get_object("limitSpin" + str(x)) for x in range(7)]
        self.fromSpins = [self.builder.get_object("fromSpin" + str(x)) for x in range(7)]
        self.toSpins = [self.builder.get_object("toSpin" + str(x)) for x in range(7)]
        self.boundariesLabels = [self.builder.get_object("boundariesLabel" + str(x)) for x in range(7)]
        self.limitLabels = [self.builder.get_object("limitLabel" + str(x)) for x in range(7)]

        self.statusbarCID = self.statusbar.get_context_id("timekprstatus")

        self.limits = []

        #Using /etc/shadow spwd module
        for userinfo in getspall():
            if is_regular_user(userinfo[0]):
                self.userSelectCombo.append_text(userinfo[0])
                self.userSelectCombo.set_active(0)

        #Ensure we have at least one available normal user
        if self.userSelectCombo.get_active_text() is None:
            dlg = Gtk.MessageDialog(None, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CLOSE, _("You need to have at least one normal user available to configure timekpr"))
            dlg.set_default_response(Gtk.ResponseType.CLOSE)
            dlg.run()
            dlg.destroy()
            exit("Error: You need to have at least one normal user available to configure timekpr")

        self.on_userSelectCombo_toggled(self)

        return

    def remove_status_message(self, msgid):
        self.statusbar.remove(self.statusbarCID, msgid)

    def set_status_message(self, message):
        msgid = self.statusbar.push(self.statusbarCID, strftime("%Y-%m-%d %H:%M:%S ") + message)
        GObject.timeout_add(6000, self.remove_status_message, msgid)

    def on_window_destroy(self, *args):
        Gtk.main_quit(*args)

    def on_aboutMenuItem_selected(self, widget):
        ui_file = join(VAR['TIMEKPRSHARED'], 'about_dialog.ui')

        builder = Gtk.Builder()
        builder.add_from_file(ui_file)

        dialog = builder.get_object('aboutdialog')
        dialog.set_version(VERSION)
        dialog.set_translator_credits(_("translator-credits"))
        dialog.set_comments(_('Keep control of computer usage'))
        dialog.show_all()
        dialog.run()
        dialog.destroy()

    def on_lockUnlockButton_clicked(self, widget):
        if self.lockUnlockLabel.get_label() == _('Lock account'):
            #lock account
            lockuser(self.user)
            statusmsg = _("Locked account %s") % (self.user)
            self.set_status_message(statusmsg)
            self.read_settings_nolimits()
        else:
            #unlock account
            unlockuser(self.user)
            #remove .lock file
            lockf = join(VAR['TIMEKPRDIR'], self.user + '.lock')
            rm(lockf)
            logoutf = join(VAR['TIMEKPRWORK'], self.user + '.logout')
            rm(logoutf)
            latef = join(VAR['TIMEKPRWORK'], self.user + '.late')
            rm(latef)
            statusmsg = _("Unlocked account %s") % self.user
            self.set_status_message(statusmsg)
            self.read_settings_nolimits()

    def on_clearAllRestrictionsButton_clicked(self, widget):
        #clears all limits and their files
        #FIXME: A yes/no confirmation would be handy here
        timef = join(VAR['TIMEKPRWORK'], self.user + '.time')
        logoutf = join(VAR['TIMEKPRWORK'], self.user + '.logout')
        latef = join(VAR['TIMEKPRWORK'], self.user + '.late')
        allowf = join(VAR['TIMEKPRWORK'], self.user + '.allow')
        #Should remove .allow file? It's not a restriction
        rm(timef)
        rm(logoutf)
        rm(latef)
        rm(allowf)
        #Remove boundaries
        removeuserlimits(self.user)
        #Remove limits
        configf = join(VAR['TIMEKPRDIR'], self.user)
        rm(configf)
        #Unlock user
        unlockuser(self.user)

        statusmsg = _("Removed all restrictions for account %s") % self.user
        self.set_status_message(statusmsg)
        self.on_userSelectCombo_toggled(self)

    def on_resetTimeButton_clicked(self, widget):
        #clear the .time file
        timefile = join(VAR['TIMEKPRWORK'], self.user + '.time')
        rm(timefile)
        statusmsg = _("Cleared used up time for account %s") % self.user
        self.set_status_message(statusmsg)
        self.read_settings_nolimits()

    def on_rewardButton_clicked(self, widget):
        arg = self.rewardSpin.get_value_as_int()
        timefile = join(VAR['TIMEKPRWORK'], self.user + '.time')
        if isfile(timefile):
            f = open(timefile)
            tlast = int(f.read())
            f.close()
        else:
            tlast = 0
        tnew = tlast - arg * 60
        f = open(timefile, 'w')
        f.write(str(tnew))
        f.close()
        statusmsg = _("Applied reward of %(num)s minute(s) to account %(user)s") % {'num': arg, 'user': self.user}
        self.set_status_message(statusmsg)
        self.read_settings_nolimits()

    def on_extendLimitsButton_clicked(self, widget):
        #UPDATE: extend limits button is now "Bypass for today"
        #It now is the same as changing boundaries from 0 to 24 for today's day of the week.
        #.allow can still be useful - active (logged in user accounts) won't be killed
        index = int(strftime("%w"))
        wfrom = self.fromtolimits[0]
        wto = self.fromtolimits[1]
        wfrom[index] = '0'
        wto[index] = '24'
        removeuserlimits(self.user)
        adduserlimits(self.user, wfrom, wto)
        allowfile = join(VAR['TIMEKPRWORK'], self.user + '.allow')
        f = open(allowfile, 'w').close()
        statusmsg = _("Set access hours to 00-24 on %(day)s for account %(user)s") % {'day': strftime("%A"), 'user': self.user}
        self.set_status_message(statusmsg)
        self.on_userSelectCombo_toggled(self)

    def on_refreshButton_clicked(self, widget):
        statusmsg = _("Refreshed setting values from account %s") % self.user
        self.set_status_message(statusmsg)
        self.on_userSelectCombo_toggled(self)

    def on_cancelButton_clicked(self, widget):
        Gtk.main_quit()

    def read_boundaries(self):
        #from-to time limitation (aka boundaries) - time.conf
        if isuserlimited(self.user):
            #Get user time limits (boundaries) as lists from-to
            bfrom = self.fromtolimits[0]
            bto = self.fromtolimits[1]

            for i in range(7):
                self.fromSpins[i].set_value(float(bfrom[i]))
                self.toSpins[i].set_value(float(bto[i]))
            # Use boundaries?
            ub = True
            # Single boundaries? (set per day)
            sb = False
            #Are all boundaries the same?
            #If they're not same, activate single (per day) boundaries
            if [bfrom[0]] * 7 != bfrom or [bto[0]] * 7 != bto:
                sb = True
            #Even if boundaries are Al0000-2400, return False
            if not sb and bfrom[0] == '0' and bto[0] == '24':
                ub = False
            self.boundariesCheck.set_active(ub)
            self.singleBoundariesCheck.set_active(sb)
        else:
            for i in range(7):
                self.fromSpins[i].set_value(7)
                self.toSpins[i].set_value(22)
            self.boundariesCheck.set_active(False)
            self.singleBoundariesCheck.set_active(False)

    def read_limits(self):
        #time length limitation
        configFile = join(VAR['TIMEKPRDIR'], self.user)
        del self.limits[:]
        if isfile(configFile):
            fileHandle = open(configFile)
            self.limits = fileHandle.readline()
            self.limits = self.limits.replace("limit=( ", "")
            self.limits = self.limits.replace(")", "")
            self.limits = self.limits.split(" ")

            for i in range(7):
                self.limitSpins[i].set_value(float(self.limits[i]) / 60)

            # Single limits? (set per day)
            sl = False
            # Use limits?
            ul = True

            for i in range(1, 7):
                if self.limits[i] != self.limits[i-1]:
                    sl = True

            if self.limits[0] == '86400' and not sl:
                ul = False
            self.limitCheck.set_active(ul)
            self.singleLimitsCheck.set_active(sl)
        else:
            for i in range(7):
                self.limitSpins[i].set_value(120)
            self.limitCheck.set_active(False)
            self.singleLimitsCheck.set_active(False)

    def update_status_icons(self, uislocked):
        #Set icons in status gtk-yes or gtk-no
        lockgreen = join(VAR['TIMEKPRSHARED'], 'padlock-green.png')
        lockred = join(VAR['TIMEKPRSHARED'], 'padlock-red.png')
        iconyes = Gtk.STOCK_YES
        iconno = Gtk.STOCK_NO
        iconsize = Gtk.IconSize.BUTTON
        #limitSpins status is already set, so we can use it
        #self.spinlimitvalue = self.builder.get_object("limitSpins" + strftime('%w')).get_value()
        if not isuserlimitedtoday(self.user) and not uislocked:
            self.allDayLoginImage.set_from_stock(iconyes, iconsize)
        else:
            self.allDayLoginImage.set_from_stock(iconno, iconsize)

        if self.limitCheck.get_active():
            self.limitsEnabledImage.set_from_file(lockred)
        else:
            self.limitsEnabledImage.set_from_file(lockgreen)

        if self.boundariesCheck.get_active():
            self.boundariesEnabledImage.set_from_file(lockred)
        else:
            self.boundariesEnabledImage.set_from_file(lockgreen)

        if uislocked:
            self.accountLockedImage.set_from_file(lockred)
        else:
            self.accountLockedImage.set_from_file(lockgreen)

        index = int(strftime("%w"))
        try:
            limit = int(self.limits[index])
        except IndexError:
            limit = 86400 # =60*60*24 (seconds in one day)

        timefile = join(VAR['TIMEKPRWORK'], self.user + '.time')
        used = 0
        if isfile(timefile) and fromtoday(timefile):
            t = open(timefile)
            used = int(t.readline())
            t.close()
        left = limit - used
        m, s = divmod(left, 60)
        self.timeLeftLabel.set_label(ngettext('%(min)s minute', '%(min)s minutes', abs(m)) % {'min': m})

    def set_button_states(self, user_is_locked):
        if user_is_locked:
            self.lockUnlockLabel.set_label(_('Unlock account'))
        else:
            self.lockUnlockLabel.set_label(_('Lock account'))

        if self.limitCheck.get_active():
            timefile = join(VAR['TIMEKPRWORK'], self.user + '.time')
            if isfile(timefile):
                self.resetTimeButton.set_sensitive(True)
            else:
                self.resetTimeButton.set_sensitive(False)
            #Reward button should add time even if .time is not there?
            self.rewardButton.set_sensitive(True)
            self.rewardSpin.set_sensitive(True)
            self.rewardLabel.set_sensitive(True)
        else:
            self.resetTimeButton.set_sensitive(False)
            self.rewardButton.set_sensitive(False)
            self.rewardSpin.set_sensitive(False)
            self.rewardLabel.set_sensitive(False)

        if self.boundariesCheck.get_active():
            index = int(strftime("%w"))
            wfrom = self.fromtolimits[0]
            wto = self.fromtolimits[1]
            if wfrom[index] != '0' or wto[index] != '24':
                self.extendLimitsButton.set_sensitive(True)
            else:
                self.extendLimitsButton.set_sensitive(False)
        else:
            self.extendLimitsButton.set_sensitive(False)

    def on_userSelectCombo_toggled(self, widget):
        self.user = self.userSelectCombo.get_active_text()
        user_is_locked = isuserlocked(self.user)
        self.fromtolimits = getuserlimits(self.user)
        self.read_boundaries()
        self.read_limits()
        self.userStatusLabel.set_label(_('Status for') + ' <span weight="bold">' + self.user + '</span>')
        self.update_status_icons(user_is_locked)
        self.set_button_states(user_is_locked)

    def read_settings_nolimits(self):
        user_is_locked = isuserlocked(self.user)
        self.update_status_icons(user_is_locked)
        self.set_button_states(user_is_locked)

    def on_boundariesCheck_toggled(self, widget):
        if self.boundariesCheck.get_active():
            self.fromSpins[0].set_sensitive(True)
            self.toSpins[0].set_sensitive(True)
            self.singleBoundariesCheck.set_sensitive(True)
            self.toLabel.set_sensitive(True)
            self.fromLabel.set_sensitive(True)
            self.boundariesLabels[0].set_sensitive(True)
        else:
            self.fromSpins[0].set_sensitive(False)
            self.toSpins[0].set_sensitive(False)
            self.singleBoundariesCheck.set_sensitive(False)
            self.toLabel.set_sensitive(False)
            self.fromLabel.set_sensitive(False)
            self.boundariesLabels[0].set_sensitive(False)
        self.on_singleBoundariesCheck_toggled(self)

    def on_singleBoundariesCheck_toggled(self, widget):
        if self.singleBoundariesCheck.get_active() and self.boundariesCheck.get_active():
            for i in range(1, 7):
                self.fromSpins[i].set_sensitive(True)
                self.toSpins[i].set_sensitive(True)
                self.boundariesLabels[i].set_sensitive(True)
            self.boundariesLabels[0].set_text(" " + _("Sun") + " ")
        else:
            for i in range(1, 7):
                self.fromSpins[i].set_sensitive(False)
                self.toSpins[i].set_sensitive(False)
                self.boundariesLabels[i].set_sensitive(False)
            self.boundariesLabels[0].set_text(_("Every day"))

    def on_limitCheck_toggled(self, widget):
        if self.limitCheck.get_active():
            self.limitSpins[0].set_sensitive(True)
            self.singleLimitsCheck.set_sensitive(True)
            self.minutesLabel.set_sensitive(True)
            self.limitLabels[0].set_sensitive(True)
        else:
            self.limitSpins[0].set_sensitive(False)
            self.singleLimitsCheck.set_sensitive(False)
            self.minutesLabel.set_sensitive(False)
            self.limitLabels[0].set_sensitive(False)
        self.on_singleLimitsCheck_toggled(self)

    def on_singleLimitsCheck_toggled(self, widget):
        if self.singleLimitsCheck.get_active() and self.limitCheck.get_active():
            for i in range(1, 7):
                self.limitLabels[i].set_sensitive(True)
                self.limitSpins[i].set_sensitive(True)
            self.limitLabels[0].set_text(" " + _("Sun") + " ")
        else:
            for i in range(1, 7):
                self.limitLabels[i].set_sensitive(False)
                self.limitSpins[i].set_sensitive(False)
            self.limitLabels[0].set_text(_("Every day"))

    def on_applyButton_clicked(self, widget):
        space = " "
        limit = "limit=( 86400 86400 86400 86400 86400 86400 86400 )"
        #timekprpam.py adduserlimits() uses lists with numbers as strings
        bFrom = ['0'] * 7
        bTo = ['24'] * 7

        if self.limitCheck.get_active():
            if self.singleLimitsCheck.get_active():
                limit = "limit=("
                for i in range(7):
                    limit = limit + space + str(self.limitSpins[i].get_value_as_int() * 60)
                limit = limit + space + ")"
            else:
                limit = "limit=("
                for i in range(7):
                    limit = limit + space + str(self.limitSpins[0].get_value_as_int() * 60)
                limit = limit + space + ")"
        if self.boundariesCheck.get_active():
            if self.singleBoundariesCheck.get_active():
                bFrom = []
                bTo = []
                for i in range(7):
                    bFrom.append(str(self.fromSpins[i].get_value_as_int()))
                    bTo.append(str(self.toSpins[i].get_value_as_int()))
            else:
                bFrom = []
                bTo = []
                for i in range(7):
                    bFrom.append(str(self.fromSpins[0].get_value_as_int()))
                    bTo.append(str(self.toSpins[0].get_value_as_int()))
        configFile = join(VAR['TIMEKPRDIR'], self.user)
        if self.limitCheck.get_active():
            fH = open(configFile, 'w')
            fH.write(limit + "\n")
            fH.close()
        else:
            rm(configFile)

        #No need to check if boundaries are active or not, apply the default or custom limits
        #Remove old user limits (boundaries)
        rb = removeuserlimits(self.user)
        #Add new limits (boundaries)
        ab = adduserlimits(self.user, bFrom, bTo)

        statusmsg = _("Applied limit changes for account %s") % self.user
        self.set_status_message(statusmsg)
        self.on_userSelectCombo_toggled(self)


if __name__ == "__main__":
    init_locale()
    check_if_admin()
    create_dirs()
    timekprGUI()
    Gtk.main()
