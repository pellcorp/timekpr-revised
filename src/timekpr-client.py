#!/usr/bin/python
# -*- coding: utf-8 -*-

# generic import
import gi

# configparser
try:
    # python3
    import configparser
except ImportError:
    # python2.x
    import ConfigParser as configparser

# indicator stuff
try:
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import AppIndicator3 as AppIndicator
    USE_INDICATOR = True
except (ImportError, ValueError):
    USE_INDICATOR = False
    pass

# init speech
try:
    from espeak import espeak as espeak
    USE_SPEECH = True
except (ImportError, ValueError):
    USE_SPEECH = False
    pass

# trying to get on the bus
try:
    import dbus
    USE_DBUS = True
except  (ImportError, ValueError):
    USE_DBUS = False
    pass

import datetime
import os
import sys
import time

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import GLib

import locale
import gettext
from gettext import gettext as _
from gettext import ngettext

import subprocess

# debug
DEBUG = False
# if DEVACTIVE is true, it uses files from local directory
DEVACTIVE = False

# check for debug option
try:
    for arg in sys.argv:
        if arg == "debug":
            DEBUG = True
        elif arg == "devactive":
            DEVACTIVE = True
except Exception:
    pass

# local files
if DEVACTIVE:
    from sys import path
    path.append('.')
    print("%s: development config" % ("main"))

from common.timekprpam import *
from common.timekprcommon import *

# timekpr.conf variables (dictionary variable)
VAR = getvariables(DEVACTIVE)
VERSION = getversion()

UI_POPUPMENU = """
<ui>
    <popup name='PopupMenu'>
        <menuitem action='TimeLeft' />
        <separator />
        <menuitem action='Properties' />
        <separator />
        <menuitem action='Timekpr-GUI' />
        <separator />
        <menuitem action='About' />
    </popup>
</ui>
"""

def debug(text, force=False):
    prefix="LOG"
    if DEBUG:
        prefix="DBG%s" % (prefix)
    if DEBUG or force:
        print('%s: %s' % (prefix, text))

#translation stuff
def init_locale():
    locale_domain = "timekpr" # must match locale domain set in *.ui files
    locale_path = '/usr/share/locale'

    # init python gettext
    gettext.bindtextdomain(locale_domain, locale_path)
    gettext.textdomain(locale_domain)

def get_language():
    lang = ""

    try:
        lang = locale.getlocale()[0].split('_')[0]
    except Exception:
        pass

    return lang

def config_filename(DEVACTIVE):
    cfg_filename = ""
    if DEVACTIVE:
        cfg_filename = "../support"

    cfg_path = os.getenv("XDG_CONFIG_HOME", default=os.path.join(os.path.expanduser("~"), ".config", "timekpr"))
    cfg_filename = cfg_filename + os.path.join(cfg_path, 'timekpr-client.conf')
    return cfg_filename

def load_config(DEVACTIVE):
    fconf = config_filename(DEVACTIVE)

    conf = configparser.ConfigParser()
    try:
        conf.read(fconf)
    except configparser.ParsingError:
        debug('Error: Could not parse the configuration file properly %s' % fconf, True)

    #Creating a dictionary file
    var = dict()

    try:
        var['SHOW_FIRST_NOTIFICATION'] = conf.getboolean('notifier', 'show_first_notification')
    except (configparser.NoSectionError, configparser.NoOptionError):
        var['SHOW_FIRST_NOTIFICATION'] = True

    try:
        var['USE_SPEECH_NOTIFICATION'] = conf.getboolean('notifier', 'use_speech_notification')
    except (configparser.NoSectionError, configparser.NoOptionError):
        var['USE_SPEECH_NOTIFICATION'] = True

    return var

def save_config(DEVACTIVE):
    fconf = config_filename(DEVACTIVE)

    dir = os.path.dirname(fconf)
    if not os.path.exists(dir):
        os.makedirs(dir)

    conf = configparser.ConfigParser()
    conf.add_section('notifier')
    conf.set('notifier', 'show_first_notification', VAR['SHOW_FIRST_NOTIFICATION'])
    conf.set('notifier', 'use_speech_notification', VAR['USE_SPEECH_NOTIFICATION'])

    with open(fconf, 'wb') as configfile:
        conf.write(configfile)

def which(program, use_secure_path=False, options=None):
    """Searches the environment PATH (or an hard-coded 'secure' path) for an executable with the given name."""
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, name = os.path.split(program)
    if fpath:
        if is_exe(program):
            if options:
                program += " " + options
            return program
    else:
        if use_secure_path:
            path = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
        else:
            path = os.environ["PATH"]

        for part in path.split(os.pathsep):
            part = part.strip('"')
            exe_file = os.path.join(part, program)
            if is_exe(exe_file):
                if options:
                    exe_file += " " + exe_file
                return exe_file

    return None

def init_espeak():
    if USE_SPEECH:
        # set up speech synth
        espeak.set_voice(get_language());
        espeak.set_parameter(espeak.Parameter.Pitch, 1)
        espeak.set_parameter(espeak.Parameter.Rate, 145)
        espeak.set_parameter(espeak.Parameter.Range, 600)

class IndicatorTimekpr(object):
    def __init__(self):
        # get which DE we are running
        self.isAppIndicator = (True if (self.getSessionName().find("Unity") > -1 or (self.getSessionName() == "KDE" and self.getSessionVersion(self.getSessionName()) == 5)) and USE_INDICATOR else False)

        # this is for Unity stuff
        if self.isAppIndicator:
            # init indicator itself (icon will be set later)
            self.ind = AppIndicator.Indicator.new("indicator-timekpr", "", AppIndicator.IndicatorCategory.APPLICATION_STATUS)
            self.ind.set_status(AppIndicator.IndicatorStatus.ACTIVE)

            # define empty menu
            self.menu = Gtk.Menu()
            self.item_left = Gtk.MenuItem(_("Time left..."))
            self.menu.append(self.item_left)
            self.menu.append(Gtk.SeparatorMenuItem())
            self.item_properties = Gtk.MenuItem(_('Properties'))
            self.menu.append(self.item_properties)
            self.menu.append(Gtk.SeparatorMenuItem())
            self.item_cp = Gtk.MenuItem(_('Timekpr Control Panel'))
            self.menu.append(self.item_cp)
            self.menu.append(Gtk.SeparatorMenuItem())
            self.item_about = Gtk.MenuItem(_('About'))
            self.menu.append(self.item_about)
            self.menu.show_all()
            self.item_left.connect("activate", self.on_click)
            self.item_properties.connect("activate", self.on_properties)
            self.item_cp.connect("activate", self.on_timekpr_gui)
            self.item_about.connect("activate", self.on_about)

            self.ind.set_menu(self.menu)
        # this is for Non-Unity stuff
        else:
            # set up tray
            self.tray = Gtk.StatusIcon()
            self.tray.set_visible(True)

            self.tray.connect('activate', self.on_click)
            self.tray.connect('popup-menu', self.onPopupMenu)

            action_group = Gtk.ActionGroup("timekpr-client_actions")
            action_group.add_actions([
                ("TimeLeft", Gtk.STOCK_INFO, _("Time left..."), None, None, self.on_click),
                ("Properties", Gtk.STOCK_PROPERTIES, None, None, None, self.on_properties),
                ("Timekpr-GUI", Gtk.STOCK_PREFERENCES, _('Timekpr Control Panel'), None, None, self.on_timekpr_gui),
                ("About", Gtk.STOCK_ABOUT, None, None, None, self.on_about)
                                    ])

            uimanager = Gtk.UIManager()
            uimanager.add_ui_from_string(UI_POPUPMENU)
            uimanager.insert_action_group(action_group)
            self.popup = uimanager.get_widget("/PopupMenu")

        # initialize timekpr related stuff
        self.initTimekpr()

    def on_click(self, evt):
        self.click = True
        self.regularNotifier()

    def on_properties(self, evt):
        ui_file = os.path.join(VAR['TIMEKPRSHARED'], 'client.ui')

        self.builder = Gtk.Builder()
        self.builder.add_from_file(ui_file)

        #connect signals to python methods
        self.builder.connect_signals(self)

        #connect gtk objects to python variables
        for obj in self.builder.get_objects():
            if issubclass(type(obj), Gtk.Buildable):
                name = Gtk.Buildable.get_name(obj)
                setattr(self, name, obj)

        self.clientwindow.set_title(_('Timekpr Client Control Panel'))
        self.userLabel.set_text(self.username)

        self.showFirstNotificationCheck.set_active(VAR['SHOW_FIRST_NOTIFICATION'])
        self.useSpeechNotificationCheck.set_active(VAR['USE_SPEECH_NOTIFICATION'])

        # do not allow user to mess around when speech is not available
        self.useSpeechNotificationCheck.set_sensitive(USE_SPEECH)

    def on_aboutMenuItem_selected(self, evt):
        self.on_about(evt)

    def on_applyButton_clicked(self, evt):
        VAR['SHOW_FIRST_NOTIFICATION'] = self.showFirstNotificationCheck.get_active()
        VAR['USE_SPEECH_NOTIFICATION'] = self.useSpeechNotificationCheck.get_active()
        save_config(DEVACTIVE)

    def on_cancelButton_clicked(self, evt):
        self.clientwindow.destroy()

    def on_window_destroy(self, evt):
        pass

    def on_timekpr_gui(self, evt):
        import subprocess
        rc = subprocess.call(['pkexec', 'timekpr-gui'])

    def onPopupMenu(self, status, button, time):
        self.popup.popup(None, None, None, None, 0, time)

    def on_about(self, evt):
        ui_file = os.path.join(VAR['TIMEKPRSHARED'], 'about_dialog.ui')

        builder = Gtk.Builder()
        builder.add_from_file(ui_file)

        dialog = builder.get_object('aboutdialog')
        dialog.set_version(VERSION)
        dialog.set_translator_credits(_("translator-credits"))
        dialog.set_comments(_('Keep control of computer usage'))
        dialog.show_all()
        dialog.run()
        dialog.destroy()

    def initTimekpr(self):
        # get variables and set interval
        self.VAR = getvariables(DEVACTIVE)
        self.checkInterval = 30
        self.timerLevelInEffect = 1

        # get username
        self.username = os.getenv('USER')

        # replace stuff for DEV
        if DEVACTIVE:
            self.VAR['TIMEKPRSHARED'] = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'icons/'))
            self.VAR['TIMEKPRWORK'] = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'sample/'))
            self.VAR['TIMEKPRDIR'] = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'sample/'))

        # get both locked and unlocked icons
        self.limited_green = os.path.join(self.VAR['TIMEKPRSHARED'], 'padlock-limited-green.png')
        self.limited_yellow = os.path.join(self.VAR['TIMEKPRSHARED'], 'padlock-limited-yellow.png')
        self.limited_red = os.path.join(self.VAR['TIMEKPRSHARED'], 'padlock-limited-red.png')
        self.unlimited_green = os.path.join(self.VAR['TIMEKPRSHARED'], 'padlock-unlimited-green.png')

        # get language
        self.lang = get_language()

        # set up control files
        self.timefile = os.path.join(self.VAR['TIMEKPRWORK'], self.username + '.time')
        self.allowfile = os.path.join(self.VAR['TIMEKPRWORK'], self.username + '.allow')
        self.conffile = os.path.join(self.VAR['TIMEKPRDIR'], self.username)

        # create stuff for DEV
        if DEVACTIVE:
            debug("creating sample dir")
            dir = os.path.dirname(self.VAR['TIMEKPRWORK']+"/")
            if not os.path.exists(dir):
                debug("creating sample files")
                os.makedirs(dir)
                f=open(self.timefile, "a")
                f.write("84540")
                f.close()
                f=open(self.allowfile, "a")
                f.close()
                f=open(self.conffile + ".late", "a")
                f.close()

        # nobody wanted info by clicking on the icon and other default stuff
        self.click = False
        self.firstNotif = True
        self.notifTimer = None
        self.notifyInterface = None
        self.timeSpentPrev, verified = self.getTime(self.timefile)
        self.notificationLimits = (
            [0*60,1*60,'critical',self.limited_red,0] # very critial, once a minute, urgency is critical (on top of everyting), icon is red
            ,[3*60,1*60,'critical',self.limited_red,1] # less than 3 mins - notification goes off every minute, urgency is critical (on top of everyting), icon is red
            ,[10*60,5*60,'critical',self.limited_yellow,2] # normal, but yellow as warning, not much time left at all, urgency is critical (on top of everyting), icon is still yellow
            ,[30*60,10*60,'normal',self.limited_yellow,3] # normal, but yellow as warning, not much time left
            ,[2*60*60,30*60,'low',self.limited_green,4] # plenty of time
            ,[9999999,60*60,'low',self.limited_green,5] # even more plenty of time
        )

        # this is needed only if DBUS is used
        if USE_DBUS:
            # create a dict for urgencies
            self.dbusUrgencies = {"low":dbus.Byte(0, variant_level=1), "normal":dbus.Byte(1, variant_level=1), "critical":dbus.Byte(2, variant_level=1)}
            # init DBUS early
            self.initNotificatioDelivery(True)
            # first time it may fail, we need to init it the lazy way later

        # initial check of the limits
        self.reReadConfigAndcheckLimits()

        # set up first notification as per config
        self.firstNotif = VAR['SHOW_FIRST_NOTIFICATION']

        # add a GLib loop to check limits:
        GLib.timeout_add_seconds(self.checkInterval, self.reReadConfigAndcheckLimits)

        # add a notifier for the first time to x seconds (only if not already initialized)
        self.notifTimer = GLib.timeout_add_seconds(self.timerLevelInEffect+9, self.initNotificatioDelivery)

    def reReadConfigAndcheckLimits(self):
        name = "reReadConfigAndcheckLimits"
        # defaults
        urgency = 'low'

        # re-read settings in case they changed
        self.limits, self.bfrom, self.bto = readusersettings(self.username, self.conffile)

        # get the day
        index = int(strftime("%w"))

        # if the user is not a restricted user for this day, set the tray icon to green padlock
        if not isrestricteduser(self.username, self.limits[index]):
            # user is not limited
            if self.isAppIndicator:
                self.ind.set_icon(self.unlimited_green)
                self.ind.set_label("∞", "")
                self.ind.set_title("∞")
            else:
                self.tray.set_from_file(self.unlimited_green)
                self.tray.set_tooltip_text("∞")

            # come back later
            return True
        elif self.firstNotif:
            # user is limited
            if self.isAppIndicator:
                self.ind.set_icon(self.limited_red)
            else:
                self.tray.set_from_file(self.limited_red)

        # get the time already spent
        time, verified = self.getTime(self.timefile)

        # check if we have file, if not - exit
        if verified != True:
            self.notifyUser(_('Can not read configuration, time left is unknown at the moment... Please wait a little for configuration to be initialized'), 'critical')
            return True

        debug("%s: previous time: %d, new time: %d, check interval: %d" % (name, time, self.timeSpentPrev, 3*self.checkInterval-1))

        # check if time changed too rapildly, we have to resched the notifier
        if abs(time - self.timeSpentPrev) > (3*self.checkInterval-1):
            # end the current callback
            GLib.source_remove(self.notifTimer)

            # add call very shortly
            self.timerLevelInEffect = 1
            self.notifTimer = GLib.timeout_add_seconds(self.timerLevelInEffect, self.regularNotifier)
            debug("%s: time changed rapidly, emit notification" % (name))

        # store previous reading
        self.timeSpentPrev = time

        # get the time left
        left = self.getTimeLeft()
        debug("%s: time left %d" % (name, left))

        # normalize time for display
        if left <= 0:
            left = 0
            urgency = 'critical'
        # in case more time added while very low on minutes
        elif self.timerLevelInEffect <= 0 and left > 0:
            self.regularNotifier()

        # split hours, minutes, seconds
        h, m, s = self.fractSec(left)

        # indicators only
        if self.isAppIndicator:
            self.ind.set_label("(%s:%s)" % (str(h).rjust(2, "0"), str(m).rjust(2, "0")), "")
            self.ind.set_title("(%s:%s)" % (str(h).rjust(2, "0"), str(m).rjust(2, "0")))
        else:
            self.tray.set_tooltip_text("(%s:%s)" % (str(h).rjust(2, "0"), str(m).rjust(2, "0")))

        # now if it arrives too early
        if isearly(self.bfrom, self.allowfile):
            self.notifyUser(_('You are early, you will be logged out in LESS than 2 minutes'), urgency)

        # now if it arrives too late
        if islate(self.bto, self.allowfile):
            self.notifyUser(_('You are late, you will be logged out in LESS than 2 minutes'), urgency)

        # now if allowed time is almost spent
        if ispasttime(self.limits, time):
            self.notifyUser(_('Your time is up, you will be logged out in LESS than 2 minutes'), urgency)

        # done
        return True

    # initialize anything related to notifications and send first notification (called from glib timer)
    def initNotificatioDelivery(self, firstInit=False):
        # changeable global variables
        global USE_DBUS

        # trying to get on the bus
        if USE_DBUS and self.notifyInterface is None:
            try:
                # dbus connection
                self.sessionDbus = dbus.SessionBus()
                self.notifyObject = self.sessionDbus.get_object('org.freedesktop.Notifications', '/org/freedesktop/Notifications')
                self.notifyInterface = dbus.Interface(self.notifyObject, 'org.freedesktop.Notifications')
            except:
                if firstInit != True:
                    USE_DBUS = False
                else:
                    debug("%s: DBUS init failed for the first time, trying second time..." % ("initNotificatioDelivery"))
                pass

        # add call very shortly
        if firstInit != True:
            self.timerLevelInEffect = 1
            self.notifTimer = GLib.timeout_add_seconds(self.timerLevelInEffect, self.regularNotifier)

        # limit this to one call (called from timer, has to return False not to repeat the message)
        return False

    # periodic notifier, gives notifications to the user
    def regularNotifier(self):
        # default values
        name = "regularNotifier"
        result = True
        timerLevelInEffectTmp = self.timerLevelInEffect
        urgency = 'low'

        # get the day
        index = int(strftime("%w"))

        # if the user is not a restricted user for this day
        if not isrestricteduser(self.username, self.limits[index]):
            if self.firstNotif or self.click:
                self.notifyUser(_('Your time is not limited today'), 'low')
                self.click = False

                # restricted user - no more notifs
                self.timerLevelInEffect = 0
            result = False
        # if there is time to check
        else:
            time, verified = self.getTime(self.timefile)
            if verified != True:
                result = False
                debug("%s: file (%s) can NOT be read, we have a problem..." % (name, self.timefile))
                return result

        # first notification is no more
        self.firstNotif = False

        # we don't need to process any further
        if result != False:
            # get how much time is left
            left = self.getTimeLeft()

            debug("%s: time left: %d" % (name, left))

            # if the time is up, notifications is taken care of by reReadConfigAndcheckLimits
            if left < 0:
                # handled in read config
                self.timerLevelInEffect = 0
                result = False

            # we don't need to process any further
            if result != False:
                # split hours, minutes, seconds
                h, m, s = self.fractSec(left)

                # build up message in human language :)
                message = self.calculateTimeLeftString(h, m, s)

                # check limits and do actions based on results
                for rLimit in self.notificationLimits:
                    debug("%s: checking limit: %d" % (name, rLimit[0]))

                    # check time left according to defined limits
                    if left < rLimit[0] + self.checkInterval + 5:
                        debug("%s: found the right limit: %d" % (name, rLimit[0]))

                        # set urgency
                        urgency = rLimit[2]

                        # if not clicked
                        if not self.click:
                            # new timer
                            self.timerLevelInEffect = rLimit[1]
                            debug("%s: check if limit has changed, old: %d, new: %d" % (name, timerLevelInEffectTmp, self.timerLevelInEffect))

                            # if limit has changed
                            if timerLevelInEffectTmp != self.timerLevelInEffect:
                                # depending on DE
                                if self.isAppIndicator:
                                    self.ind.set_icon(rLimit[3])
                                else:
                                    self.tray.set_from_file(rLimit[3])

                                # change tmp for adjustments
                                timerLevelInEffectTmp = self.timerLevelInEffect

                                debug("%s: limit compensation, left: %d, prev: %d, check: %d" % (name, left, self.notificationLimits[rLimit[4]-1][0], self.timerLevelInEffect))

                                # calculate new interval: say if we have 26 mins notification will be scheduled at 16 mins, but the rule
                                # is that if we have less than 25 mins, notification goes off every 5 mins, so that has to be at 25, 20, ... mins
                                # to compensate that we need to schedule time to go off at 25 not 16
                                if left - self.notificationLimits[rLimit[4]-1][0] < self.timerLevelInEffect:
                                    timerLevelInEffectTmp = left - self.notificationLimits[rLimit[4]-1][0]
                                    debug("%s: adjusted limit: %d" % (name, timerLevelInEffectTmp))

                                # set up new interval
                                self.notifTimer = GLib.timeout_add_seconds(timerLevelInEffectTmp, self.regularNotifier)

                                # end existing interval
                                result = False

                        # that's it
                        break

                # notify (taking into account calculated urgency as well)
                self.notifyUser(message, urgency)

        # noone clicked us
        self.click = False

        # result
        return result

    # returns a formated string with the time left for a user
    def calculateTimeLeftString(self, h, m, s):
        # variables
        strLevel = 0

        ## printing correctly
        # header
        # TRANSLATORS: this is a part of message "You have %(hour)s hour(s), %(min)s minute(s) and %(sec)s second(s) left" please translate accordingly
        message = _('You have')

        # for hours
        if h > 0:
            # TRANSLATORS: this is a part of message "You have %(hour)s hour(s), %(min)s minute(s) and %(sec)s second(s) left" please translate accordingly
            messageTmp = ' ' + ngettext('%(hour)s hour', '%(hour)s hours', h) % {'hour': h}
            strLevel=strLevel+1
        else:
            messageTmp = ''

        # compose
        message = message + messageTmp

        # for minutes
        if m > 0:
            if strLevel > 0:
                messageTmp = ','
            else:
                messageTmp = ''

            # TRANSLATORS: this is a part of message "You have %(hour)s hour(s), %(min)s minute(s) and %(sec)s second(s) left" please translate accordingly
            messageTmp = messageTmp + ' ' + ngettext('%(min)s minute', '%(min)s minutes', m) % {'min': m}
            strLevel = strLevel + 1
        else:
            messageTmp = ''

        # compose
        message = message + messageTmp

        # for seconds
        if s > 0 or (m == 0 and h == 0):
            if strLevel > 0:
                messageTmp = ','
            else:
                messageTmp = ''

            # TRANSLATORS: this is a part of message "You have %(hour)s hour(s), %(min)s minute(s) and %(sec)s second(s) left" please translate accordingly
            messageTmp = messageTmp + ' ' + ngettext('%(sec)s second', '%(sec)s seconds', s) % {'sec': s}
            strLevel = strLevel + 1
        else:
            messageTmp = ''

        # compose
        # TRANSLATORS: this is a part of message "You have %(hour)s hour(s), %(min)s minute(s) and %(sec)s second(s) left" please translate accordingly
        message = message + messageTmp + ' ' + _('left')

        # final message
        return message

    def notifyUser(self, message, urgency):
        name = "notifyUser"
        # defaults
        icon = 'gtk-dialog-info'
        durationSecs = 3
        durationMsecs = durationSecs * 1000
        title = _('Timekpr notification')

        # based on urgency, choose different icon
        if urgency == 'normal':
            icon = 'gtk-dialog-warning'
        elif urgency == 'critical':
            icon = 'gtk-dialog-error'

        # if speech is enabled, don't bother user with urgent notifications when it's not urgent (these go off even in fullscreen games)
        if not VAR['USE_SPEECH_NOTIFICATION']:
            urgency = 'critical'

        # if dbus available
        if USE_DBUS:
            # onl if dbus is initiated
            if self.notifyInterface is not None:
                # notify
                self.notifyInterface.Notify('Timekpr', 0, icon, title, message, '', {"urgency":self.dbusUrgencies[urgency]}, durationMsecs)
                debug("%s: notification via dbus" % (name))
            else:
                debug("%s: notification via dbus, BUT DBUS is NOT initalized" % (name), True)
        # KDE uses different tech to notify users
        elif self.getSessionName() == 'KDE' and self.getSessionVersion(self.getSessionName()) == 3:
            # KDE3 and friends use dcop
            getcmdoutput('dcop knotify default notify notifying timekpr-client "' + message + '" "" "" 16 0')
            debug("%s: notification via dcop" % (name))
        # failover
        else:
            # for the rest try standard notification
            getcmdoutput('notify-send --icon=' + icon + ' --urgency=' + urgency + ' -t ' + str(durationMsecs) + ' "' + title + '" "' + message + '"')
            debug("%s: notification via notify-send" % (name))

        # if speech is enabled, let's make some noise
        if VAR['USE_SPEECH_NOTIFICATION'] and USE_SPEECH:
            espeak.synth(message)
            debug("%s: speach" % (name))

    # returns the number of seconds a user has spent
    def getTime(self, tfile):
        name = "getTime"
        debug("%s: config file (%s) read" % (name, tfile))

        # check for file
        if not isfile(tfile):
            debug("%s: config file (%s) NOT found!" % (name, tfile), True)
            return 0, False

        # get seconds spent
        t = open(tfile)
        time = int(t.readline())
        t.close()

        # pass back time
        return time, True

    def getTimeLeft(self):
        name = "getTimeLeft"
        # get day
        index = int(strftime("%w"))

        # calculates how much time if left
        usedtime, verified = self.getTime(self.timefile)
        timeleft = self.limits[index] - usedtime
        timeuntil = self.timeofbto(index) - datetime.datetime.now()
        tuntil = timeuntil.seconds

        # what is less (is "until" time earlier than limit)
        if timeleft <= tuntil:
            left = timeleft
        else:
            left = tuntil

        debug("%s: used: %d, left: %d, until: %d, left: %d" % (name, usedtime, timeleft, tuntil, left))

        # return what's left :)
        return left

    # return the time limit
    def timeofbto(self, index):
        # current date
        y = datetime.date.today().year
        m = datetime.date.today().month
        d = datetime.date.today().day

        # to hour
        h = self.bto[index]

        # compose new date
        date = datetime.date(y, m, d)

        # correct date
        if h == 24:
            h = 0
            date = date + datetime.timedelta(days=1)

        # final calculation for date
        dt = datetime.datetime(date.year, date.month, date.day, h, 0, 0)

        # done
        return dt

    # divides time into larger pieces :)
    def fractSec(self, s):
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return h, m, s

    # this gets session information
    def getSessionName(self):
        debug("session name: %s" % (os.getenv('XDG_CURRENT_DESKTOP')))
        return os.getenv('XDG_CURRENT_DESKTOP')

    # get KDE version
    def getSessionVersion(self, sessionName):
        # defaults
        version = 0

        # for KDE check KDE version
        if sessionName == "KDE":
            # get KDE version
            versionTmp = os.getenv('KDE_SESSION_VERSION')

            # get version
            if version == "\n" or version == "":
                version = 3
            else:
                version = int(versionTmp)

        debug("session version: %d" % (version))
        # final version
        return version

    def quit(self):
        Gtk.main_quit()

if __name__ == "__main__":
    init_locale()
    init_espeak()
    # add local configuration to dictionary
    VAR.update(load_config(DEVACTIVE))
    indicator = IndicatorTimekpr()
    Gtk.main()
