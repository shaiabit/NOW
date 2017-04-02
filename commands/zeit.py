import datetime
from django.conf import settings
from commands.command import MuxCommand
from evennia.utils.evtable import EvTable
from evennia.utils import logger, utils, gametime, create


class CmdTime(MuxCommand):
    """
    show server time statistics
    Usage:
      time
    List Server time statistics such as uptime
    and the current time stamp.
    """
    key = 'time'
    aliases = 'uptime'
    locks = 'cmd:perm(time) or perm(Players)'
    help_category = 'World'
    player_caller = True

    def func(self):
        """Show server time data in a table."""
        table1 = EvTable("|wServer time", "", align="l", width=78)
        table1.add_row("Current uptime", utils.time_format(gametime.uptime(), 3))
        table1.add_row("Total runtime", utils.time_format(gametime.runtime(), 2))
        table1.add_row("First start", datetime.datetime.fromtimestamp(gametime.server_epoch()))
        table1.add_row("Current time", datetime.datetime.now())
        table1.reformat_column(0, width=30)
        table2 = EvTable("|wIn-Game time", "|wReal time x %g" % gametime.TIMEFACTOR, align="l", width=77, border_top=0)
        epochtxt = "Epoch (%s)" % ("from settings" if settings.TIME_GAME_EPOCH else "server start")
        table2.add_row(epochtxt, datetime.datetime.fromtimestamp(gametime.game_epoch()))
        table2.add_row("Total time passed:", utils.time_format(gametime.gametime(), 2))
        table2.add_row("Current time ", datetime.datetime.fromtimestamp(gametime.gametime(absolute=True)))
        table2.reformat_column(0, width=30)
        self.caller.msg(unicode(table1) + "\n" + unicode(table2))