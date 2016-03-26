# -*- coding: UTF-8 -*-
"""
Commands

Commands describe the input the player can do to the game.

"""

from evennia import Command as BaseCommand
from evennia import default_cmds


class Command(BaseCommand):
    """
    Inherit from this if you want to create your own
    command styles. Note that Evennia's default commands
    use MuxCommand instead (next in this module).

    Note that the class's `__doc__` string (this text) is
    used by Evennia to create the automatic help entry for
    the command, so make sure to document consistently here.

    Each Command implements the following methods, called
    in this order:
        - at_pre_command(): If this returns True, execution is aborted.
        - parse(): Should perform any extra parsing needed on self.args
            and store the result on self.
        - func(): Performs the actual work.
        - at_post_command(): Extra actions, often things done after
            every command, like prompts.

    """
    # these need to be specified

    key = "MyCommand"
    aliases = []
    locks = "cmd:all()"
    help_category = "General"

    # optional
    # auto_help = False      # uncomment to deactive auto-help for this command.
    # arg_regex = r"\s.*?|$" # optional regex detailing how the part after
                             # the cmdname must look to match this command.

    # (we don't implement hook method access() here, you don't need to
    #  modify that unless you want to change how the lock system works
    #  (in that case see evennia.commands.command.Command))

    def at_pre_cmd(self):
        """
        This hook is called before `self.parse()` on all commands.
        """
        pass

    def parse(self):
        """
        This method is called by the `cmdhandler` once the command name
        has been identified. It creates a new set of member variables
        that can be later accessed from `self.func()` (see below).

        The following variables are available to us:
           # class variables:

           self.key - the name of this command ('mycommand')
           self.aliases - the aliases of this cmd ('mycmd','myc')
           self.locks - lock string for this command ("cmd:all()")
           self.help_category - overall category of command ("General")

           # added at run-time by `cmdhandler`:

           self.caller - the object calling this command
           self.cmdstring - the actual command name used to call this
                            (this allows you to know which alias was used,
                             for example)
           self.args - the raw input; everything following `self.cmdstring`.
           self.cmdset - the `cmdset` from which this command was picked. Not
                         often used (useful for commands like `help` or to
                         list all available commands etc).
           self.obj - the object on which this command was defined. It is often
                         the same as `self.caller`.
        """
        pass

    def func(self):
        """
        This is the hook function that actually does all the work. It is called
        by the `cmdhandler` right after `self.parser()` finishes, and so has access
        to all the variables defined therein.
        """
        self.caller.msg("Command called!")

    def at_post_cmd(self):
        """
        This hook is called after `self.func()`.
        """
        pass


class MuxCommand(default_cmds.MuxCommand):
    """
    This sets up the basis for Evennia's 'MUX-like' command style.
    The idea is that most other Mux-related commands should
    just inherit from this and don't have to implement parsing of
    their own unless they do something particularly advanced.

    A MUXCommand command understands the following possible syntax:

        name[ with several words][/switch[/switch..]] arg1[,arg2,...] [[=|,] arg[,..]]

    The `name[ with several words]` part is already dealt with by the
    `cmdhandler` at this point, and stored in `self.cmdname`. The rest is stored
    in `self.args`.

    The MuxCommand parser breaks `self.args` into its constituents and stores them
    in the following variables:
        self.switches = optional list of /switches (without the /).
        self.raw = This is the raw argument input, including switches.
        self.args = This is re-defined to be everything *except* the switches.
        self.lhs = Everything to the left of `=` (lhs:'left-hand side'). If
                     no `=` is found, this is identical to `self.args`.
        self.rhs: Everything to the right of `=` (rhs:'right-hand side').
                    If no `=` is found, this is `None`.
        self.lhslist - `self.lhs` split into a list by comma.
        self.rhslist - list of `self.rhs` split into a list by comma.
        self.arglist = list of space-separated args (including `=` if it exists).

    All args and list members are stripped of excess whitespace around the
    strings, but case is preserved.
    """

    def func(self):
        """
        This is the hook function that actually does all the work. It is called
        by the `cmdhandler` right after `self.parser()` finishes, and so has access
        to all the variables defined therein.
        """
        # this can be removed in your child class, it's just
        # printing the ingoing variables as a demo.
        super(MuxCommand, self).func()


from builtins import range
import time
from django.conf import settings
from evennia.server.sessionhandler import SESSIONS
from evennia.commands.default.muxcommand import MuxPlayerCommand
from evennia.utils import utils, create, search, prettytable


class CmdQuit(MuxPlayerCommand):
    """
    quit the game
    Usage:
      @quit
    Switch:
      all - disconnect all connected sessions
    Gracefully disconnect your current session from the
    game. Use the /all switch to disconnect from all sessions.
    """
    key = "@quit"
    aliases = "quit"
    locks = "cmd:all()"

    def func(self):
        "hook function"
        player = self.player
        bye = '|RDisconnecting|n'
        exit_msg = 'Hope to see you again, soon.'

        if 'all' in self.switches:
            msg = bye + ' all sessions. ' + exit_msg
            player.msg(msg, session=self.session)
            for session in player.sessions.all():
                player.disconnect_session_from_player(session)
        else:
            nsess = len(player.sessions.all())
            if nsess == 2:
                msg = bye + '. One session is still connected.' 
                player.msg(msg, session=self.session)
            elif nsess > 2:
                msg = bye + ". %i sessions are still connected."
                player.msg(msg % (nsess-1), session=self.session)
            else:
                # we are quitting the last available session
                msg = bye + '. ' + exit_msg
                player.msg(msg, session=self.session)
            player.disconnect_session_from_player(self.session)


class CmdWho(MuxPlayerCommand):
    """
    list who is currently online
    Usage:
      who
    Shows who is currently online. Use the /f switch to see
    character locations, and more info for those with permissions.
    """

    key = "who"
    locks = "cmd:all()"

    def func(self):
        """
        Get all connected players by polling session.
        """

        player = self.player
        session_list = SESSIONS.get_sessions()

        session_list = sorted(session_list, key=lambda o: o.player.key)

        if 'f' in self.switches:
            show_session_data = player.check_permstring("Immortals") or player.check_permstring("Wizards")
        else:
            show_session_data = False


        nplayers = (SESSIONS.player_count())
        if 'f' in self.switches:
            if show_session_data:
                # privileged info - who/f by wizard or immortal
                table = prettytable.PrettyTable(["{wPlayer Name",
                                                 "{wOn for",
                                                 "{wIdle",
                                                 "{wCharacter",
                                                 "{wRoom",
                                                 "{wCmds",
                                                 "{wProtocol",
                                                 "{wHost"])
                for session in session_list:
                    if not session.logged_in: continue
                    delta_cmd = time.time() - session.cmd_last_visible
                    delta_conn = time.time() - session.conn_time
                    player = session.get_player()
                    puppet = session.get_puppet()
                    location = puppet.location.key if puppet else "None"
                    table.add_row([utils.crop(player.name, width=25),
                                   utils.time_format(delta_conn, 0),
                                   utils.time_format(delta_cmd, 1),
                                   utils.crop(puppet.key if puppet else "None", width=25),
                                   utils.crop(location, width=25),
                                   session.cmd_total,
                                   session.protocol_key,
                                   isinstance(session.address, tuple) and session.address[0] or session.address])
            else:
                # non privileged info - who/f by player

                table = prettytable.PrettyTable(["{wCharacter", "{wOn for", "{wIdle", "{wLocation"])
                for session in session_list:
                    if not session.logged_in:
                        continue
                    delta_cmd = time.time() - session.cmd_last_visible
                    delta_conn = time.time() - session.conn_time
                    player = session.get_player()
                    puppet = session.get_puppet()
                    location = puppet.location.key if puppet else "None"
                    table.add_row([utils.crop(puppet.key if puppet else "- Unknown -", width=25),
                                   utils.time_format(delta_conn, 0),
                                   utils.time_format(delta_cmd, 1),
                                   utils.crop(location, width=25)])
        else:
            # unprivileged info - who
            table = prettytable.PrettyTable(["{wCharacter", "{wOn for", "{wIdle"])
            for session in session_list:
                if not session.logged_in:
                    continue
                delta_cmd = time.time() - session.cmd_last_visible
                delta_conn = time.time() - session.conn_time
                player = session.get_player()
                puppet = session.get_puppet()
                table.add_row([utils.crop(puppet.key if puppet else "- Unknown -", width=25),
                               utils.time_format(delta_conn, 0),
                               utils.time_format(delta_cmd, 1)])

        isone = nplayers == 1
        string = "%s\n%s unique account%s logged in." % (table, "One" if isone else nplayers, "" if isone else "s")
        self.msg(string)


class CmdPose(MuxCommand):
    """
    Describe and/or attempt to trigger an action on an object.
    The pose text will automatically begin with your name.

    Usage:
      pose <pose text>
      pose's <pose text>

      pose <verb> <noun>:<pose text>

      try <verb> <noun>

    Example:
      > pose is standing by the tree, smiling.
      Rulan is standing by the tree, smiling.

      > pose get anvil:puts his back into it.
      Rulan tries to get the anvil. He puts his back into it.
      (optional success message if anvil is liftable.)

      > try unlock door
      Rulan tries to unlock the door.
      (optional success message if door is unlocked.)
    """
    key = "pose"
    aliases = [':', ';', 'emote', 'try']
    locks = "cmd:all()"

    def parse(self):
        """
        Parse the cases where the emote starts with specific characters,
        such as 's, at which we don't want to separate the character's
        name and the emote with a space.
        
        Also parse for a verb and noun in a power pose of the form:
        verb noun:pose
        
        verb noun:

        or using the try command, just
        verb noun
        """
        args = unicode(self.args)
        
        if self.cmdstring == 'try':
            args += ':'
        if len(args.split(':')) > 1:
            verbnoun, pose = args.split(':', 1)
            if len(verbnoun.split()) == 2:
                verb, noun=verbnoun.split()
                msg = "|r%s|n tries to %s the %s." % (self.caller.name, verb, noun)
                self.caller.location.msg_contents(msg)
                args = pose
        
        if args and not args[0] in ["-", "'", "’", ",", ";", ":", ".", "?", "!", "…"]:
            args = " %s" % args.strip()
        self.args = args

    def func(self):
        "Hook function"
        if self.args:
            msg = "|c%s|n%s" % (self.caller.name, self.args)
            self.caller.location.msg_contents(msg)
