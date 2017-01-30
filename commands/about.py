# -*- coding: UTF-8 -*-
from commands.command import MuxCommand
from evennia.players.models import PlayerDB
from evennia.utils import utils
import os
import sys
import twisted
import django


class CmdAbout(MuxCommand):
    """
    Display info about NOW or target.
    Usage:
      about [target]
    """
    key = 'about'
    locks = 'cmd:all()'
    help_category = 'System'

    def func(self):
        """Display information about server or target"""
        opt = self.switches
        args = unicode(self.args).strip()
        if 'last' in opt:
            if args:
                return
            recent_users = PlayerDB.objects.get_recently_connected_players()[:10]
            self.caller.msg(recent_users)
            return
        string = """
         |cEvennia|n %s|n
         MUD/MUX/MU* development system
         |wLicence|n https://opensource.org/licenses/BSD-3-Clause
         |wWeb|n http://evennia.com
         |wIrc|n #evennia on FreeNode
         |wForum|n http://evennia.com/discussions
         |wMaintainer|n (2010-)   Griatch (griatch AT gmail DOT com)
         |wMaintainer|n (2006-10) Greg Taylor
         |wOS|n %s
         |wPython|n %s
         |wTwisted|n %s
         |wDjango|n %s
        """ % (utils.get_evennia_version(),
               os.name,
               sys.version.split()[0],
               twisted.version.short(),
               django.get_version()) if args else 'Target information not available.'
        self.caller.private('NOW', 'info', string)
