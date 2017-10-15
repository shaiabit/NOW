# -*- coding: utf-8 -*-
from commands.command import MuxAccountCommand
from evennia.utils import utils
import time


class CmdQuit(MuxAccountCommand):
    """
    Gracefully disconnect your current session and send optional
    quit reason message to your other sessions, if any.
    Usage:
      quit [reason]
    Switches:
    /all      disconnect from all sessions.
    /home     go home, first.
    """
    key = 'quit'
    aliases = ['bye', 'disconnect', 'qhome']
    locks = 'cmd:all()'
    arg_regex = r'^/|\s|$'
    options = ('all', 'home')

    def func(self):
        """hook function"""
        account = self.account
        bye = '|RDisconnecting|n'
        exit_msg = 'Hope to see you again, soon.'
        cmd = self.cmdstring
        opt = self.switches
        char = self.character
        here = char.location
        if 'qhome' in cmd or 'home' in opt and char and here:  # Go home before quitting.
            char.execute_cmd('home')
        reason = self.args.strip() + '(Quitting)'
        if reason:
            bye += " ( |w%s|n ) " % reason
        if 'all' in self.switches:
            for session in account.sessions.all():
                session_online_time = utils.time_format(time.time() - session.conn_time, 1)
                msg = bye + ' all sessions after ' + session_online_time + ' online. '
                account.msg(msg, session=session)
                account.msg(exit_msg, session=session)
                account.disconnect_session_from_account(session, reason + '/ALL')
        else:
            session_count = len(account.sessions.all())
            online = utils.time_format(time.time() - self.session.conn_time, 1)
            if session_count == 2:
                msg = bye
                others = [x for x in self.account.sessions.get() if x is not self.session]
                account.msg(msg + 'after ' + online + ' online.', session=self.session)
                account.msg(msg + 'your other session. |gThis session remains connected.|n', session=others)
            elif session_count > 2:
                msg = bye + "%i sessions are still connected."
                account.msg(msg % (session_count - 1))
            else:
                # If quitting the last available session, give connect time.
                msg = bye + 'after ' + online + ' online. '
                account.msg(msg, session=self.session)
            account.msg(exit_msg, session=self.session)
            account.disconnect_session_from_account(self.session, reason)
