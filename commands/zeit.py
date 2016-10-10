import datetime

from commands.command import MuxCommand
from evennia.utils import logger, utils, gametime, create, prettytable


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
        table = prettytable.PrettyTable(['|wserver time statistic', '|wtime'])
        table.align = 'l'
        table.add_row(['Current server uptime', utils.time_format(gametime.uptime(), 3)])
        table.add_row(['Total server running time', utils.time_format(gametime.runtime(), 2)])
        table.add_row(['Total in-game time (realtime x %g)'
                       % gametime.TIMEFACTOR, utils.time_format(gametime.gametime(), 2)])
        table.add_row(['Server time stamp', datetime.datetime.now()])
        self.caller.msg(str(table))
