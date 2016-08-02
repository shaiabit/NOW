# -*- coding: UTF-8 -*-
import time
from commands.command import MuxPlayerCommand
from evennia.server.sessionhandler import SESSIONS
from evennia.utils import ansi, utils, create, search, evtable


class CmdWho(MuxPlayerCommand):
    """
    Shows who is currently online.
    Usage:
      who
    Switches:
    /f             - shows character locations, and more info for those with permissions.
    /s or /species - shows species setting for characters in your location.
    """
    key = 'who'
    aliases = 'ws'
    locks = 'cmd:all()'

    def func(self):
        """Get all connected players by polling session."""
        you = self.player
        session_list = SESSIONS.get_sessions()
        opt = self.switches
        session_list = sorted(session_list, key=lambda o: o.player.key)
        show_session_data = you.check_permstring('Immortals') if 'f' in opt else False
        player_count = (SESSIONS.player_count())
        table = evtable.EvTable(border='none')
        if 'f' in opt or 'full' in opt:
            if show_session_data:
                # privileged info - who/f by wizard or immortal
                table.add_row('|wCharacter', '|wLocation', '|wPlayer Name', '|wOn for', '|wIdle',  '|wCmds',
                              '|wProtocol', '|wAddress')
                table.reformat_column(0, width=15, align='l')
                table.reformat_column(1, width=15, align='l')
                table.reformat_column(2, width=15, align='r')
                table.reformat_column(3, width=8, align='l')
                table.reformat_column(4, w4idth=7, align='l')
                table.reformat_column(5, width=6, align='r')
                table.reformat_column(6, width=12, align='l')
                table.reformat_column(7, width=18, align='r')
                for session in session_list:
                    if not session.logged_in:
                        continue
                    delta_cmd = time.time() - session.cmd_last_visible
                    delta_conn = time.time() - session.conn_time
                    player = session.get_player()
                    puppet = session.get_puppet()
                    location = puppet.location.get_display_name(you)\
                        if puppet and puppet.location else '|222Nothingness|n'
                    table.add_row(puppet.get_display_name(you) if puppet else 'None', location,
                                  player.get_display_name(you),
                                  utils.time_format(delta_conn, 0), utils.time_format(delta_cmd, 1),
                                  session.cmd_total, session.protocol_key,
                                  isinstance(session.address, tuple) and session.address[0] or session.address)
            else:  # unprivileged info - who/f by player
                table.add_row('|wCharacter', '|wOn for', '|wIdle', '|wLocation')
                table.reformat_column(0, width=25, align='l')
                table.reformat_column(1, width=8, align='l')
                table.reformat_column(2, width=7, align='r')
                table.reformat_column(3, width=25, align='l')
                for session in session_list:
                    if not session.logged_in:
                        continue
                    delta_cmd = time.time() - session.cmd_last_visible
                    delta_conn = time.time() - session.conn_time
                    character = session.get_puppet()
                    location = character.location.key if character and character.location else 'Nothingness'
                    table.add_row(character.key if character else '- Unknown -',
                                  utils.time_format(delta_conn, 0), utils.time_format(delta_cmd, 1), location)
        else:
            if 's' in opt or 'species' in opt or self.cmdstring == 'ws':
                my_character = self.caller.get_puppet(self.session)
                if not (my_character and my_character.location):
                    self.msg("You can't see anyone here.")
                    return
                table.add_row('|wCharacter', '|wOn for', '|wIdle', '|wSpecies')
                table.reformat_column(0, width=25, align='l')
                table.reformat_column(1, width=8, align='l')
                table.reformat_column(2, width=7, align='r')
                table.reformat_column(3, width=25, align='l')
                for session in session_list:
                    character = session.get_puppet()
                    if not session.logged_in or not character or character.location != my_character.location:
                        continue
                    delta_cmd = time.time() - session.cmd_last_visible
                    delta_conn = time.time() - session.conn_time
                    character = session.get_puppet()
                    species = character.attributes.get('species', default='*ghost*')
                    table.add_row(character.key if character else '*ghost*',
                                  utils.time_format(delta_conn, 0), utils.time_format(delta_cmd, 1), species)
            else:  # unprivileged info - who
                table.add_row('|wCharacter', '|wOn for', '|wIdle')
                table.reformat_column(0, width=25, align='l')
                table.reformat_column(1, width=8, align='l')
                table.reformat_column(2, width=7, align='r')
                for session in session_list:
                    if not session.logged_in:
                        continue
                    delta_cmd = time.time() - session.cmd_last_visible
                    delta_conn = time.time() - session.conn_time
                    character = session.get_puppet()
                    table.add_row(character.key if character else '- Unknown -',
                                  utils.time_format(delta_conn, 0), utils.time_format(delta_cmd, 1))
        is_one = player_count == 1
        string = '%s' % 'A' if is_one else str(player_count)
        string += ' single ' if is_one else ' unique '
        plural = ' is' if is_one else 's are'
        string += 'account%s logged in.' % plural
        you.msg(table)
        you.msg(string)
