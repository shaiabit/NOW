from evennia import default_cmds
from django.conf import settings
from evennia import utils

# error return function, needed by Extended Look command
_AT_SEARCH_RESULT = utils.variable_from_module(*settings.SEARCH_AT_RESULT.rsplit('.', 1))


class CmdSense(default_cmds.MuxCommand):
    """
    Handle sensing objects in different ways. WIP: Expanding to handle other senses.

    Sense yourself, your location or objects in your vicinity.
    Usage:
      <sense verb>[/switch] <object>['s aspect[ = [detail]]
      <sense verb>[/switch] *<player>['s aspect[ = [detail]]

      Add detail following the equal sign after the object's aspect.
      Nothing following the equals sign (=) will remove the detail
    """
    key = 'sense'
    aliases = ['l', 'look', 'taste', 'touch', 'smell', 'listen']
    locks = 'cmd:all()'
    arg_regex = r'\s|$'
    player_caller = True

    def func(self):
        """Handle sensing objects in different ways. WIP: Expanding to handle other senses."""
        char = self.character
        # player = self.player
        args = self.args.strip()
        cmd = self.cmdstring

        if cmd != 'l' and 'look' not in cmd:
            if 'sense' in cmd:
                if char and char.location:
                    obj_list = char.search(args, candidates=[char.location] + char.location.contents +
                                           char.contents) if args else char
                    if obj_list and obj_list.db.senses:
                        char.msg('You can sense %s in the following ways: %s' % (obj_list, obj_list.db.senses.keys()))
                        obj = obj_list
                        verb_msg = "You can interact with %s: " % obj_list.get_display_name(self.session)
                    else:
                        obj = char
                        verb_msg = "You can be interacted with by: "
                    verbs = obj.locks
                    collector = ''
                    show_red = True if obj.access(char, 'examine') else False
                    for verb in ("%s" % verbs).split(';'):
                        element = verb.split(':')[0]
                        if element == 'call':
                            continue
                        name = element[2:] if element[:2] == 'v-' else element
                        if obj.access(char, element):  # obj lock checked against actor
                            collector += "|lctry %s #%s|lt|g%s|n|le " % (name, obj.id, name)
                        elif show_red:
                            collector += "|r%s|n " % name
                    char.msg(verb_msg + "%s" % collector)
            elif 'taste' in cmd or 'touch' in cmd or 'smell' in cmd or 'listen' in cmd:  # Specific sense (not look)
                obj_list = char.search(args, candidates=[char.location] + char.location.contents + char.contents)\
                    if args else char
                char.msg('You try to sense %s.' % (obj_list if obj_list else 'something'))
                # Object to sense might have been found. Check the senses dictionary.
                if obj_list and obj_list.db.senses and cmd in obj_list.db.senses:
                    senses_of = obj_list.db.senses[cmd]
                    if None in senses_of:
                            details_of = obj_list.db.details
                            if details_of and senses_of[None] in details_of:
                                entry = details_of[senses_of[None]]
                                char.msg('You sense %s from %s.' % (entry, obj_list))
                # First case: look for an object in room, inventory, room contents, their contents,
                # and their contents contents with tagged restrictions, then if no match is found
                # in their name or alias, look at the senses tables in each of these objects: The
                # Senses attribute is a dictionary of senses that point to the details dictionary
                # entries. Senses dictionary allows for aliases in the details and pointing
                # specific senses to specific entries.
                #
                # If not looking for a specific object or entry, list objects and aspects of the particular
                # sense. Start with that first, and start with the char's own self and inventory.
                # when the /self;me and /inv;inventory switch is used?
            return
        if args:
            # Parsing for object/aspect/detail:
            # Box's wheel = Red spinners lit with pyrotechnics.
            # object, aspect = args.rsplit("'s ", 1)
            # detail = self.rhs.strip()

            obj = char.search(args,
                              candidates=char.location.contents + char.contents,
                              use_nicks=True,
                              quiet=True)
            if not obj:
                # no object found. Check if there is a matching detail around the location.
                # TODO: Restrict search for details by possessive parse:  [object]'s [aspect]
                candidates = [char.location] + char.location.contents + char.contents
                for location in candidates:
                    # TODO: Continue if look location is not visible to looker.
                    if location and hasattr(location, "return_detail") and callable(location.return_detail):
                        detail = location.return_detail(args)
                        if detail:
                            # Show found detail.
                            char.msg(detail)
                            return  # TODO: Add /all switch to override return here to view all details.
                # no detail found. Trigger delayed error messages
                _AT_SEARCH_RESULT(obj, char, args, quiet=False)
                return
            else:
                # we need to extract the match manually.
                obj = utils.make_iter(obj)[0]
        else:
            obj = char.location
            if not obj:
                char.msg("There is nothing to sense here.")
                return
        if not hasattr(obj, 'return_appearance'):
            # this is likely due to a player calling the command.
            obj = obj.character
        if not obj.access(char, 'view'):
            char.msg("You are unable to sense '%s'." % args)
            return
        # get object's appearance
        char.msg(obj.return_appearance(char))
        # the object's at_desc() method.
        obj.at_desc(looker=char)
