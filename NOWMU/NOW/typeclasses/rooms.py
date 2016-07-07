"""
Room

Rooms are simple containers that have no location of their own.

"""

import random
from evennia import DefaultRoom
from evennia import TICKER_HANDLER
from evennia.comms.models import ChannelDB, Msg
from evennia.comms.channelhandler import CHANNELHANDLER

from evennia.utils import lazy_property

from traits import TraitHandler
from effects import EffectHandler

from evennia import CmdSet # For the class Grid
from evennia import default_cmds  # For the class Grid's commands


class Room(DefaultRoom):
    """
    Rooms are like any Object, except their location is None
    (which is default). They also use basetype_setup() to
    add locks so they cannot be puppeted or picked up.
    (to change that, use at_object_creation instead)

    See examples/object.py for a list of
    properties and methods available on all Objects.
    """
    STYLE = '|y'

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

    def get_display_name(self, looker, **kwargs):
        """Displays the name of the object in a viewer-aware manner."""
        if self.locks.check_lockstring(looker, "perm(Builders)"):
            return "%s%s|w(#%s)|n" % (self.STYLE, self.name, self.id)
        else:
            return "%s%s|n" % (self.STYLE, self.name)

    def mxp_name(self, viewer, command):
        """Returns the full styled and clickable-look name for the viewer's perspective as a string."""
        return "|lc%s|lt%s|le" % (command, self.get_display_name(viewer)) if viewer and \
            self.access(viewer, 'view') else ''

    def return_appearance(self, viewer):
        """
        This formats a description. It is the hook a 'look' command
        should call.

        Args:
            viewer (Object): Object doing the looking.
        """
        if not viewer:
            return
        # get and identify all objects
        visible = (con for con in self.contents if con != viewer and con.access(viewer, 'view'))
        exits, ways, users, things = [], [], [], []

        way_dir = {'ne': 'northeast', 'n': 'north', 'nw': 'northwest', 'e': 'east',
                   'se': 'southeast', 's': 'south', 'sw': 'southwest', 'w': 'west'}

        default_exits = [u'north', u'south', u'east', u'west', u'northeast', u'northwest', u'southeast', u'southwest',
                         u'up', u'down', u'in', u'out']

        exits_simple, exits_complex = [], []

        def sort_exits(x, y):
            """sort supplied list of exit strings, based on default_exits, returns sorted list."""
            matches = []  # start empty and build a sorted list
            for j in default_exits:
                for i, easy in enumerate(x):
                    if j == easy:
                        matches.append(y[i])
            s = set(matches)  # Set magic for adding back non-matches.
            return matches + [z for z in y if z not in s]

        for con in visible:
            if con.destination:
                exits.append(con)
            elif con.has_player:
                users.append(con)
            else:
                things.append(con)
        # get description, build string
        command = '%s #%s' % ('sense', self.id)
        string = "\n%s\n" % self.mxp_name(viewer, command)
        desc = self.db.desc
        desc_brief = self.db.desc_brief
        if desc:
            string += "%s" % desc
        elif desc_brief:
            string += "%s" % desc_brief
        else:
            string += 'Nothing more than smoke and mirrors appears around you.'
        if self.attributes.has('exits'):
            ways = self.db.exits
        if exits or ways:
            string += "\n|wVisible exits|n: "
            for e in exits:
                exits_simple.append(e.name)
                exits_complex.append("%s" % e.mxp_name(viewer, 'sense #%s' % e.id) if hasattr(e, "mxp_name")
                                     else e.get_display_name(viewer))
            if ways and not ways == {}:
                for w in ways:
                    exits_simple.append(way_dir[w])
                    exits_complex.append("|lc%s|lt|530%s|n|le" % (w, way_dir[w]))
            string += ", ".join(d for d in sort_exits(exits_simple, exits_complex))
        elif viewer.db.last_room:
            string += "\n|wVisible exits|n: |lcback|lt|gBack|n|le to %s." % viewer.db.last_room.name
        if users or things:
            user_list = ", ".join(u.mxp_name(viewer, 'sense #%s' % u.id) for u in users)
            ut_joiner = ', ' if users and things else ''
            item_list = ", ".join(t.mxp_name(viewer, 'sense #%s' % t.id) if hasattr(t, "mxp_name")
                                  else t.get_display_name(viewer) for t in things)
            string += "\n|wHere you find:|n " + user_list + ut_joiner + item_list
        return string

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
        string = "%s%s|n is leaving %s%s|n, heading for %s%s|n." % (self.STYLE, name, self.location.STYLE, loc_name,
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
        string = "%s%s|n arrives to %s%s|n from %s%s|n." % (self.STYLE, name, self.location.STYLE, loc_name,
                                                            source_location.STYLE, src_name)
        self.location.msg_contents(string, exclude=self)

# [...] class TutorialRoom(DefaultRoom):

    def at_object_creation(self):
        """Called when room is first created"""
        self.db.desc_brief = "This is a default room."
        # self.cmdset.add_default(TutorialRoomCmdSet) # 
        
    def at_object_receive(self, new_arrival, source_location):
        """
        When an object enters a room we tell other objects in the room
        about it by trying to call a hook on them. The Mob object
        uses this to cheaply get notified of enemies without having
        to constantly scan for them.

        Args:
            new_arrival (Object): the object that just entered this room.
            source_location (Object): the previous location of new_arrival.

        """
        if new_arrival.has_player:  # and not new_arrival.is_superuser: # this is a character
            if self.tags.get('outdoor', category='flags'):
                tickers = TICKER_HANDLER.all_display()
                counter = 0
                for tick in tickers:
                    if tick[0] == self and tick[1] == 'update_weather':
                        notice = ''
                        counter += 1
                        show = '20%% chance every %s seconds in ' % tick[3]
                        show += "%s%s" % (tick[0] or "[None]", tick[0] and " (#%s)" %
                                          (tick[0].id if hasattr(tick[0], "id") else "") or "")
                        if counter > 1:
                            notice = '|rExtra Ticker|n - |yadditional|n '
                            # Too many weather tickers going, maybe remove extra?
                        channel = ChannelDB.objects.channel_search('MudInfo')
                        if channel[0]:
                            channel[0].msg('* %s\'s %s experience * %s%s' % (new_arrival.key, tick[4], notice, show),
                                           keep_log=False)
                if counter == 0:  # No weather ticker - add one.
                    interval = random.randint(50, 70)
                    TICKER_HANDLER.add(interval=interval, callback=self.update_weather, idstring='Weather')

            for obj in self.contents_get(exclude=new_arrival):
                if hasattr(obj, "at_new_arrival"):
                    obj.at_new_arrival(new_arrival)

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

# [...] class WeatherRoom(TutorialRoom):

    # def update_weather(self, *args, **kwargs):
    def update_weather(self):
        """
        Called by the tickerhandler at regular intervals. Even so, we
        only update 20% of the time, picking a random weather message
        when we do. The tickerhandler requires that this hook accepts
        any arguments and keyword arguments (hence the *args, **kwargs
        even though we don't actually use them in this example)
        """

        weather = self.db.weather or (
            "The rain coming down from the iron-grey sky intensifies.",
            "A gust of wind throws the rain right in your face. Despite your cloak you shiver.",
            "The rainfall eases a bit and the sky momentarily brightens.",
            "For a moment it looks like the rain is slowing, then it begins anew with renewed force.",
            "The rain pummels you with large, heavy drops. You hear the rumble of thunder in the distance.",
            "The wind is picking up, howling around you, throwing water droplets in your face. It's cold.",
            "Bright fingers of lightning flash over the sky, moments later followed by a deafening rumble.",
            "It rains so hard you can hardly see your hand in front of you. You'll soon be drenched to the bone.",
            "Lightning strikes in several thundering bolts, striking the trees in the forest to your west.",
            "You hear the distant howl of what sounds like some sort of dog or wolf.",
            "Large clouds rush across the sky, throwing their load of rain over the world.")

        if random.random() < 0.2:  # only update 20 % of the time
            self.msg_contents("|w%s|n" % random.choice(weather))
            # TODO: Weather channel? Send weather messages to a channel.   


class RealmEntry(Room):
    """
    Rooms are like any Object, except their location is None
    (which is default). They also use basetype_setup() to
    add locks so they cannot be puppeted or picked up.
    (to change that, use at_object_creation instead)

    See examples/object.py for a list of
    properties and methods available on all Objects.
    """
    STYLE = '|242'

    def at_object_creation(self):
        """Called when the room is first created."""
        super(Room, self).at_object_creation()
        self.db.info = "The first room of the realm. This assigns the realm-specific attributes to the character."

    def at_object_receive(self, character, source_location):
        """Assign properties on characters"""

        if character.is_superuser:
            string = "-" * 78 +\
                     "|/WARNING: You are playing while superuser. Use the {quell} command|/" \
                     " to play without superuser privileges (many functions and locks are bypassed|/" \
                     " by default by the presence of a superuser, making this mode really only useful|/" \
                     " for exploring things behind the scenes later or entering to make modifications).|/"\
                     + "-" * 78
            character.msg("|r%s|n" % string.format(quell="|w@quell|r"))
        else:  # setup character for the particular realm:
            # Load attributes needed into a dictionary then set the attributes on the character as needed.
            health = self.db.char_health or 20
            if character.has_player:
                character.db.health = health
                character.db.health_max = health


class CmdSetGridRoom(CmdSet):
        """This method adds commands to the grid room command set."""
        key = 'Grid Nav'
        priority = 101  # Same as Exit objects

        def at_cmdset_creation(self):
            self.add(CmdGrid())
            self.add(CmdGridNorth())
            self.add(CmdGridSouth())
            self.add(CmdGridEast())
            self.add(CmdGridWest())
            self.add(CmdGridNortheast())
            self.add(CmdGridNorthwest())
            self.add(CmdGridSoutheast())
            self.add(CmdGridSouthwest())


class CmdGridMotion(default_cmds.MuxCommand):
    """
    Parent class for all simple exit-directions. 
    Actual exit objects superseded these in every way.

    Grid locations are stored on the Grid room that is navigated by these commands.
    Usage:
    """
    arg_regex = r'^/|\s|$'
    auto_help = True
    help_category = 'Travel'
    player_caller = True

    def func(self):
        """Command for all simple exit directions."""
        you = self.character
        session = self.session
        loc = you.location

        loc.msg_contents("%s chooses to go |g%s|n on the grid." % (you.get_display_name(session), self.key))
        you.msg(loc.return_appearance(you))  # Show view from location.

    def motion(self, position):
        """Update character's position in room where position is [x, y]"""
        direction = self.key
        x_motion, y_motion = [0, 0]
        if 'north' in direction:
            y_motion = -1
        if 'east' in direction:
            x_motion = 1
        if 'west' in direction:
            x_motion = -1
        if 'south' in direction:
            y_motion = 1
        x_pos, y_pos = position
        return map(lambda x, y: x + y, [x_pos, y_pos], [x_motion, y_motion])


class CmdGrid(CmdGridMotion):
    """
    grid  -- manage the room's grid.
    Usage:
      grid
    Switches:
    /exits   Show exits of the room affected by grid motion commands.
    /size <[xmin..xmax, ymin..ymax]>   Show or edit the current working grid size of the room.
    /base <[x, y]>                     Show or edit the base (center) of the grid in the room.
    /current <[x, y]>                  Show or edit the current working location in the room.
    /large                             Show a large grid to represent the grid room layout.
    /small                             Show a small grid to represent the grid room layout.
    """
    key = 'grid'
    help_category = 'Building'
    locks = 'cmd:perm(Builders)'
    player_caller = True

    def func(self):
        """Command to manage all grid room properties."""
        you = self.character
        session = self.session
        loc = you.location

        loc.msg_contents("%s examines %s." % (you.get_display_name(session), loc.get_display_name(session)))
        x, y = (loc.grid.x, loc.grid.y)
        if 'exits' in self.switches:
            exits = []
            for e in loc.exits:
                short_name = str(e.key)
                # loc.grid.exits.short_name = [0,0]
                exits.append([e, short_name])
            you.msg("Exits: %s" % exits)
        if 'size' in self.switches:
            if not self.args:
                you.msg("Room: %sx%s as [%s..%s, %s..%s] Current editing position: [%s, %s]" %
                        (x.max-x.min+1, y.max-y.min+1, x.min, x.max, y.min, y.max, x.current, y.current))
            else:
                x_y = self.args.split(',')
                xr, yr = x_y[0], x_y[1] if len(x_y) > 1 else [x_y[0], x_y[0]]
                xmin, xmax = xr.split('..') if len(xr.split('..')) > 1 else [xr, xr+1]
                ymin, ymax = yr.split('..') if len(yr.split('..')) > 1 else [yr, yr+1]
                xmin, xmax, ymin, ymax = [int(xmin), int(xmax), int(ymin), int(ymax)]
                if xmax-xmin < 99 and ymax-ymin < 99 and xmin <= x.base <= xmax and ymin <= y.base <= ymax:
                    you.msg("Room: %sx%s as [%s..%s, %s..%s]" %
                            (xmax-xmin+1, ymax-ymin+1, xmin, xmax, ymin, ymax))
                    x.min, x.max, y.min, y.max = [xmin, xmax, ymin, ymax]
                else:
                    range_error = "[x0..x1, y0..y1] ranges must be at least 1 and at most 100."
                    base_error = "Base values [%s, %s] must be within [x0..x1, y0..y1]." \
                                 "|/Change ranges, or change base values." % (x.base, y.base)
                    you.msg(base_error if xmax-xmin < 99 and ymax-ymin < 99 else range_error)
            return
        if 'base' in self.switches:
            x_y = self.args.split(',')
            xbase, ybase = int(x_y[0]), int(x_y[1]) if len(x_y) > 1 else [0, 0]
            if x.min <= xbase <= x.max and y.min <= ybase <= y.max:
                x.base, y.base = [xbase, ybase]
                you.msg("|gRoom base set|n to [%s, %s] within %sx%s area [%s..%s, %s..%s]" %
                        (x.base, y.base, x.max-x.min+1, y.max-y.min+1, x.min, x.max, y.min, y.max))
            else:
                you.msg("|rRoom base must be within %sx%s area|n [%s..%s, %s..%s]" %
                        (x.max-x.min+1, y.max-y.min+1, x.min, x.max, y.min, y.max))
        if 'current' in self.switches:
            x_y = self.args.split(',')
            xcurr, ycurr = int(x_y[0]), int(x_y[1]) if len(x_y) > 1 else [0, 0]
            if x.min <= xcurr <= x.max and y.min <= ycurr <= y.max:
                x.current, y.current = [xcurr, ycurr]
                you.msg("|gRoom current edit location set|n to [%s, %s] within %sx%s area [%s..%s, %s..%s]" %
                        (x.current, y.current, x.max-x.min+1, y.max-y.min+1, x.min, x.max, y.min, y.max))
            else:
                you.msg("|rRoom current edit location must be within %sx%s area|n [%s..%s, %s..%s]" %
                        (x.max-x.min+1, y.max-y.min+1, x.min, x.max, y.min, y.max))
        small = True if 'small' in self.switches else False
        if small or 'large' in self.switches:
            intro = 'Small' if small else 'Large'
            you.msg('%s grid display of room:|/' % intro)
            for i in range(x.min, x.max+1):
                line = ''
                if small:
                    for j in range(y.min, y.max+1):
                        line += ' x ' if x.base == i and y.base == j else ' . '
                    you.msg("%s|/" % line)
                else:
                    for k in range(0, 2):
                        for j in range(y.min, y.max+1):
                            if k == 0:
                                line += '[ _ ] ' if x.base == i and y.base == j else '[   ] '
                            else:
                                line += '[___] ' if x.base == i and y.base == j else '[___] '
                        line += '|/'
                    you.msg("%s" % line)
        you.msg("Room: %sx%s as [%s..%s, %s..%s]|/Base editing position: [%s, %s]|/Current editing position: [%s, %s]" %
                (x.max-x.min+1, y.max-y.min+1, x.min, x.max, y.min, y.max, x.base, y.base, x.current, y.current))


class CmdGridNorth(CmdGridMotion):
    __doc__ = CmdGridMotion.__doc__ + "north  or n        -- move north on the room's grid."
    key = 'north'
    aliases = 'n'
    locks = 'cmd:not on_exit(n)'


class CmdGridNortheast(CmdGridMotion):
    __doc__ = CmdGridMotion.__doc__ + "northeast  or ne   -- move northeast on the room's grid."
    key = 'northeast'
    aliases = 'ne'
    locks = 'cmd:not on_exit(ne)'


class CmdGridNorthwest(CmdGridMotion):
    __doc__ = CmdGridMotion.__doc__ + "northwest  or nw   -- move northwest on the room's grid."
    key = 'northwest'
    aliases = 'nw'
    locks = 'cmd:not on_exit(nw)'


class CmdGridEast(CmdGridMotion):
    __doc__ = CmdGridMotion.__doc__ + "east  or e         -- move east on the room's grid."
    key = 'east'
    aliases = 'e'
    locks = 'cmd:not on_exit(e)'


class CmdGridSouth(CmdGridMotion):
    __doc__ = CmdGridMotion.__doc__ + "south  or s        -- move south on the room's grid."
    key = 'south'
    aliases = 's'
    locks = 'cmd:not on_exit(s)'


class CmdGridSoutheast(CmdGridMotion):
    __doc__ = CmdGridMotion.__doc__ + "sortheast  or se   -- move southeast on the room's grid."
    key = 'southeast'
    aliases = 'se'
    locks = 'cmd:not on_exit(se)'


class CmdGridSouthwest(CmdGridMotion):
    __doc__ = CmdGridMotion.__doc__ + "southwest  or sw   -- move southwest on the room's grid."
    key = 'southwest'
    aliases = 'sw'
    locks = 'cmd:not on_exit(sw)'


class CmdGridWest(CmdGridMotion):
    __doc__ = CmdGridMotion.__doc__ + "west  or w         -- move west on the room's grid."
    key = 'west'
    aliases = 'w'
    locks = 'cmd:not on_exit(w)'


class Grid(Room):
    """
    Grid Rooms are like any Room, except they have sub locations within
    by default. Objects dropped here are associated with a specific 
    location prevending them from being picked up unless the character
    is next to them.
    """
    STYLE = '|204'

    @lazy_property
    def grid(self):
        return TraitHandler(self, db_attribute='grid')

    def at_object_creation(self):
        """called when the object is first created"""
        self.cmdset.add_default(CmdSetGridRoom)
        self.db.grid = {'x': {'name': 'East/West size', 'type': 'counter', 'base': 0, 'current': 0,
                              'min': 0, 'max': 1}, 'y': {'name': 'North/South size', 'type': 'counter', 'base': 0,
                                                         'current': 0, 'min': 0, 'max': 1}}
