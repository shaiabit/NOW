import time
from evennia.utils import utils
from evennia.commands.default.muxcommand import MuxPlayerCommand


class CmdQuit(MuxPlayerCommand):
    """
    Gracefully disconnect your current session and send optional
    quit reason message to your other sessions, if any.
    Usage:
      quit [reason]
    Switches:
    /all      disconnect from all sessions.
    """
    key = 'quit'
    aliases = ['bye', 'disconnect']
    locks = 'cmd:all()'
    arg_regex = r'^/|\s|$'

    def func(self):
        """hook function"""
        player = self.player
        bye = '|RDisconnecting|n'
        exit_msg = 'Hope to see you again, soon.'

        if self.args.strip():
            bye += " ( |w%s\n ) " % self.args.strip()

        if 'all' in self.switches:
            msg = bye + ' all sessions. ' + exit_msg
            player.msg(msg, session=self.session)
            for session in player.sessions.all():
                player.disconnect_session_from_player(session)
        else:
            nsess = len(player.sessions.all())
            if nsess == 2:
                msg = bye + '. One session is still connected.'
                player.msg(msg, session=self.session)
            elif nsess > 2:
                msg = bye + ". %i sessions are still connected."
                player.msg(msg % (nsess - 1), session=self.session)
            else:
                # If quitting the last available session, give connect time.
                online = utils.time_format(time.time() - self.session.conn_time, 1)
                msg = bye + ' after ' + online + ' online. ' + exit_msg
                player.msg(msg, session=self.session)
            player.disconnect_session_from_player(self.session)
