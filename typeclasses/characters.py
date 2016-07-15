"""
Characters

Characters are (by default) Objects setup to be puppeted by Players.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""
import re
from world.helpers import make_bar, mass_unit
from evennia import DefaultCharacter

from evennia.utils import lazy_property

from traits import TraitHandler
from effects import EffectHandler


class Character(DefaultCharacter):
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

    # @lazy_property
    # def equipment(self):
    #     return EquipmentHandler(self)

    def at_before_move(self, destination):
        """
        Called just before moving object - here we check to see if
        it is supporting another object that is currently in the room
        before allowing the move. If it is, we do prevent the move by
        returning False.
        """
        if destination == self.location:
            return False
        if self.db.locked:
            self.msg("\nYou're still sitting.")  # stance, prep, obj
            return False  # Object is supporting something; do not move it
        elif self.attributes.has('health') and self.db.health <= 0:
            self.msg("You can't move; you're incapacitated!")  # Type 'home' to TODO:
            # go back home and recover, or wait for a healer to come to you.")
            return False
        if self.db.Combat_TurnHandler:
            self.caller.msg("You can't leave while engaged in combat!")
            return False
        # if self.db.HP <= 0:
        #    self.caller.msg("You can't move, you've been defeated! Type 'return' to return home and recover!")
        #    return False
        return True

    def at_after_move(self, source_location):
        """Trigger look after a move."""
        if self.location.access(self, 'view'):
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
        if not self.location:
            return
        name = self.name
        loc_name = self.location.name
        dest_name = destination.name
        string = "|r%s|n is leaving %s%s|n, heading for %s%s|n." % (name, self.location.STYLE, loc_name,
                                                                    destination.STYLE, dest_name)
        self.location.msg_contents(string, exclude=self)

    def announce_move_to(self, source_location):
        """
        Called after the move if the move was not quiet. At this point
        we are standing in the new location.
        Args:
            source_location (Object): The place we came from
        """
        name = self.name
        if not source_location and self.location.has_player:
            # This was created from nowhere and added to a player's
            # inventory; it's probably the result of a create command.
            string = "You now have %s%s|n in your possession." % (self.STYLE, name)
            self.location.msg(string)
            return
        src_name = "nowhere"
        loc_name = self.location.name
        if source_location:
            src_name = source_location.name
        string = "|g%s|n arrives to %s%s|n from %s%s|n." % (name, self.location.STYLE, loc_name,
                                                            source_location.STYLE, src_name)
        self.location.msg_contents(string, exclude=self)

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

        def message(obj, from_obj):
            obj.msg("|g%s|n fades into view." % self.get_display_name(obj), from_obj=from_obj)
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
        if not self.sessions.count():
            # only remove this char from grid if no sessions control it anymore.
            if self.location:

                def message(obj, from_obj):
                    obj.msg("|r%s|n sleeps." % self.key, from_obj=from_obj)
                self.location.for_contents(message, exclude=[self], from_obj=self)
                self.db.prelogout_location = self.location
                self.location = None

                def message(obj, from_obj):
                    obj.msg("%s fades from view." % self.get_display_name(obj), from_obj=from_obj)
                self.db.prelogout_location.for_contents(message, exclude=[self], from_obj=self)

    def get_display_name(self, looker, **kwargs):
        """Displays the name of the object in a viewer-aware manner."""
        if self.locks.check_lockstring(looker, "perm(Builders)"):
            return "%s%s|w(#%s)|n" % (self.STYLE, self.name, self.id)
        else:
            return "%s%s|n" % (self.STYLE, self.name)

    def mxp_name(self, viewer, command):
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
        # get description, build string

        string = "\n%s" % self.mxp_name(viewer, '@verb #%s' % self.id)
        string += " |y(%s)|n " % mass_unit(self.get_mass())
        if self.attributes.has('health') and self.attributes.has('health_max'):  # Add character health bar.
            gradient = ["|[300", "|[300", "|[310", "|[320", "|[330", "|[230", "|[130", "|[030", "|[030"]
            health = make_bar(self.attributes.get('health'), self.attributes.get('health_max'), 20, gradient)
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
            self.msg("|g%s|n just looked at you." % viewer.key)
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


class NPC(Character):
    """Uses Character class as a starting point."""
    STYLE = '|m'

    def at_object_creation(self):
        """Initialize a newly-created NPC"""
        super(Character, self).at_object_creation()
        self.cmdset.add('commands.battle.BattleCmdSet', permanent=True)

    def at_post_puppet(self):  # TODO: Fix this for multi-puppeteers.
        """
        Called just after puppeting has been completed and all
        Player<->Object links have been established.
        """
        self.msg("\nYou assume the role of %s.\n" % self.get_display_name(self))
        self.msg(self.at_look(self.location))

#    Testing Trait system
        # self.traits.add('health', 'Health', type='gauge', base=20, min=0, max=20)
        # print(self.traits.health.current)

        if not self.traits.mass:
            mass = 10 if not self.db.mass else self.db.mass
            self.traits.add('mass', 'Mass', type='static', base=mass)
            print(self.traits.mass.current)

        if not self.traits.stat_atm:
            self.traits.add('stat_atm', 'Melee Attack', type='gauge', base=6, min=0, max=10)
        if not self.traits.stat_atr:
            self.traits.add('atr', 'Ranged Attack', type='gauge', base=6, min=0, max=10)
        if not self.traits.stat_def:
            self.traits.add('stat_def', 'Defense', type='gauge', base=6, min=0, max=10)
        if not self.traits.stat_vit:
            self.traits.add('stat_vit', 'Vitality', type='gauge', base=6, min=0, max=10)
        if not self.traits.stat_mob:
            self.traits.add('stat_mob', 'Mobility', type='gauge', base=6, min=0, max=10)
        if not self.traits.stat_spe:
            self.traits.add('stat_spe', 'Special', type='gauge', base=6, min=0, max=10)

        # def message(obj, from_obj):
        #    obj.msg("|g%s|n fades into view." % self.get_display_name(obj), from_obj=from_obj)
        # self.location.for_contents(message, exclude=[self], from_obj=self)

        def message(obj, from_obj):
            obj.msg("%s%s|n awakens." % (self.STYLE, self.get_display_name(obj)), from_obj=from_obj)
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
        if not self.sessions.count():
            # only remove this char from grid if no sessions control it anymore.
            if self.location:
                def message(obj, from_obj):
                    obj.msg("%s%s|n sleeps." % (self.STYLE, self.get_display_name(obj)), from_obj=from_obj)
                self.location.for_contents(message, exclude=[self], from_obj=self)
                self.db.prelogout_location = self.location
                # self.location = None  # TODO: Send NPC home after unpuppeting?
                # def message(obj, from_obj):
                #     obj.msg("|r%s|n fades from view." % self.get_display_name(obj), from_obj=from_obj)
                # self.db.prelogout_location.for_contents(message, exclude=[self], from_obj=self)
