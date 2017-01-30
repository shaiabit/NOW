# -*- coding: UTF-8 -*-
"""
Characters are (by default) Objects setup to be puppeted by Players.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.
"""
from evennia import DefaultCharacter
from typeclasses.tangibles import Tangible
from evennia.utils.utils import lazy_property
from traits import TraitHandler
from world.helpers import make_bar, mass_unit
# from evennia.utils.utils import delay  # Delay a follower's arrival after the leader


class Character(DefaultCharacter, Tangible):
    """
    The Character defaults to implementing some of its hook methods with the
    following standard functionality:

    at_basetype_setup - always assigns the DefaultCmdSet to this object type
                    (important!)sets locks so character cannot be picked up
                    and its commands only be called by itself, not anyone else.
                    (to change things, use at_object_creation() instead)
    at_after_move - launches the "look" command
    at_post_puppet(player) -  when Player disconnects from the Character, we
                    store the current location, so the "unconnected" character
                    object does not need to stay on grid but can be given a
                    None-location while offline.
    at_pre_puppet - just before Player re-connects, retrieves the character's
                    old location and puts it back on the grid with a "charname
                    has connected" message echoed to the room
    """
    STYLE = '|c'

    def at_before_move(self, destination):
        """
        Called just before moving object - here we check to see if
        it is supporting another object that is currently in the room
        before allowing the move. If it is, we do prevent the move by
        returning False.
        """
        if not self.location:  # Always allow moving from Nothingness
            return True
        if destination == self.location:  # Prevent move into same room character is already in.
            return False
        if self.nattributes.has('mover'):  # Allow move when being moved by something.
            return True
        if self.db.locked:  # Prevent leaving a room while still sitting.
            self.msg("\nYou're still sitting.")  # stance, prep, obj
            return False  # Object is supporting something; do not move it
        elif self.traits.health and not self.location.tags.get('past', category='realm')\
                and self.traits.health.actual <= 0:  # Prevent move while incapacitated.
            self.msg("You can't move; you're incapacitated!")  # Type 'home' to TODO:
            # go back home and recover, or wait for a healer to come to you.")
            return False
        if self.db.Combat_TurnHandler:  # Prevent move while in combat.
            self.caller.msg("You can't leave while engaged in combat!")
            return False
        if self.attributes.has('riders') and self.db.riders and self.location:  # Test list of riders.
            self.ndb.riders = []
            if self.db.settings and 'carry others' in self.db.settings and self.db.settings['carry others'] is False:
                return True  # Character has riders, but does not want to carry them.
            for each in self.db.riders:
                if each.location == self.location:
                    each.ndb.mover = self
                    if not (each.has_player and each.at_before_move(destination)):
                        continue
                    if each.db.settings and 'carry others' in each.db.settings and each.db.settings['carry others']\
                            is False:
                            continue
                    self.ndb.riders.append(each)
                    self.location.at_object_leave(each, destination)
        return True

    def at_after_move(self, source_location):
        """Store last location and room then trigger the arrival look after a move. Reset doing to default."""
        if source_location:  # Is "None" when moving from Nothingness. If so, do nothing.
            self.ndb.last_location = source_location
            if not source_location.destination:
                self.db.last_room = source_location
        if self.location:  # Things to do after the character moved somewhere
            self.db.pose = self.db.pose_default  # Reset room pose when moving to new location
            if self.location.access(self, 'view'):  # No need to look if moving into Nothingness, locked from looking
                if not self.db.settings or self.db.settings.get('look arrive', default=True):
                    self.msg(text=((self.at_look(self.location),), {'window': 'room'}))
            if source_location and self.db.followers and len(self.db.followers) > 0 and self.ndb.exit_used:
                for each in source_location.contents:
                    if not each.has_player or each not in self.db.followers or not self.access(each, 'view'):
                        continue  # no player, not on follow list, or can't see character to follow, then do not follow
                    # About to follow - check if follower is riding something:
                    riding = False
                    for thing in source_location.contents:
                        if thing == each or not thing.db.riders or each not in thing.db.riders:
                            continue
                        riding = True
                    if not riding:
                        print('<%s> %s' % (each, self.ndb.exit_used))
                        each.execute_cmd(self.ndb.exit_used)
        return source_location

    def announce_move_from(self, destination):
        """
        Called if the move is to be announced. This is
        called while we are still standing in the old
        location.
        Args:
            destination (Object): The place we are going to.
        """
        here = self.location
        if not here:
            return
        direction_name = (' |lc%s|lt|530%s|n|le' % (self.ndb.moving_to,
                                                    self.ndb.moving_to)) if self.ndb.moving_to else ''
        # TODO - if character leaving is invisible to viewer and all riders are invisible, then no message sent
        # to viewer, otherwise anyone invisible is listed as "Someone"
        for viewer in here.contents:
            if viewer == self:
                continue
            name = self.get_display_name(viewer, color=False)
            loc_name = self.location.get_display_name(viewer)
            dest_name = destination.get_display_name(viewer)
            string = '|r%s' % name
            if self.ndb.riders and len(self.ndb.riders) > 0:  # Plural exit message: Riders
                if len(self.ndb.riders) > 1:
                    string += ', |r' + '%s|n' % '|n, |r'.join(rider.get_display_name(viewer, color=False)
                                                              for rider in self.ndb.riders[:-1])
                string += ' and |r%s|n are ' % self.ndb.riders[-1].get_display_name(viewer, color=False)
            else:  # Singular exit message: no riders
                string += ' is '
            string += "leaving %s, heading%s for %s." % (loc_name, direction_name, dest_name)
            viewer.msg(string)

    def announce_move_to(self, source_location):
        """
        Called after the move if the move was not quiet. At this point
        we are standing in the new location.
        Args:
            source_location (Object): The place we came from
        """
        here = self.location
        if not source_location and self.location.has_player:
            # This was created from nowhere and added to a player's
            # inventory; it's probably the result of a create command.
            string = "You now have %s in your possession." % (self.get_display_name(here))
            here.msg(string)
            return
        direction_name = ('|lc%s|lt|530%s|n|le' % (self.ndb.moving_from,
                                                   self.ndb.moving_from)) if self.ndb.moving_from else ''
        for viewer in here.contents:
            if viewer == self:
                continue
            src_name = '|222Nothingness'
            if source_location:
                src_name = source_location.get_display_name(viewer)
            string = '|g%s' % self.get_display_name(viewer, color=False)
            if here:
                depart_name = here.get_display_name(viewer)
            else:
                depart_name = '|222Nothingness'
            if self.ndb.riders and len(self.ndb.riders) > 0:
                if len(self.ndb.riders) > 1:
                    string += ', |g' + '%s' % '|n, |g'.join(rider.get_display_name(viewer, color=False)
                                                            for rider in self.ndb.riders[:-1])
                    string += "|n and |g%s|n arrive " % self.ndb.riders[-1].get_display_name(viewer, color=False)
                else:
                    string += ' and |g%s|n arrive ' % self.ndb.riders[-1].get_display_name(viewer, color=False)
            else:
                string += ' arrives '
            if direction_name:
                string += "to %s|n from the %s from %s|n." % (depart_name, direction_name, src_name)
            else:
                string += "to %s|n from %s|n." % (depart_name, src_name)
            viewer.msg(string)
        if self.ndb.riders and len(self.ndb.riders) > 0:
            for each in self.ndb.riders:
                success = each.move_to(here, quiet=True, emit_to_obj=None, use_destination=False,
                                       to_none=False, move_hooks=False)
                # If moved to grid room, write location onto character here
                # If moved from grid room, save old location for possible return
                each.ndb.grid_loc, last = self.ndb.grid_loc, each.ndb.grid_loc
                if not success:
                    self.msg('|r%s|n did not arrive.' % each.get_display_name(self, color=False))
                    # If failed move to grid room, re-write location, last location used for going back.
                    if last:
                        self.ndb.grid_loc = last
                    each.nattributes.remove('mover')
                    self.ndb.riders.remove(each)
                    continue
            for each in self.ndb.riders:
                here.at_object_receive(each, source_location)
                each.at_after_move(source_location)
                each.nattributes.remove('mover')
            self.nattributes.remove('riders')
        if self.db.settings and not self.db.settings.get('look arrive', default=True):
            awake = (con for con in self.location.contents if con != self
                     and con.has_player and con.access(self, 'view'))
            awake_list = ", ".join(a.get_display_name(self, mxp='sense %s' % a.get_display_name(
                self, plain=True), pose=True) for a in awake)
            awake_list = (' Awake here: ' + awake_list) if len(awake_list) > 0 else ''
            self.msg('|/|gArriving at %s.%s'
                     % (self.location.get_display_name(self, mxp='look here'), awake_list.replace('.,', ';')))
        self.nattributes.remove('moving_to')
        self.nattributes.remove('moving_from')

    def at_post_puppet(self):
        """
        Called just after puppeting has been completed and all
        Player<->Object links have been established.
        """
        # Inside your Command func(), use self.msg() or caller.msg(..., session=self.session)
        # That will go only to the session actually triggering the command. You can then do player.sessions.all()
        # and send to all but the current session.
        # There is no way to know that unless the session sends themself as an argument to said method.
        # The session has to be in an argument to that method, like you said.
        # I see that the session is indeed available in the puppet_object method (which calls at_post_puppet)
        # so I suppose we could extend that hook with a session argument.
        # I think it may have originally been defined at a time when an object only ever had one session,
        # so once you were puppeted you could easily retrieve it.

        self.msg('\nYou assume the role of %s.\n' % self.get_display_name(self, pose=self.location is not None))
        if self.location:
            self.msg(self.at_look(self.location))
        if self.ndb.new_mail:
            self.msg('\nYou have new mail in your %s mailbox.\n' % self.home.get_display_name(self))

        def message(obj, from_obj):
            text = 'fades into view' if self.location != self.home else 'awakens'
            obj.msg("|g%s|n %s." % (self.get_display_name(obj, color=False), text), from_obj=from_obj)

        self.location.for_contents(message, exclude=[self], from_obj=self)

    def at_post_unpuppet(self, player, session=None):
        """
        Store characters in Nothingness when the player goes ooc/logs off,
        when characters are left in a room that is not home. Otherwise
        character objects remain in the room after players leave.
        Args:
            player (Player): The player object that just disconnected
                from this object.
            session (Session): Session controlling the connection that
                just disconnected.
        """
        if self.location:
            # reason = ['Idle Timeout', 'QUIT', 'BOOTED', 'Lost Connection']  # TODO
            at_home = self.location == self.home

            def message(obj, from_obj):
                text = 'sleeps' if at_home else 'fades from view'
                obj.msg('|r%s|n %s.' % (self.get_display_name(obj, color=False), text), from_obj=from_obj)

            self.location.for_contents(message, exclude=[self], from_obj=self)
            self.db.prelogout_location = self.location

            if not (at_home or self.has_player):  # if no sessions control it anymore, and its not home...
                self.location = None  # store in Nothingness.

    def process_sdesc(self, sdesc, obj, **kwargs):
        """
        Allows to customize how your sdesc is displayed (primarily by changing colors).
        Args:
            sdesc (str): The sdesc to display.
            obj (Object): The object to which the adjoining sdesc
                belongs (can be yourself).

        Returns:
            sdesc (str): The processed sdesc ready
                for display.
        """
        if self.check_permstring('Mages'):
            return '%s%s|n [|[G%s|n]' % (obj.STYLE, sdesc, obj.key)
        else:
            return '%s%s|n' % (obj.STYLE, sdesc)

    def process_recog(self, recog, obj, **kwargs):
        """
        Allows to customize how a recog string is displayed.
        Args:
            recog (str): The recog string. It has already been
                translated from the original sdesc at this point.
            obj (Object): The object the recog:ed string belongs to.
                This is not used by default.
        Returns:
            recog (str): The modified recog string.
        """
        return self.process_sdesc(recog, obj)

    def get_pronoun(self, regex_match):
        """
        Get pronoun from the pronoun marker in the text. This is used as
        the callable for the re.sub function.
        Args:
            regex_match (MatchObject): the regular expression match.
        Notes:
            - `|s`, `|S`: Subjective form: he, she, it, He, She, It
            - `|o`, `|O`: Objective form: him, her, it, Him, Her, It
            - `|p`, `|P`: Possessive form: his, her, its, His, Her, Its
            - `|a`, `|A`: Absolute Possessive form: his, hers, its, His, Hers, Its
        """

        _GENDER_PRONOUN_MAP = {'male': {'s': 'he', 'o': 'him', 'p': 'his', 'a': 'his'},
                               'female': {'s': 'she', 'o': 'her', 'p': 'her', 'a': 'hers'},
                               'neutral': {'s': 'it',  'o': 'it', 'p': 'its', 'a': 'its'}}

        # _RE_GENDER_PRONOUN = re.compile(r'[^\|]+(\|s|S|o|O|p|P|a|A)')

        typ = regex_match.group()[2]  # "s", "O" etc
        gender = self.attributes.get('gender', default='neutral')
        gender = gender if gender in ('male', 'female', 'neutral') else 'neutral'
        pronoun = _GENDER_PRONOUN_MAP[gender][typ.lower()]
        return pronoun.capitalize() if typ.isupper() else pronoun

    def get_mass(self):
        mass = self.traits.mass.actual if self.traits.mass else 0
        return reduce(lambda x, y: x+y.get_mass() if hasattr(y, 'get_mass') else 0, [mass] + self.contents)

    def get_carry_limit(self):
        return 80 * self.traits.health.actual

    def return_appearance(self, viewer):
        """This formats a description. It is the hook a 'look' command should call.
        Args:
            viewer (Object): Object doing the looking.
        """
        if not viewer:
            return
        if not viewer.is_typeclass('typeclasses.players.Player'):
            viewer = viewer.player  # make viewer reference the player object
        char = viewer.puppet
        # get and identify all objects
        visible = (con for con in self.contents if con != viewer and
                   con.access(viewer, 'view'))
        exits, users, things = [], [], []
        for con in visible:
            if con.destination:
                exits.append(con)
            elif con.has_player:
                users.append(con)
            else:
                things.append(con)
        string = "\n%s" % self.get_display_name(viewer, mxp='sense %s' % self.get_display_name(viewer, plain=True))
        if self.location.tags.get('rp', category='flags'):
            string += ' %s' % self.attributes.get('pose') or ''
        if self.traits.mass and self.traits.mass.actual > 0:
            string += " |y(%s)|n " % mass_unit(self.get_mass())
        if self.traits.health:  # Add character health bar if character has health.
            gradient = ["|[300", "|[300", "|[310", "|[320", "|[330", "|[230", "|[130", "|[030", "|[030"]
            health = make_bar(self.traits.health.actual, self.traits.health.max, 20, gradient)
            string += " %s\n" % health
        else:
            string += "\n"
        desc = self.db.desc
        desc_brief = self.db.desc_brief
        if desc:
            string += "%s" % desc
        elif desc_brief:
            string += "%s" % desc_brief
        else:
            string += 'A shimmering illusion shifts from form to form.'
        if exits:
            string += "\n|wExits: " + ", ".join("%s" % e.get_display_name(viewer) for e in exits)
        if users or things:
            user_list = ", ".join(u.get_display_name(viewer) for u in users)
            ut_joiner = ', ' if users and things else ''
            item_list = ", ".join(t.get_display_name(viewer) for t in things)
            string += "\n|wYou see:|n " + user_list + ut_joiner + item_list
        if self != char:
            if not (self.db.settings and 'look notify' in self.db.settings
                    and self.db.settings['look notify'] is False):
                self.msg("%s just looked at you." % char.get_display_name(self))
        return string

    def return_detail(self, detailkey):
        """
        This looks for an Attribute "obj_details" and possibly
        returns the value of it.

        Args:
            detailkey (str): The detail being looked at. This is
                case-insensitive.
        """
        details = self.db.details
        if details:
            return details.get(detailkey.lower(), None)

    def set_detail(self, detailkey, description):
        """
        This sets a new detail, using an Attribute "details".

        Args:
            detailkey (str): The detail identifier to add (for
                aliases you need to add multiple keys to the
                same description). Case-insensitive.
            description (str): The text to return when looking
                at the given detailkey.
        """
        if self.db.details:
            self.db.details[detailkey.lower()] = description
        else:
            self.db.details = {detailkey.lower(): description}

    def follow(self, caller):
        """Set following agreement - caller follows character"""
        if self == caller:
            self.msg('You decide to follow your heart.')
            return
        action = 'follow'
        if self.attributes.has('followers') and self.db.followers:
            if caller in self.db.followers:
                self.db.followers.remove(caller)
                action = 'stop following'
            else:
                self.db.followers.append(caller)
        else:
            self.db.followers = [caller]
        color = 'g' if action == 'follow' else 'r'
        caller.location.msg_contents('|%s%s|n decides to %s {follower}.'
                                     % (color, caller.key, action), from_obj=caller, mapping=dict(follower=self))

    def mount(self, caller):
        """Set riding agreement - caller rides character"""
        if self == caller:
            return
        action = 'ride'
        if self.attributes.has('riders') and self.db.riders:
            if caller in self.db.riders:
                self.db.riders.remove(caller)
                action = 'stop riding'
            else:
                self.db.riders.append(caller)
        else:
            self.db.riders = [caller]
        # caller is/was riding self invalidate caller riding anyone else in the room.
        for each in caller.location.contents:
            if each == caller or each == self or not each.db.riders or caller not in each.db.riders:
                continue
            each.db.riders.remove(caller)
        color = 'g' if action == 'ride' else 'r'
        caller.location.msg_contents('|%s%s|n decides to %s {mount}.'
                                     % (color, caller.key, action), from_obj=caller, mapping=dict(mount=self))


class NPC(Character):
    """Uses Character class as a starting point."""
    STYLE = '|m'

    def at_object_creation(self):
        """Initialize a newly-created NPC"""
        super(Character, self).at_object_creation()
        self.cmdset.add('commands.battle.BattleCmdSet', permanent=True)

    def at_post_puppet(self):
        """
        Called just after puppeting has been completed and all
        Player<->Object links have been established.
        """
        self.msg("\nYou assume the role of %s.\n" % self.get_display_name(self))
        self.msg(self.at_look(self.location))
        if self.ndb.new_mail:
            self.msg('|/You have new mail in your %s mailbox.|/' % self.home.get_display_name(self))

        def message(obj, from_obj):
            if self.sessions.count() > 1:  # Show as pose if NPC already has a player.
                obj.msg("%s looks more awake." % self.get_display_name(obj), from_obj=from_obj)
            else:
                obj.msg("|g%s|n awakens." % self.get_display_name(obj, color=False), from_obj=from_obj)

        self.location.for_contents(message, exclude=[self], from_obj=self)

    def at_post_unpuppet(self, player, session=None):
        """
        We store the character when the player goes ooc/logs off,
        when the character is left in a public or semi-public room.
        Otherwise the character object will remain in the room after
        the player logged off ("headless", so to say).
        Args:
            player (Player): The player object that just disconnected
                from this object.
            session (Session): Session controlling the connection that
                just disconnected.
        """
        if self.location:

            def message(obj, from_obj):
                if self.has_player:  # Show as pose if NPC still has a player.
                    obj.msg("%s looks sleepier." % (self.get_display_name(obj)), from_obj=from_obj)
                else:  # Show as gone if NPC has no player now.
                    obj.msg("|r%s|n sleeps." % self.get_display_name(obj, color=False), from_obj=from_obj)

            self.location.for_contents(message, exclude=[self], from_obj=self)
            self.db.prelogout_location = self.location
