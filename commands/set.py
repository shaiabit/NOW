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
        # where = self.obj
        player = self.player
        setting = char.db.settings or {}
        message = char.db.messages or {}

        if 'set' in cmd:
            if 'list' in opt or not args:
                if not char.db.settings:
                    char.db.settings = {}
                player.msg('Listing %s control panel settings: |g%s'
                           % (char.get_display_name(player), '|n, |g'.join('|lcset/toggle %s|lt%s|le|n: |c%s'
                                                                           % (each, each, char.db.settings[each])
                                                                           for each in char.db.settings)))
                return
            if 'on' in opt or 'off' in opt or 'toggle' in opt or 'symbol' in opt or 'message' in opt:
                action = opt[0]
                if action == 'on':
                    action = 'engage'
                    setting[args] = True
                    status = True
                elif action == 'off':
                    action = 'disengage'
                    setting[args] = False
                    status = False
                elif action == 'value':
                    action = 'dial'
                    setting[lhs] = int(rhs)
                    status = int(rhs)
                elif action == 'symbol':
                    action = 'dial'
                    setting[lhs] = rhs
                    status = rhs
                elif action == 'message':
                    action = 'set'
                    message[lhs] = rhs
                    status = rhs
                else:  # Toggle setting
                    setting[args] = False if char.db.settings and args in char.db.settings\
                                             and char.db.settings[args] else True
                    status = setting[args]
                mode = 'messages' if action == 'set' else 'settings'
                if rhs:
                    string = '|wYou %s %s to %s on %s character %s to "%s".' % \
                              (action, lhs if lhs else 'something', rhs, char.get_display_name(player), mode, status)
                else:
                    string = '|wYou %s %s on %s character %s to "%s".' %\
                              (action, args if args else 'something', char.get_display_name(player), mode, status)
                player.msg(string)  # Notify player of character setting changes.
                if action == 'set' and rhs:
                    char.db.messages = message
                else:
                    char.db.settings = setting
