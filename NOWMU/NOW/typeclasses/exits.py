"""
Exits

Exits are connectors between Rooms. An exit always has a destination property
set and has a single command defined on itself with the same name as its key,
for allowing Characters to traverse the exit to its destination.

"""
from evennia import DefaultExit, utils, Command

MOVE_DELAY = {"stroll": 16,
              "walk": 8,
              "run": 4,
              "sprint": 2,
              "scamper": 1}

class Exit(DefaultExit):
    """
    Exits are paths between rooms. Exits are normal Objects except
    they defines the `destination` property. It also does work in the
    following methods:

     basetype_setup() - sets default exit locks (to change, use `at_object_creation` instead).
     at_cmdset_get(**kwargs) - this is called when the cmdset is accessed and should
                              rebuild the Exit cmdset along with a command matching the name
                              of the Exit object. Conventionally, a kwarg `force_init`
                              should force a rebuild of the cmdset, this is triggered
                              by the `@alias` command when aliases are changed.
     at_failed_traverse() - gives a default error message ("You cannot
                            go there") if exit traversal fails and an
                            attribute `err_traverse` is not defined.

    Relevant hooks to overload (compared to other types of Objects):
        at_traverse(traveller, target_loc) - called to do the actual traversal and calling of the other hooks.
                                            If overloading this, consider using super() to use the default
                                            movement implementation (and hook-calling).
        at_after_traverse(traveller, source_loc) - called by at_traverse just after traversing.
        at_failed_traverse(traveller) - called by at_traverse if traversal failed for some reason. Will
                                        not be called if the attribute `err_traverse` is
                                        defined, in which case that will simply be echoed.
    """

    STYLE = '|g'
    STYLE_PATH = '|252'

    def at_desc(self, looker=None):
        """
        This is called whenever looker looks at an exit.
        looker is the object requesting the description.
        Called before return_appearance.
        """
        if not looker.location == self:
            looker.msg("You gaze into the distance.")


    def full_name(self, viewer):
        """
        Returns the full styled and clickable-look name
        for the viewer's perspective as a string.
        """

        if viewer and (self != viewer) and self.access(viewer, "view"):
            style = self.STYLE_PATH if self.db.is_path or False else self.STYLE
            return "%s%s|n" % (style, self.get_display_name(viewer))
        else:
            return ''


    def mxp_name(self, viewer, command):
        """
        Returns the full styled and clickable-look name
        for the viewer's perspective as a string.
        """

        if viewer and self.access(viewer, "view"):
            return "|lc%s|lt%s%s|n|le" % (command, self.STYLE, self.full_name(viewer))
        else:
            return ''


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
        visible = (con for con in self.contents if con != viewer and
                                                    con.access(viewer, "view"))
        exits, users, things = [], [], []
        for con in visible:
            if con.destination:
                exits.append(con)
            elif con.has_player:
                users.append(con)
            else:
                things.append(con)
        # get description, build string
        string = "%s " % (self.mxp_name(viewer, '@verb #%s' % self.id) if hasattr(self, "mxp_name") else self.get_display_name(viewer))
        desc = self.db.desc
        desc_brief = self.db.desc_brief
        if desc and viewer.location == self:
            string += "%s" % desc
        elif desc_brief:
            string += "%s" % desc_brief
        else:
            string += "leads to %s" % self.destination.mxp_name(viewer, '@verb #%s' % self.destination.id) if hasattr(self.destination, "mxp_name") else self.destination.get_display_name(viewer)
        if exits:
            string += "\n|wExits: " + ", ".join("%s" % e.full_name(viewer) for e in exits)
        if users or things:
            user_list = ", ".join(u.full_name(viewer) for u in users)
            ut_joiner = ', ' if users and things else ''
            item_list = ", ".join(t.full_name(viewer) for t in things)
            path_view = 'Y' if viewer.location == self else 'Along the way y'
            string += "\n|w%sou see:|n " % path_view + user_list + ut_joiner + item_list
        return string


    def at_traverse(self, traversing_object, target_location):
        """
        Implements the actual traversal, using utils.delay to delay the move_to.
        """

        # if the exit has an attribute is_path and and traverser has move_speed,
        # use that, otherwise default to normal exit behavior and "walk" speed.

        is_path = self.db.is_path or False
        source_location = traversing_object.location
        move_speed = traversing_object.db.move_speed or "walk"
        move_delay = MOVE_DELAY.get(move_speed, 4)

        if not traversing_object.at_before_move(target_location):
            return False

        if is_path == False:
            success = traversing_object.move_to(self, quiet=False)
            if success:
                self.at_after_traverse(traversing_object, source_location)
            return success

        if traversing_object.location == target_location: # If object is at destination...
            return True


        def move_callback():
            "This callback will be called by utils.delay after move_delay seconds."

            source_location = traversing_object.location
            if traversing_object.move_to(target_location):
                traversing_object.nattributes.remove('currently_moving')
                self.at_after_traverse(traversing_object, source_location)
            else:
                if self.db.err_traverse: # if exit has a better error message, use it.
                    self.caller.msg(self.db.err_traverse)
                else:  # No shorthand error message. Call hook.
                    self.at_failed_traverse(traversing_object)

        traversing_object.msg("You start moving %s at a %s." % (self.key, move_speed))

        if traversing_object.location != self: # If object is not inside exit...
            success = traversing_object.move_to(self, quiet=False, use_destination=False)
            if not success:
                return False
            self.at_after_traverse(traversing_object, source_location)

        # create a delayed movement

        deferred = utils.delay(move_delay, callback=move_callback)

        # Store the deferred on the character, this will allow momvent
        # to abort. Use an ndb here since deferreds cannot be pickled.

        traversing_object.ndb.currently_moving = deferred


    def at_after_traverse(self, traveller, source_loc):
        "called by at_traverse just after traversing."

        traveller.ndb.last_location = source_loc
        if source_loc.destination == None:
            traveller.db.last_room = source_loc


SPEED_DESCS = {"stroll": "strolling",
               "walk": "walking",
               "run": "running",
               "sprint": "sprinting",
               "scamper": "scampering"}


class CmdSetSpeed(Command):
    """
    set your movement speed
    Usage:
      setspeed stroll||walk||run||sprint||scamper
    This will set your movement speed, determining how long time
    it takes to traverse exits. If no speed is set, 'walk' speed
    is assumed.
    """
    key = "setspeed"

    def func(self):
        """
        Simply sets an Attribute used by the SlowExit above.
        """
        speed = self.args.lower().strip()
        if speed not in SPEED_DESCS:
            self.caller.msg("Usage: setspeed stroll||walk||run||sprint||scamper")
        elif self.caller.db.move_speed == speed:
            self.caller.msg("You are already set to move by %s." % SPEED_DESCS[speed])
        else:
            self.caller.db.move_speed = speed
            self.caller.msg("You will now move by %s." % SPEED_DESCS[speed])


class CmdStop(Command):
    """
    stop moving
    Usage:
      stop
    Stops the current movement, if any.
    """
    key = "stop"
    locks = "cmd:on_path()"

    def func(self):
        """
        This is a very simple command, using the
        stored deferred from the exit traversal above.
        """

        currently_moving = self.caller.ndb.currently_moving
        if currently_moving:
            currently_moving.cancel() # disables the trigger.
            self.caller.nattributes.remove('currently_moving')  # Removes the trigger.
            self.caller.msg("You stop moving.")
        else:
            self.caller.msg("You are not moving.")


class CmdContinue(Command):
    """
    Move again: Exit the path into the room if stopped.
    Usage:
      contiue || move || go
    """
    key = "continue"
    aliases = ["move", "go"]
    locks = "cmd:on_path()"

    def func(self):
        """
        This just moves you if you're stopped.
        """

        caller = self.caller
        start = caller.location
        destination = caller.location.destination

        if destination == None:
            caller.msg("You have not yet decided which way to go.")
            return

        if caller.ndb.currently_moving:
            caller.msg("You are already moving.")
        else:
            caller.location.msg_contents("%s is going to %s." \
                % (caller.full_name(caller.sessions), \
                destination.full_name(caller.sessions)), exclude=caller)
            caller.msg("You begin %s toward %s." % (SPEED_DESCS[caller.db.move_speed], \
                destination.full_name(caller.sessions)))
            if caller.move_to(destination, quiet=False):
                start.at_after_traverse(caller, start)


class CmdBack(Command):
    """
    About face! Exit the path into the location room.
    Usage:
      back || return || u-turn
    """
    key = "back"
    aliases = ["return", "u-turn"]
    locks = "cmd:NOT no_back()"

    def func(self):
        """
        This turns you around if you are traveling,
        or tries to take you back to a previous room
        if you are stopped in a room.
        """

        caller = self.caller # The character calling "back"
        destination = caller.location.destination  # Where caller is going.
        start = caller.location.location  # Where caller came from.

        if destination == None: # You are inside of something.

            # Find an exit that leads back to the last room you were in.
            last_location = caller.ndb.last_location or False
            last_room = caller.db.last_room or False

            if last_room: # Message if you have arrived in a room already.
                if last_room != caller.location:  # We are not in the place we were.
                    # We came from another room. How do we go back?
                    exits = caller.location.exits  # All the ways we can go.
                    if exits:
                        for exit in exits:  # Iterate through all the exits...
                            # Is this exit the one that takes us back?
                            if exit.destination == last_room: # It's the way back!
                                caller.execute_cmd(exit.name) # Try! It might fail.
                    else: # The room has no way out of it.
                        caller.msg("You go back the way you came.")
                        caller.move_to(last_room)
            else:  # No way back, try out.
                if start:
                    caller.msg("You leave %s." % caller.location.full_name(caller.sessions))
                    caller.move_to(start)
                else:
                    caller.msg("You can not leave %s." % caller.location.full_name(caller.sessions))
            return
        elif caller.ndb.currently_moving: # If you are inside an exit,
            caller.execute_cmd('stop')  # traveling, then stop, go back.
        caller.msg("You turn around and go back the way you came.")
        caller.move_to(start)