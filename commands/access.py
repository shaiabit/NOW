# -*- coding: UTF-8 -*-
from django.conf import settings
from commands.command import MuxCommand


class CmdAccess(MuxCommand):
    """
    Displays your current world access levels for
    your current player and character account.
    Usage:
      access
    Switches:
    /groups  - Also displays the system's permission groups hierarchy.
    """
    key = 'access'
    locks = 'cmd:all()'
    help_category = 'System'

    def func(self):
        """Load the permission groups"""
        caller = self.caller
        hierarchy_full = settings.PERMISSION_HIERARCHY
        string = ''
        if 'groups' in self.switches:
            string = "|wPermission Hierarchy|n (climbing): %s|/" % ", ".join(hierarchy_full)
        if caller.player.is_superuser:
            cperms = "<|ySuperuser|n> " + ", ".join(caller.permissions.all())
            pperms = "<|ySuperuser|n> " + ", ".join(caller.player.permissions.all())
        else:
            cperms = ", ".join(caller.permissions.all())
            pperms = ", ".join(caller.player.permissions.all())
        string += "|wYour Player/Character access|n: "
        if hasattr(caller, 'player'):
            string += "Player: (%s: %s) and " % (caller.player.key, pperms)
        string += "Character (%s: %s)" % (caller.get_display_name(self.session), cperms)
        caller.msg(string)
