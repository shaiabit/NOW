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

    def func(self):
        """hook function"""
        player = self.player
        bye = '|RDisconnecting|n'
        exit_msg = 'Hope to see you again, soon.'
        reason = self.args.strip() if self.args else 'Quitting'
        if reason:
            bye += " ( |w%s ) " % reason
        if 'all' in self.switches:
            msg = bye + ' all sessions. ' + exit_msg
            for session in player.sessions.all():
                player.msg(msg, session=session)
                player.msg(exit_msg, session=session)
                player.disconnect_session_from_player(session, reason=reason)
        else:
            session_count = len(player.sessions.all())
            if session_count == 2:
                msg = bye
                others = self.player.sessions.get()
                if self.session in others:
                    others.remove(self.session)
                print(repr(all))
                player.msg(msg + 'One session remains connected.', session=self.session)
                player.msg(msg + 'Your session remains connected.', session=others)
            elif session_count > 2:
                msg = bye + "%i sessions are still connected."
                player.msg(msg % (session_count - 1))
            else:
                # If quitting the last available session, give connect time.
                online = utils.time_format(time.time() - self.session.conn_time, 1)
                msg = bye + ' after ' + online + ' online. ' + exit_msg
                player.msg(msg, session=self.session)
            player.msg(exit_msg, session=self.session)
            player.disconnect_session_from_player(self.session, reason=reason)
