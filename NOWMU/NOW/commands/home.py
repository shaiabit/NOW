from evennia import default_cmds
from evennia.utils import utils, search

class CmdHome(default_cmds.MuxCommand):
    """
    move to your character's home location
    Usage:
      home  or
    Switches:
      home/set <obj> [= home_location]
    Takes you to your home, if you have one. home/set will show you
    where your home is set, or provide a what and where to set its home.
    """

    key = "home"
    locks = "cmd:all()"
    arg_regex = r"^/|\s|$"
    help_category = "Travel"

    def func(self):
        "Implement the command"

        caller = self.caller
        home = caller.home

        if not 'set' in self.switches:
            if not home:
                caller.msg("You have no home yet.")
            elif home == caller.location:
                caller.msg("You are already home!")
            else:
                caller.msg("There's no place like home ...")
                caller.move_to(home)
        else:
            if not self.args:
                string = "Usage: home/set <obj> [= home_location]"
                self.caller.msg(string)
                return
            obj = caller.search(self.lhs, global_search=True)
            if not obj:
                return
            if not self.rhs: # just view the destination set as home
                home = obj.home
                if not home:
                    string = "%s has no home location set!" % obj.get_display_name(caller)
                else:
                    string = "%s's current home is %s." % (obj, home.get_display_name(caller))
            else:  # set/change a home location
                new_home = caller.search(self.rhs, global_search=True)
                if not new_home:
                    return
                old_home = obj.home
                obj.home = new_home
                if old_home:
                    string = "%s's home location was changed from %s to %s." % (obj, old_home.get_display_name(caller), new_home.get_display_name(caller))
                else:
                    string = "%s' home location was set to %s." % (obj, new_home.get_display_name(caller))
            caller.msg(string)
