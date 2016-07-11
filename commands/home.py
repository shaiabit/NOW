from evennia import default_cmds
from evennia.utils import utils, search


class CmdHome(default_cmds.MuxCommand):
    """
    Takes you to your home, if you have one. home/set will show you
    where your home is set, or provide a what and where to set its home.
    Usage:
      home
    Switches:
    /set <obj> [= home_location]  views or sets <obj>'s home location.
    /here  sets current character's home to current location.
    The "home" location is a "safety" location for objects; they will be
    moved there if their current location ceases to exist. All objects
    should always have a home location for this reason.
    It is also a convenient target of the "home" command.
    """
    key = 'home'
    locks = 'cmd:all()'
    arg_regex = r"^/|\s|$"
    help_category = 'Travel'
    player_caller = True

    def func(self):
        """Implement the command"""
        you = self.character
        player = self.player
        home = you.home
        if not self.switches:
            if not home:
                you.msg("You have no home yet.")
            elif home == you.location:
                you.msg("You are already home!")
            else:
                you.msg("There's no place like home ...")
                you.move_to(home)
        else:
            if not self.args:
                obj = you
            else:
                obj = you.search(self.lhs, global_search=True)
            if not obj:
                return
            if not self.rhs and 'here' not in self.switches:  # just view the destination set as home
                if obj != you and not player.check_permstring('Helpstaff') or not obj.access(player, 'puppet'):
                    you.msg("You must have |wHelpstaff|n or higher access to view the home of %s." % obj)
                    return
                home = obj.home
                if not home:
                    string = "%s has no home location set!" % obj.get_display_name(you)
                else:
                    string = "%s's current home is %s." % (obj, home.get_display_name(you))
            else:  # set/change a home location
                if obj != you and not player.check_permstring('Mages') or not obj.access(player, 'puppet'):
                    you.msg("You must have |wMages|n or higher access to change the home of %s." % obj)
                    return
                if self.rhs and 'here' not in self.switches:
                    new_home = you.search(self.rhs, global_search=True)
                else:
                    new_home = you.location
                if not new_home:
                    return
                old_home = obj.home
                obj.home = new_home
                if old_home:
                    string = "%s's home location was changed from %s to %s." % (obj, old_home.get_display_name(you),
                                                                                new_home.get_display_name(you))
                else:
                    string = "%s' home location was set to %s." % (obj, new_home.get_display_name(you))
            you.msg(string)
