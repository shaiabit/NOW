from evennia import default_cmds
import time
from evennia.server.sessionhandler import SESSIONS
from evennia.utils import utils


class CmdWhoinfo(default_cmds.MuxCommand):
    """Parent class for pre-login who and info commands."""
    locks = "cmd:all()"
    auto_help = True


class CmdWhoUs(CmdWhoinfo):
    key = "who"
    aliases = ["w"]

    def func(self):
        """returns the list of online characters"""  # TODO: pad field widths to fixed length
        nplayers = (SESSIONS.player_count())
        self.caller.msg("[%s] Through the fog you see:" % self.key)
        session_list = SESSIONS.get_sessions()
        string = ' Character  On for  Idle Location'
        for session in session_list:
            if not session.logged_in:
                continue
            delta_cmd = time.time() - session.cmd_last_visible
            delta_conn = time.time() - session.conn_time
            puppet = session.get_puppet()
            location = puppet.location.key if puppet and puppet.location else 'Nothingness'
            string += '|/ ' + '  '.join([utils.crop(puppet.key if puppet else 'None', width=25),
                                         utils.time_format(delta_conn, 0), utils.time_format(delta_cmd, 1),
                                         utils.crop(location, width=25)])
        is_one = nplayers == 1
        string += '|/'
        string += '%s' % 'A' if is_one else str(nplayers)
        string += ' single ' if is_one else ' unique '
        plural = '' if is_one else 's'
        string += 'account%s logged in.' % plural
        self.caller.msg(string)
