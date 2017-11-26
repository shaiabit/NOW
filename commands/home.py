# -*- coding: utf-8 -*-
from commands.command import MuxCommand
from evennia.utils import utils, search


class CmdHome(MuxCommand):
    """
    Takes you to your home, if you have one. home/set will show you
    where your home is set, or provide a what and where to set its home.
    Usage:
      home[/option]
    Options:
    /set <obj> [=||to home_location]  views or sets <obj>'s home location.
    /sweep <obj>  send obj home.
    /here  sets current character's home to current location.
    /room  returns a character to its home room, regardless of where home is set.
    
    The "home" location is a "safety" location for objects; they will be
    moved there if their current location ceases to exist. All objects
    should always have a home location for this reason.
    It is also a convenient target of the "home" command.
    """
    key = 'home'
    options = ('set', 'sweep', 'here', 'room')
    locks = 'cmd:all()'
    arg_regex = r"^/|\s|$"
    help_category = 'Travel'
    account_caller = True
    parse_using = ' to '

    def func(self):
        """Implement the command"""
        you = self.character
        account = self.account
        opt = self.switches
        # you potentially has two homes.
        room = you.db.objects['home'] if you.db.objects and you.db.objects.get('home', False) else you.home
        home = room if 'room' in opt else you.home  # Or home room, to handle /room option
        if not opt or 'room' in opt:
            if not home:
                you.msg('You have no home yet.')
            else:
                if home == you.location:
                    if home is room:
                        you.msg('You are already home, which is the same as your home room')
                        return
                    else:
                        you.msg('You are already home. Sending you to your home room...')
                        home = room
                you.msg("There's no place like home ...")
                you.move_to(home, use_destination=False)
        else:
            if not self.args:
                obj = you
            else:
                obj = you.search(self.lhs, global_search=True)
            if not obj:
                return
            if 'sweep' in opt:
                home = obj.home
                if not home:
                    you.msg('%s has no home yet.' % obj.get_display_name(account))
                elif home == obj.location:
                    you.msg('%s is already home!' % obj.get_display_name(account))
                elif obj is not you and not account.check_permstring('helpstaff')\
                        and not obj.access(account, 'puppet') and not obj.access(you, 'control')\
                        and not obj.location.access(you, 'control'):
                    you.msg("You do not have access to send {} home.".format(obj.get_display_name(account)))
                    return
                else:
                    going_home = "There's no place like home ... ({} is sending you home.)"
                    obj.msg(going_home.format(you.get_display_name(obj)))
                    if you.location:
                        you.location.msg_contents('%s%s|n sends %s%s|n home.'
                                                  % (you.STYLE, you.key, obj.STYLE, obj.key))
                    was = obj.location
                    obj.move_to(home, use_destination=False)
                    if you.location != was:
                        source_location_name = was.get_display_name(you) if was else '|xNo|=gth|=fin|=egn|=des|=css|n'
                        you.msg("%s left %s and went home to %s."
                                % (obj.get_display_name(you), source_location_name, home.get_display_name(you)))
                return
            if not self.rhs and 'here' not in opt:  # just view the destination set as home
                if obj != you and not account.check_permstring('helpstaff') and not obj.access(account, 'puppet'):
                    you.msg("You must have |wHelpstaff|n or higher power to view the home of %s."
                            % obj.get_display_name(account))
                    return
                home = obj.home
                if not home:
                    string = "%s has no home location set!" % obj.get_display_name(you)
                else:
                    string = "%s's current home is %s." % (obj.get_display_name(you), home.get_display_name(you))
            else:  # set/change a home location
                if obj != you and not account.check_permstring('mage') and not obj.access(account, 'puppet'):
                    you.msg("You must have |wmage|n or higher powers to change the home of %s." % obj)
                    return
                if self.rhs and 'here' not in opt:
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
