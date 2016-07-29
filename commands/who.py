# -*- coding: UTF-8 -*-
import time
from commands.command import MuxPlayerCommand
from evennia.server.sessionhandler import SESSIONS
from evennia.utils import ansi, utils, create, search, prettytable


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
        player = self.player
        session_list = SESSIONS.get_sessions()
        session_list = sorted(session_list, key=lambda o: o.player.key)
        show_session_data = player.check_permstring('Immortals') if 'f' in self.switches else False
        nplayers = (SESSIONS.player_count())
        if 'f' in self.switches or 'full' in self.switches:
            if show_session_data:
                # privileged info - who/f by wizard or immortal
                table = prettytable.PrettyTable(["|wPlayer Name",
                                                 "|wOn for",
                                                 "|wIdle",
                                                 "|wCharacter",
                                                 "|wRoom",
                                                 "|wCmds",
                                                 "|wProtocol",
                                                 "|wHost"])
                for session in session_list:
                    if not session.logged_in:
                        continue
                    delta_cmd = time.time() - session.cmd_last_visible
                    delta_conn = time.time() - session.conn_time
                    player = session.get_player()
                    puppet = session.get_puppet()
                    location = puppet.location.get_display_name(self.player)\
                        if puppet and puppet.location else '|222Nothingness|n'
                    table.add_row([utils.crop(player.get_display_name(self.player), width=25),
                                   utils.time_format(delta_conn, 0),
                                   utils.time_format(delta_cmd, 1),
                                   utils.crop(puppet.get_display_name(self.player) if puppet else 'None', width=25),
                                   utils.crop(location, width=25),
                                   session.cmd_total,
                                   session.protocol_key,
                                   isinstance(session.address, tuple) and session.address[0] or session.address])
            else:  # unprivileged info - who/f by player
                table = prettytable.PrettyTable(["|wCharacter", "|wOn for", "|wIdle", "|wLocation"])
                for session in session_list:
                    if not session.logged_in:
                        continue
                    delta_cmd = time.time() - session.cmd_last_visible
                    delta_conn = time.time() - session.conn_time
                    character = session.get_puppet()
                    location = character.location.key if character and character.location else 'Nothingness'
                    table.add_row([utils.crop(character.key if character else '- Unknown -', width=25),
                                   utils.time_format(delta_conn, 0),
                                   utils.time_format(delta_cmd, 1),
                                   utils.crop(location, width=25)])
        else:
            if 's' in self.switches or 'species' in self.switches or self.cmdstring == 'ws':
                my_character = self.caller.get_puppet(self.session)
                if not (my_character and my_character.location):
                    self.msg("You can't see anyone here.")
                    return
                table = prettytable.PrettyTable(["|wCharacter", "|wOn for", "|wIdle", "|wSpecies"])
                for session in session_list:
                    character = session.get_puppet()
                    if not session.logged_in or not character or character.location != my_character.location:
                        continue
                    delta_cmd = time.time() - session.cmd_last_visible
                    delta_conn = time.time() - session.conn_time
                    character = session.get_puppet()
                    species = character.attributes.get('species', default='*ghost*')
                    table.add_row([utils.crop(character.key if character else '*ghost*', width=25),
                                   utils.time_format(delta_conn, 0),
                                   utils.time_format(delta_cmd, 1),
                                   utils.crop(species, width=25)])
            else:  # unprivileged info - who
                table = prettytable.PrettyTable(["|wCharacter", "|wOn for", "|wIdle"])
                for session in session_list:
                    if not session.logged_in:
                        continue
                    delta_cmd = time.time() - session.cmd_last_visible
                    delta_conn = time.time() - session.conn_time
                    character = session.get_puppet()
                    table.add_row([utils.crop(character.key if character else '- Unknown -', width=25),
                                   utils.time_format(delta_conn, 0),
                                   utils.time_format(delta_cmd, 1)])
        is_one = nplayers == 1
        string = "%s\n%s " % (table, 'A' if is_one else nplayers)
        string += 'single' if is_one else 'unique'
        plural = '' if is_one else 's'
        string += " account%s logged in." % plural
        self.msg(string)
