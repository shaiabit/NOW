from evennia import default_cmds
# May need other imports. See: https://github.com/evennia/evennia/blob/d42e971be63047f4f33414e88488077c15120afe/evennia/commands/default/building.py


class CmdDestroy(default_cmds.MuxCommand):
    """
    permanently delete objects
    Usage:
       @destroy[/switches] [obj, obj2, obj3, [dbref-dbref], ...]
    switches:
       override - The @destroy command will usually avoid accidentally
                  destroying player objects. This switch overrides this safety.
    examples:
       @destroy house, roof, door, 44-78
       @destroy 5-10, flower, 45
    Destroys one or many objects. If dbrefs are used, a range to delete can be
    given, e.g. 4-10. Also the end points will be deleted.
    """

    key = "destroy"
    aliases = ["delete", "recycle"]
    locks = "cmd:perm(destroy) or perm(Builders)"
    help_category = "Building"

    def func(self):
        "Implements the command."

        caller = self.caller

        if not self.args or not self.lhslist:
            caller.msg("Usage: %s[/switches] [obj, obj2, obj3, [dbref-dbref],...]" % self.cmdstring)
            return ""

        def delobj(objname, byref=False):
            # helper function for deleting a single object
            string = ""
            obj = caller.search(objname)
            if not obj:
                self.caller.msg(" (Objects to destroy must either be local or specified with a unique #dbref.)")
                return ""
            objname = obj.name
            if not obj.access(caller, 'delete'):
                return "\nYou don't have permission to delete %s." % objname
            if obj.player and not 'override' in self.switches:
                return "\nObject %s is controlled by an active player. Use /override to delete anyway." % objname
            if obj.dbid == int(settings.DEFAULT_HOME.lstrip("#")):
                return "\nYou are trying to delete {c%s{n, which is set as DEFAULT_HOME. " \
                        "Re-point settings.DEFAULT_HOME to another " \
                        "object before continuing." % objname

            had_exits = hasattr(obj, "exits") and obj.exits
            had_objs = hasattr(obj, "contents") and any(obj for obj in obj.contents
                                                        if not (hasattr(obj, "exits") and obj not in obj.exits))
            # do the deletion or removal
            obj.location = None
            # okay = obj.delete()
            okay = True if obj.location == None else False
            if not okay:
                string += "\nERROR: %s not deleted, probably because delete() returned False." % objname
            else:
                string += "\n%s vanishes." % objname  # Trigger effects
                if had_exits:
                    string += " Exits to and from %s were destroyed as well." % objname
                if had_objs:
                    string += " Objects inside %s were moved to their homes." % objname
            return string

        string = ""
        for objname in self.lhslist:
            if '-' in objname:
                # might be a range of dbrefs
                dmin, dmax = [utils.dbref(part, reqhash=False)
                              for part in objname.split('-', 1)]
                if dmin and dmax:
                    for dbref in range(int(dmin), int(dmax + 1)):
                        string += delobj("#" + str(dbref), True)
                else:
                    string += delobj(objname)
            else:
                string += delobj(objname, True)
        if string:
            caller.msg(string.strip())
