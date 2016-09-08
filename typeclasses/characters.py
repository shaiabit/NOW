"""
Characters

Characters are (by default) Objects setup to be puppeted by Players.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""
from world.helpers import make_bar, mass_unit
from world.rpsystem import RPCharacter

from evennia.utils import lazy_property

from traits import TraitHandler
from effects import EffectHandler


class Character(RPCharacter):
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

    @lazy_property
    def traits(self):
        return TraitHandler(self)

    @lazy_property
    def skills(self):
        return TraitHandler(self, db_attribute='skills')

    @lazy_property
    def effects(self):
        return EffectHandler(self)

    def at_before_move(self, destination):
        """
        Called just before moving object - here we check to see if
        it is supporting another object that is currently in the room
        before allowing the move. If it is, we do prevent the move by
        returning False.
        """
        if destination == self.location:  # Prevent move into same room character is already in.
            return False
        if self.db.locked:  # Prevent leaving a room while still sitting.
            self.msg("\nYou're still sitting.")  # stance, prep, obj
            return False  # Object is supporting something; do not move it
        elif self.attributes.has('health') and self.db.health <= 0:  # Prevent move while incapacitated.
            self.msg("You can't move; you're incapacitated!")  # Type 'home' to TODO:
            # go back home and recover, or wait for a healer to come to you.")
            return False
        if self.db.Combat_TurnHandler:  # Prevent move while in combat.
            self.caller.msg("You can't leave while engaged in combat!")
            return False
        if self.nattributes.has('mover'):  # Allow move when being moved by something.
            return True
        if self.attributes.has('followers') and self.db.followers and self.location:  # Test list of followers.
            self.ndb.followers = []
            if self.db.settings and 'lead others' in self.db.settings and self.db.settings['lead others'] is False:
                return True  # Character has followers, but does not want to lead others.
            for each in self.db.followers:
                if each.location == self.location:
                    each.ndb.mover = self
                    if not (each.has_player and each.at_before_move(destination)):
                        continue
                    if each.db.settings and 'follow others' in each.db.settings and each.db.settings['follow others']\
                            is False:
                            continue
                    self.ndb.followers.append(each)
                    self.location.at_object_leave(each, destination)
        return True

    def at_after_move(self, source_location):
        """Store last location and room then trigger the arrival look after a move."""
        if source_location:  # Is "None" when moving from Nothingness. If so, do nothing.
            self.ndb.last_location = source_location
            if not source_location.destination:
                self.db.last_room = source_location
        if self.location and self.location.access(self, 'view'):  # No need to look if moving into Nothingness
            self.msg(text=((self.at_look(self.location),), {'window': 'room'}))
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
        for viewer in here.contents:
            if viewer == self:
                continue
            name = self.get_display_name(viewer)
            loc_name = self.location.get_display_name(viewer)
            dest_name = destination.get_display_name(viewer)
            string = '|w(|rLeaving|w) %s' % name
            if self.ndb.followers and len(self.ndb.followers) > 0:
                if len(self.ndb.followers) > 1:
                    string += ', |r' + '%s|n' % '|n, |r'.join(follower.key for follower in self.ndb.followers[:-1])
                    string += ' and |r%s|n are ' % self.ndb.followers[-1].key
                else:
                    string += ' and |r%s|n are ' % self.ndb.followers[-1]
            else:
                string += ' is '
            string += "leaving %s, heading for %s." % (loc_name, dest_name)
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
        for viewer in here.contents:
            if viewer == self:
                continue
            src_name = '|222Nothingness'
            if source_location:
                src_name = source_location.get_display_name(viewer)
            string = '|w(|gArriving|w) %s' % self.get_display_name(viewer)
            if here:
                depart_name = here.get_display_name(viewer)
            else:
                depart_name = '|222Nothingness'
            if self.ndb.followers and len(self.ndb.followers) > 0:
                if len(self.ndb.followers) > 1:
                    string += ', |g' + '%s' % '|n, |g'.join(follower.key for follower in self.ndb.followers[:-1])
                    string += "|n and |g%s|n arrive " % self.ndb.followers[-1].key
                else:
                    string += ' and |g%s|n arrive ' % self.ndb.followers[-1]
            else:
                string += ' arrives '
            string += "to %s|n from %s|n." % (depart_name, src_name)
            viewer.msg(string)
        if self.ndb.followers and len(self.ndb.followers) > 0:
            for each in self.ndb.followers:
                success = each.move_to(here, quiet=True, emit_to_obj=None, use_destination=False,
                                       to_none=False, move_hooks=False)
                if not success:
                    self.msg('%s%s|n did not arrive.' % (each.STYLE, each.key))
                    each.nattributes.remove('mover')
                    self.ndb.followers.remove(each)
                    continue
            for each in self.ndb.followers:
                here.at_object_receive(each, source_location)
                each.at_after_move(source_location)
                each.nattributes.remove('mover')
            self.nattributes.remove('followers')

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
# I think it may have originally been defined at a time when an object only ever had one session, so once you were
        # puppeted you could easily retrieve it.

        self.msg("\nYou assume the role of %s.\n" % self.get_display_name(self))
        self.msg(self.at_look(self.location))
        if self.ndb.new_mail:
            self.msg('|/You have new mail in your %s mailbox.|/' % self.home.get_display_name(self))

        def message(obj, from_obj):
            obj.msg("|g%s|n fades into view." % self.key, from_obj=from_obj)

        if self.location != self.home:
            self.location.for_contents(message, exclude=[self], from_obj=self)

        def message(obj, from_obj):
            obj.msg("|g%s|n awakens." % self.key, from_obj=from_obj)

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
        if not self.sessions.count():  # Only remove this char from grid if no sessions control it anymore.
            if self.location:

                def message(obj, from_obj):
                    obj.msg("|r%s|n sleeps." % self.key, from_obj=from_obj)

                self.location.for_contents(message, exclude=[self], from_obj=self)
                self.db.prelogout_location = self.location
                if self.location != self.home:  # If not already home, send to Nothingness.
                    self.location = None

                def message(obj, from_obj):
                    obj.msg("%s%s|n fades from view." % (self.STYLE, self.key), from_obj=from_obj)

                if self.location != self.home:
                    self.db.prelogout_location.for_contents(message, exclude=[self], from_obj=self)

    def process_sdesc(self, sdesc, obj, **kwargs):
        """
        Allows to customize how your sdesc is displayed
        (primarily by changing colors).

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

    def mxp_name(self, viewer, command, **kwargs):
        """Returns the full styled and clickable-look name for the viewer's perspective as a string."""
        return "|lc%s|lt%s%s|n|le" % (command, self.STYLE, self.get_display_name(viewer)) if viewer and \
            self.access(viewer, 'view') else ''

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
        if not self.traits.mass:
            mass = 10 if not self.db.mass else self.db.mass
            self.traits.add('mass', 'Mass', type='static', base=mass)
            print('Mass for %s(%s) set to %s.' % (self.key, self.id, repr(self.traits.mass)))
        mass = self.traits.mass.actual or 10
        return reduce(lambda x, y: x+y.get_mass() if hasattr(y, 'get_mass') else 0, [mass] + self.contents)

    def get_carry_limit(self):
        return 80 * self.get_attribute_value('health')

    def return_appearance(self, viewer):
        """This formats a description. It is the hook a 'look' command should call.
        Args:
            viewer (Object): Object doing the looking.
        """
        if not viewer:
            return
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
        string = "\n%s" % self.mxp_name(viewer, 'sense %s' % self.get_display_name(viewer))
        if self.location.tags.get('rp', category='flags'):
            string += ' %s' % self.attributes.get('pose') or ''
        string += " |y(%s)|n " % mass_unit(self.get_mass())
        health_attribute_pair = True if self.attributes.has('health') and self.attributes.has('health_max') else False
        health_trait_gauge = True if self.traits.health else False
        if health_attribute_pair or health_trait_gauge:  # Add character health bar if character has health attributes.
            gradient = ["|[300", "|[300", "|[310", "|[320", "|[330", "|[230", "|[130", "|[030", "|[030"]
            if health_trait_gauge:  # FIXME
                pass  # TODO: Trait health gauge goes here.
                health = make_bar(self.traits.health, self.traits.health.max, 20, gradient)
            else:
                health = make_bar(self.attributes.get('health'), self.attributes.get('health_max'), 20, gradient)
                # Write health into traits here.
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
        if self != viewer:
            if not (self.db.settings and 'look notify' in self.db.settings
                    and self.db.settings['look notify'] is False):
                self.msg("%s just looked at you." % viewer.character.get_display_name(self))
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
        """Set following agreement"""
        if self == caller:
            self.msg('You decide to follow your heart.')
            return
        if self.attributes.has('followers') and self.db.followers:
            if caller in self.db.followers:
                caller.msg("You are already following %s%s|n." % (self.STYLE, self.key))
                return
            self.db.followers.append(caller)
        else:
            self.db.followers = [caller]
        msg = "|g%s|n decides to follow %s%s|n." % (caller.key, self.STYLE, self.key)
        caller.location.msg_contents(msg)


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
            self.msg('|/You have new mail in your %s%s|n mailbox.|/' % (self.home.STYLE, self.home.key))

        def message(obj, from_obj):
            if self.sessions.count() > 1:  # Show as pose if NPC already has a player.
                obj.msg("%s awakens." % self.get_display_name(obj), from_obj=from_obj)
            else:
                obj.msg("|g%s|n awakens." % self.key, from_obj=from_obj)

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
                if self.sessions.count():  # Show as pose if NPC still has a player.
                    obj.msg("%s sleeps." % (self.get_display_name(obj)), from_obj=from_obj)
                else:  # Show as gone if NPC has no player now.
                    obj.msg("|r%s|n sleeps." % self.key, from_obj=from_obj)

            self.location.for_contents(message, exclude=[self], from_obj=self)
            self.db.prelogout_location = self.location
