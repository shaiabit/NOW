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
    key = "sense"
    aliases = ["l", "look", "taste", "touch", "smell", "listen"]
    locks = "cmd:all()"
    arg_regex = r"\s|$"

    def func(self):
        """
        Handle sensing objects in different ways. WIP: Expanding to handle other senses.
        """
        caller = self.caller
        args = self.args.strip()

        if args:
            # Parsing for object/aspect/detail:
            # Box's wheel = Red spinners lit with pyrotechnics.
            # object, aspect = args.rsplit("'s ", 1)
            # detail = self.rhs.strip()

            obj = caller.search(args,
                                candidates=caller.location.contents + caller.contents,
                                use_nicks=True,
                                quiet=True)
            if not obj:
                # no object found. Check if there is a matching detail around the location.
                # TODO: Restrict search for details by possessive parse:  [object]'s [aspect]
                candidates = [caller.location] + caller.location.contents + caller.contents
                for location in candidates:
                    # TODO: Continue if look location is not visible to looker.
                    if location and hasattr(location, "return_detail") and callable(location.return_detail):
                        detail = location.return_detail(args)
                        if detail:
                            # Show found detail.
                            caller.msg(detail)
                            return  # TODO: Add /all switch to override return here to view all details.
                # no detail found. Trigger delayed error messages
                _AT_SEARCH_RESULT(obj, caller, args, quiet=False)
                return
            else:
                # we need to extract the match manually.
                obj = utils.make_iter(obj)[0]
        else:
            obj = caller.location
            if not obj:
                caller.msg("There is nothing to see here.")
                return

        if not hasattr(obj, 'return_appearance'):
            # this is likely due to a player calling the command.
            obj = obj.character
        if not obj.access(caller, "view"):
            caller.msg("Could not find '%s'." % args)
            return
        # get object's appearance
        caller.msg(obj.return_appearance(caller))
        # the object's at_desc() method.
        obj.at_desc(looker=caller)

