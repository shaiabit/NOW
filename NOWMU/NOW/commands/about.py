from evennia import default_cmds
from evennia.utils import utils
import os
import sys
import twisted
import django


class CmdAbout(default_cmds.MuxCommand):
    """
    Display info about the game engine.
    Usage:
      about
    """

    key = 'about'
    locks = 'cmd:all()'
    help_category = 'System'

    def func(self):
        """Show the version"""

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
               django.get_version())
        self.caller.msg(string)
