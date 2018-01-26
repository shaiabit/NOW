# -*- coding: utf-8 -*-
"""
system commands
from evennia/commands/default/system.py
Allows for customizations by importing them here.
"""
from __future__ import division

import traceback
import os
import datetime
import sys
import django
import twisted
import time

from django.conf import settings
from evennia.server.sessionhandler import SESSIONS
from evennia.scripts.models import ScriptDB
from evennia.objects.models import ObjectDB
from evennia.accounts.models import AccountDB
from evennia.utils import logger, utils, gametime, create
from evennia.utils.eveditor import EvEditor
from evennia.utils.evtable import EvTable
from evennia.utils.utils import crop, class_from_module

COMMAND_DEFAULT_CLASS = class_from_module(settings.COMMAND_DEFAULT_CLASS)

# delayed imports
_RESOURCE = None
_IDMAPPER = None

# limit symbol import for API
__all__ = ("CmdReload", "CmdReset", "CmdShutdown", "CmdPy",
           "CmdScripts", "CmdObjects", "CmdService", "CmdAbout",
           "CmdTime", "CmdServerLoad")

from evennia.commands.default.system import CmdReload
CmdReload.locks = 'cmd:perm(reload) or perm(immortal)'
CmdReload.help_category = 'System'


from evennia.commands.default.system import CmdReset
CmdReset.locks = 'cmd:perm(reset) or perm(immortal)'
CmdReset.help_category = 'System'


from evennia.commands.default.system import CmdShutdown
CmdShutdown.locks = 'cmd:perm(shutdown) or perm(immortal)'
CmdShutdown.help_category = 'System'

from evennia.commands.default.system import _py_load
from evennia.commands.default.system import _py_code
from evennia.commands.default.system import _py_quit
from evennia.commands.default.system import _run_code_snippet


from evennia.commands.default.system import CmdPy
CmdPy.locks = 'cmd:perm(py) or perm(immortal)'
CmdPy.help_category = 'System'

# helper function. Kept outside so it can be imported and run
# by other commands.

from evennia.commands.default.system import format_script_list

from evennia.commands.default.system import CmdScripts
CmdScripts.locks = 'cmd:perm(scripts) or perm(wizard)'
CmdScripts.help_category = 'System'


from evennia.commands.default.system import CmdObjects
CmdObjects.locks = 'cmd:perm(objects) or perm(builder)'
CmdObjects.help_category = 'Building'


from evennia.commands.default.system import CmdAccounts
CmdAccounts.locks = 'cmd:perm(accounts) or perm(wizard)'
CmdAccounts.help_category = 'Administration'


from evennia.commands.default.system import CmdService
CmdService.locks = 'cmd:perm(service) or perm(immortal)'
CmdService.help_category = 'System'

from evennia.commands.default.system import CmdAbout  # replaced
from evennia.commands.default.system import CmdTime   # replaced

from evennia.commands.default.system import CmdServerLoad
CmdServerLoad.locks = 'cmd:perm(load) or perm(immortal)'
CmdServerLoad.help_category = 'System'


from evennia.commands.default.system import CmdTickers
CmdTickers.locks = 'cmd:perm(tickers) or perm(builder)'
CmdTickers.help_category = 'Building'
