# -*- coding: utf-8 -*-
from commands.command import MuxCommand
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
    help_category = 'Information'
    locks = 'cmd:all()'
    account_caller = True

    def func(self):
        """Display information about server or target"""
        char = self.character
        account = self.account
        opt = self.switches
        args = unicode(self.args).strip()
        message = ''
        if args:
            pass  #
        else:
            message = """
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
        char.msg(image=['https://raw.githubusercontent.com/evennia/evennia/'
                        'master/evennia/web/website/static/website/images/evennia_logo.png'])
        char.private(None, 'info', message)
