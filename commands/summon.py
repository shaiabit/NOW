# -*- coding: UTF-8 -*-
from commands.command import MuxCommand
from evennia.server.sessionhandler import SESSIONS

class CmdSummon(MuxCommand):
    """
    Open portal from object's location to yours, or location you specify.
    The portal forms 30 seconds later and is, under some circumstances,
    one-way only.
    Usage:
      summon/switch <object>[ = <location>]
    Options:
    /quiet     Portal arrives quietly to others in room.
    /only      Only the summoned object can use the portal exit.
    /vanish    if set, the portal leads to Nothingness.
               When this option is used, <location> is ignored.
    Examples:
      summon Tria
      summon/quiet Rulan=poof
      summon/only LazyLion
      summon/vanish me
    """
    key = 'summon'
    aliases = ['msummon', 'meet']
    locks = 'cmd:perm(summon) or perm(Players)'
    help_category = 'Travel'

    def func(self):
        """Performs the summon, accounting for in-world conditions."""

        char = self.character
        loc = char.location
        cmd = self.cmdstring
        player = self.player
        args = self.args
        lhs, rhs = self.lhs, self.rhs
        opt = self.switches

        if char and char.ndb.currently_moving:
            player.msg("You can not summon while moving. (|rstop|n, then try again.)")
            return
        if not args:
            char.msg("Error: no character. Usage: summon <character>.")
            return
        session_list = SESSIONS.get_sessions()
        target = []
        for session in session_list:
            if not session.logged_in:
                continue
            puppet = session.get_puppet()
            if lhs.lower() in puppet.get_display_name(char, plain=True).lower():
                target.append(puppet)
        if len(target) < 1:
            char.msg("Error: character not found.")
            return
        if len(target) > 1:  # Too many partial matches, try exact matching.
            char.msg("Error: character not found.")
            return
        else:
            target[0].msg("You are being summoned to %s " % loc.get_display_name(target[0]) +
                          "by %s" % char.get_display_name(target[0]) +
                          ". A portal should appear soon that will take you to " +
                          "%s." % char.get_display_name(target[0]))
            char.msg("You begin to summon a portal to bring %s" % target[0].get_display_name(char) +
                     " to your location.")
