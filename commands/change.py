# -*- coding: utf-8 -*-
from commands.command import MuxCommand


class CmdChange(MuxCommand):
    """
    Operate various aspects of character configuration.
    Usage:
      change[/option] [setting] [=|to value]
    Options:
    /on
    /off
    /value
    /symbol
    /clear
    /show

    Not supplying a setting assumes you just want to view all settings.
    Not supplying a value assumes you just want to toggle the value on/off.
    """
    key = 'change'
    aliases = ['clear', 'show', 'set']
    locks = 'cmd:all()'
    options = ('on', 'off', 'value', 'symbol', 'clear', 'show')
    parse_using = ' to '
    help_category = 'Building'
    account_caller = True

    def func(self):
        """
        This function tries to be user-friendly, and allow
        any messages and settings to be configured on the
        character or the current room the character is in
        and can edit.  Name-changing functionality coming soon.
        """
        cmd = self.cmdstring
        opt = self.switches
        args = self.args.strip()
        lhs, rhs = [self.lhs, self.rhs]
        char = self.character
        # where = self.obj
        account = self.account
        setting = char.db.settings or {}
        message = char.db.messages or {}

        if 'clear' in cmd or 'clear' in opt:  # TODO: clear command/option functionality
            caller.msg('Functionality not complete. Nothing done.')
            return

        if 'list' in opt or not args or 'show' in cmd:
            messages = char.db.messages
            if not messages:
                char.db.messages = {}
            messages_filtered = {i: messages[i] for i in messages if i.lower().startswith(args.lower())} if\
                args else messages
            account.msg('Listing %s message settings: |g%s'
                        % (char.get_display_name(account), '|n, |g'.join('|g%s|n: |c%s|n'
                                                                         % (each, messages_filtered[each])
                                                                         for each in messages_filtered)))
            settings = char.db.settings
            if not settings:
                char.db.settings = {}
            settings_filtered = {i: settings[i] for i in settings if i.lower().startswith(args.lower())} if\
                args else settings
            account.msg('Listing %s control panel settings: |g%s'
                        % (char.get_display_name(account), '|n, |g'.join('|lcchange %s|lt%s|le|n: |c%s'
                                                                         % (each, each, settings_filtered[each])
                                                                         for each in settings_filtered)))
            return  # Listing messages and settings is done
        # Some other action still needs to be done
        action = 'message' if rhs else 'toggle'
        if (rhs and rhs.lower() in ('on', 'true', '1', 'yes')) or opt and opt[0] == 'on':
            action = 'on'
        elif (rhs and rhs.lower() in ('off', 'false', '0', 'no')) or opt and opt[0] == 'off':
            action = 'off'
        #  Action is acted upon depending on what is needed to be done
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
                      (action, lhs if lhs else 'something', rhs, char.get_display_name(account), mode, status)
        else:
            string = '|wYou %s %s on %s character %s to "%s".' %\
                      (action, args if args else 'something', char.get_display_name(account), mode, status)
        account.msg(string)  # Notify account of character setting changes.
        if action == 'set' and rhs:
            char.db.messages = message
        else:
            char.db.settings = setting
