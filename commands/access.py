# -*- coding: utf-8 -*-
from django.conf import settings
from commands.command import MuxCommand


class CmdAccess(MuxCommand):
    """
    Displays your current world access levels for
    your current account and character account.
    Usage:
      access[/option]
    Options:
    /groups  - Also displays the system's permission groups hierarchy.
    """
    key = 'access'
    options = ('groups',)
    locks = 'cmd:all()'
    help_category = 'System'
    account_caller = True

    def func(self):
        """Load the permission groups"""
        char = self.character
        account = self.account
        hierarchy_full = settings.PERMISSION_HIERARCHY
        info = []  # List of info to output to user
        if 'groups' in self.switches:
            info.append('|wPermission Hierarchy|n (climbing): %s|/' % ", ".join(hierarchy_full))
        if account.is_superuser:
            pperms = '<|ySuperuser|n> ' + ', '.join(account.permissions.all())
            cperms = ('<|ySuperuser|n> ' + ', '.join(char.permissions.all())) if char else None
        else:
            pperms = ', '.join(account.permissions.all())
            cperms = (', '.join(char.permissions.all())) if char else None
        info.append('|wYour Account' + ('/Character' if char else '') + ' access|n: ')
        if account:
            if account.attributes.has('_quell'):
                info.append('|r(quelled)|n ')
            info.append('Account: (%s: %s)' % (account.get_display_name(account), pperms))
        if cperms:
            info.append(' and Character (%s: %s)' % (char.get_display_name(char), cperms))
        self.msg(''.join(info))
