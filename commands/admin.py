# -*- coding: utf-8 -*-
"""

Admin commands
from evennia/commands/default/admin.py
"""

import time
import re
from django.conf import settings
from evennia.server.sessionhandler import SESSIONS
from evennia.server.models import ServerConfig
from evennia.utils import evtable, search, class_from_module
# Importing Evennia default admin commands:
from evennia.commands.default.admin import CmdBoot
from evennia.commands.default.admin import list_bans
from evennia.commands.default.admin import CmdBan
from evennia.commands.default.admin import CmdUnban
from evennia.commands.default.admin import CmdDelAccount
from evennia.commands.default.admin import CmdEmit
from evennia.commands.default.admin import CmdNewPassword
from evennia.commands.default.admin import CmdPerm

COMMAND_DEFAULT_CLASS = class_from_module(settings.COMMAND_DEFAULT_CLASS)

PERMISSION_HIERARCHY = [p.lower() for p in settings.PERMISSION_HIERARCHY]

# limit members for API inclusion
__all__ = ('CmdBoot', 'CmdBan', 'CmdUnban', 'CmdDelAccount',
           'CmdEmit', 'CmdNewPassword', 'CmdPerm', 'CmdWall')

# Overwriting Evennia defaults for CmdBoot:
CmdBoot.locks = 'cmd:perm(boot) or perm(helpstaff)'
CmdBoot.help_category = 'Administration'

# regex matching IP addresses with wildcards, eg. 233.122.4.*
IPREGEX = re.compile(r"[0-9*]{1,3}\.[0-9*]{1,3}\.[0-9*]{1,3}\.[0-9*]{1,3}")

# Overwriting Evennia defaults for CmdBan:
CmdBan.locks = 'cmd:perm(ban) or perm(immortal)'
CmdBan.help_category = 'Administration'

# Overwriting Evennia defaults for CmdUnban:
CmdUnban.locks = 'cmd:perm(unban) or perm(immortal)'
CmdUnban.help_category = 'Administration'

# Overwriting Evennia defaults for CmdDelAccount:
CmdDelAccount.locks = 'cmd:perm(delaccount) or perm(immortal)'
CmdDelAccount.help_category = 'Administration'

# Overwriting Evennia defaults for CmdEmit:
CmdEmit.locks = 'cmd:perm(emit) or perm(helpstaff)'
CmdEmit.help_category = 'Administration'

# Overwriting Evennia defaults for CmdNewPassword:
CmdNewPassword.locks = 'cmd:perm(newpassword) or perm(wizard)'
CmdNewPassword.help_category = 'Administration'

# Overwriting Evennia defaults for CmdPerm:
CmdPerm.locks = 'cmd:perm(perm) or perm(immortal)'
CmdPerm.help_category = 'Administration'


# Overwriting Evennia command CmdWall:
class CmdWall(COMMAND_DEFAULT_CLASS):
    """
    make an announcement to all

    Usage:
      @wall <message>

    Announces a message to all connected sessions
    including all currently unlogged in.
    """
    key = '@wall'
    aliases = ['announce']
    locks = 'cmd:perm(wall) or perm(wizard)'
    help_category = 'Administration'

    def func(self):
        """Implements command"""
        if not self.args:
            self.caller.msg('Usage: {} <message>'.format(self.cmdstring))
            return
        message = '### %s%s|n shouts "|w%s|n"' % (self.caller.STYLE, self.caller.name, self.args)
        self.msg("Announcing to all connections ...")
        SESSIONS.announce_all(message)
