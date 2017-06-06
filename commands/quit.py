# -*- coding: UTF-8 -*-
from commands.command import MuxPlayerCommand
from evennia.utils import utils
import time


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
    options = ('all',)

    def func(self):
        """hook function"""
        player = self.player
        bye = '|RDisconnecting|n'
        exit_msg = 'Hope to see you again, soon.'
        reason = self.args.strip() if self.args else 'Quitting'
        if reason:
            bye += " ( |w%s|n ) " % reason
        if 'all' in self.switches:
            for session in player.sessions.all():
                session_online_time = utils.time_format(time.time() - session.conn_time, 1)
                msg = bye + ' all sessions after ' + session_online_time + ' online. '
                player.msg(msg, session=session)
                player.msg(exit_msg, session=session)
                player.disconnect_session_from_player(session, reason=reason)
        else:
            session_count = len(player.sessions.all())
            online = utils.time_format(time.time() - self.session.conn_time, 1)
            if session_count == 2:
                msg = bye
                others = [x for x in self.player.sessions.get() if x is not self.session]
                player.msg(msg + 'after ' + online + ' online.', session=self.session)
                player.msg(msg + 'your other session. |gThis session remains connected.|n', session=others)
            elif session_count > 2:
                msg = bye + "%i sessions are still connected."
                player.msg(msg % (session_count - 1))
            else:
                # If quitting the last available session, give connect time.
                msg = bye + 'after ' + online + ' online. '
                player.msg(msg, session=self.session)
            player.msg(exit_msg, session=self.session)
            player.disconnect_session_from_player(self.session, reason=reason)
