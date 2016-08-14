# -*- coding: UTF-8 -*-
from commands.command import MuxCommand
from evennia import CmdSet


class SettingsCmdSet(CmdSet):
    key = 'settings'

    def at_cmdset_creation(self):
        """Add command to the set - this set will be attached to the item or room."""
        self.add(CmdSettings())


class CmdSettingsDefault(MuxCommand):
    """Add command to the set - this set will be attached to the item or room."""
    key = 'set'
    locks = 'cmd:all()'
    help_category = 'Settings'
    player_caller = True


class CmdSettings(CmdSettingsDefault):
    """
    Operate various aspects of character configuration.
    Usage:
      set[/option] [setting] [= value]
    Options:
    /on
    /off
    /toggle
    /value
    /symbol
    /message
    """

    def func(self):
        """ """
        cmd = self.cmdstring
        opt = self.switches
        args = self.args.strip()
        lhs, rhs = [self.lhs, self.rhs]
        char = self.character
        where = self.obj
        player = self.player
        setting = char.db.settings or {}
        message = char.db.messages or {}

        if 'set' in cmd:
            if 'list' in opt or not args:
                if not char.db.settings:
                    char.db.settings = {}
                player.msg('Listing %s%s|n control panel settings: |g%s'
                           % (char.STYLE, char.key, '|n, |g'.join('%s|n: |c%s' % (each, char.db.settings[each])
                                                                  for each in char.db.settings)))
                return
            if 'on' in opt or 'off' in opt or 'toggle' in opt or 'symbol' in opt or 'message' in opt:
                action = opt[0]
                if action == 'on':
                    action = 'engage'
                    setting[args] = True
                elif action == 'off':
                    action = 'disengage'
                    setting[args] = False
                elif action == 'value':
                    action = 'dial'
                    setting[lhs] = int(rhs)
                elif action == 'symbol':
                    action = 'dial'
                    setting[lhs] = rhs
                elif action == 'message':
                    action = 'set'
                    message[lhs] = rhs
                else:  # Toggle setting
                    setting[args] = False if char.db.settings and args in char.db.settings\
                                             and char.db.settings[args] else True
                mode = 'messages' if action == 'set' else 'settings'
                if rhs:
                    string = '|g%s|n %ss %s to %s on %s%s|n character %s.' % \
                              (char.key, action, lhs if lhs else 'something', rhs, where.STYLE, where.key, mode)
                else:
                    string = '|g%s|n %ss %s on %s%s|n character %s.' %\
                              (char.key, action, args if args else 'something', where.STYLE, where.key, mode)
                player.msg(string)  # Notify player of character setting changes.
                if action == 'set' and rhs:
                    char.db.messages = message
                else:
                    char.db.settings = setting
