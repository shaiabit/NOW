# -*- coding: utf-8 -*-
import evennia
from evennia.utils.utils import delay
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
    /in        Portal is one-way; into summon location.
    /out       Portal is one-way; summon location outward
    /vanish    if set, the portal leads to Nothingness.
               When this option is used, <location> is ignored.
    Examples:
      summon Tria
      summon/quiet Rulan=poof
      summon/only LazyLion
      summon/vanish me
    """
    key = 'summon'
    aliases = ['meet', 'join']
    options = ('quiet', 'only', 'in', 'out', 'vanish')
    locks = 'cmd:pperm(denizen)'
    help_category = 'Travel'

    def func(self):
        """
            Performs the summon, accounting for in-world conditions.
            join: Implies one way portal to target
            summon: Implies one way portal to summoner
            meet: Implies two-way portal
        """

        char = self.character
        cmd = self.cmdstring
        loc = char.location
        account = self.account
        args = self.args
        lhs, rhs = self.lhs, self.rhs
        opt = self.switches  # TODO - add code to make the switches work.
        
        error_private = 'is in a private room that does not allow portals to form.'

        if char and char.ndb.currently_moving:
            account.msg("You can not open a portal while moving. (|rstop|n, then try again.)")
            return
        if not args:
            char.msg("Could not find target. Usage: {} <character or NPC>".format(cmd))
            return
        session_list = SESSIONS.get_sessions()
        target = []
        # Check for private flag on source room. It must be controlled by summoner if private.
        if loc.tags.get('private', category='flags') and not loc.access(char, 'control'):
            char.msg('Error: This ' + error_private)
            return
        # Check object pool filtered by tagged "pool" and located in None.
        obj_pool = [each for each in evennia.search_tag('pool', category='portal') if not each.location]
        print('Object pool total: %i' % len(obj_pool))
        if len(obj_pool) < 2:
            char.msg('Portals are currently out of stock or in use elsewhere.')
            return
        portal_enter, portal_exit = obj_pool[-2:]
        for session in session_list:
            if not (session.logged_in and session.get_puppet()):
                continue
            puppet = session.get_puppet()
            if lhs.lower() in puppet.get_display_name(char, plain=True).lower():
                target.append(puppet)
        if len(target) < 1:
            char.msg("Error: Specific character name not found.")
            return
        elif len(target) > 1:  # Too many partial matches, try exact matching.
            char.msg("Error: Unique character name not found.")
            return
        else:
            target = target[0]
            # Check for private flag on destination room. If so, check for in/out locks.
            there = target.location
            if there and there.tags.get('private', category='flags') and not there.access(char, 'control'):
                char.msg("Error: Destination of portal" + error_private)
                return
        # Check if A can walk to B, or B to A depending on meet or summon
            meet_message = ('You are being joined by {summoner} from {loc}.')
            summon_message = ('You are being summoned to {loc} by {summoner}.')
            message = meet_message if 'meet' in cmd else summon_message
            loc_name = loc.get_display_name(target)
            my_name = target.get_display_name(target)
            target_name = target.get_display_name(char)
            char_name = char.get_display_name(target)
            target.msg(message.format(summoner=char_name, loc=loc_name))
            target.msg('A portal should appear soon.')
            char.msg("You begin to open a portal connecting %s" % target_name +
                     " and your location.")

        def open_portal():
            """Move inflatable portals into place."""
            portal_enter.move_to(target.location)
            portal_exit.move_to(loc)
            # If only in opt, lock entering to the target, only
            # If in or out, meet or summon, lock one portal end, depending.
            # If portal to Nothingness, only send one portal

        delay(10, callback=open_portal)  # 10 seconds later, the portal (exit pair) appears.

        def close_portal():
            """Remove and store inflatable portals in Nothingness."""
            for each in portal_enter.contents:
                each.move_to(target.location)
            for each in portal_exit.contents:
                each.move_to(loc)
            portal_enter.location.msg_contents("|r%s|n vanishes into |xNo|=gth|=fin|=egn|=des|=css|n." % portal_enter)
            portal_exit.location.msg_contents("|r%s|n vanishes into |xNo|=gth|=fin|=egn|=des|=css|n." % portal_exit)
            portal_enter.move_to(None, to_none=True)
            portal_exit.move_to(None, to_none=True)

        delay(180, callback=close_portal)  # Wait, then move portal objects to the portal pool in Nothingness
