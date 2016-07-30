# -*- coding: UTF-8 -*-
"""
Commands

Commands describe the input the player can do to the world.

"""
from evennia import gametime
from django.conf import settings
from evennia import utils
from evennia import default_cmds
from evennia import Command as BaseCommand
from evennia.commands.default.muxcommand import MuxCommand, MuxPlayerCommand


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
        self.caller.msg('Command "%s" called!' % self.cmdstring)

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
    player_caller = True

    def at_pre_cmd(self):
        """
        This hook is called before self.parse() on all commands
        """
        pass

    def parse(self):
        """
        This method is called by the cmdhandler once the command name
        has been identified. It creates a new set of member variables
        that can be later accessed from self.func()
        """
        super(MuxCommand, self).parse()

    def func(self):
        """
        This is the hook function that actually does all the work. It is called
        by the `cmdhandler` right after `self.parser()` finishes, and so has access
        to all the variables defined therein.
        """
        super(MuxCommand, self).func()

    def at_post_cmd(self):
        """
        This hook is called after the command has finished executing
        (after self.func()).
        """
        char = self.character
        here = char.location
        print('(%s%s)' % (self.cmdstring, self.raw))
        if here.location:
            if char.db.settings and 'broadcast command' in char.db.settings and char.db.settings['broadcast command']:
                here.msg_contents('|r(|n%s%s|n|r)|n' % (self.cmdstring, self.raw))


class MuxPlayerCommand(MuxCommand):
    """
    This is an on-Player version of the MuxCommand. Since these commands sit
    on Players rather than on Characters/Objects, we need to check
    this in the parser.
    Player commands are available also when puppeting a Character, it's
    just that they are applied with a lower priority and are always
    available, also when disconnected from a character (i.e. "ooc").
    This class makes sure that caller is always a Player object, while
    creating a new property "character" that is set only if a
    character is actually attached to this Player and Session.
    """
    def parse(self):
        """
        We run the parent parser as usual, then fix the result
        """
        super(MuxPlayerCommand, self).parse()

        if utils.inherits_from(self.caller, "evennia.objects.objects.DefaultObject"):
            self.character = self.caller  # caller is an Object/Character
            self.caller = self.caller.player
        elif utils.inherits_from(self.caller, "evennia.players.players.DefaultPlayer"):
            self.character = self.caller.get_puppet(self.session)  # caller was already a Player
        else:
            self.character = None

from django.conf import settings
from evennia.comms.models import ChannelDB, Msg
from evennia.comms.channelhandler import CHANNELHANDLER
from evennia.utils import create, utils, evtable
from evennia.utils.utils import make_iter

_DEFAULT_WIDTH = settings.CLIENT_DEFAULT_WIDTH


def find_channel(caller, channelname, silent=False, noaliases=False):
    """
    Helper function for searching for a single channel with
    some error handling.
    """
    channels = ChannelDB.objects.channel_search(channelname)
    if not channels:
        if not noaliases:
            channels = [chan for chan in ChannelDB.objects.get_all_channels()
                        if channelname in chan.aliases.all()]
        if channels:
            return channels[0]
        if not silent:
            caller.msg("Channel '%s' not found." % channelname)
        return None
    elif len(channels) > 1:
        matches = ", ".join(["%s(%s)" % (chan.key, chan.id) for chan in channels])
        if not silent:
            caller.msg("Multiple channels match (be more specific): \n%s" % matches)
        return None
    return channels[0]


class CmdChannels(MuxPlayerCommand):
    """
    Channels provide communication with a group of other players based on a
    particular interest or subject.  Channels are free of being at a particular
    location. Channels use their alias as the command to post to then.
    Usage:
      chan
    Options:
    /list to display all available channels.
    /join (on) or /part (off) to join or depart channels.

    Batch options:
    /all      to affect all channels at once:
    /all on   to join all available channels.
    /all off  to part all channels currently on.

       If you control a channel:
    /all who <channel> to list who listens to all channels.
    /who  <channel>    who listens to a specific channel.
    /lock <channel>    to set a lock on a channel.
    /desc <channel> = <description>  to describe a channel.
    /emit <channel> = <message>   to emit to channel.
    /name <channel> = <message>   sends to channel as if you're joined.
    /remove <channel> = <player> [:reason]  to remove a player from the channel.
    /quiet <channel> = <player>[:reason]    to remove the user quietly.
    """
    key = 'channel'
    aliases = ['chan', 'channels']
    help_category = 'Communication'
    locks = 'cmd: not pperm(channel_banned)'

    def func(self):
        """Implement function"""

        caller = self.caller
        args = self.args

        # Of all channels, list only the ones with access to listen
        channels = [chan for chan in ChannelDB.objects.get_all_channels()
                    if chan.access(caller, 'listen')]
        if not channels:
            self.msg("No channels available.")
            return

        subs = ChannelDB.objects.get_subscriptions(caller)  # All channels already joined

        if 'list' in self.switches:
            # full listing (of channels caller is able to listen to) ✔ or ✘
            comtable = evtable.EvTable("|wchannel|n", "|wdescription|n", "|wown sub send|n",
                                       "|wmy aliases|n", maxwidth=_DEFAULT_WIDTH)
            for chan in channels:
                clower = chan.key.lower()
                nicks = caller.nicks.get(category="channel", return_obj=True)
                nicks = nicks or []
                control = '|gYes|n ' if chan.access(caller, 'control') else '|rNo|n  '
                send = '|gYes|n ' if chan.access(caller, 'send') else '|rNo|n  '
                sub = chan in subs and '|gYes|n ' or '|rNo|n  '
                comtable.add_row(*["%s%s" % (chan.key, chan.aliases.all() and
                                   "(%s)" % ",".join(chan.aliases.all()) or ''),
                                   chan.db.desc,
                                   control + sub + send,
                                   "%s" % ",".join(nick.db_key for nick in make_iter(nicks)
                                                   if nick.strvalue.lower() == clower)])
            caller.msg("|/|wAvailable channels|n:|/" +
                       "%s|/(Use |w/list|n, |w/join|n and |w/part|n to manage received channels.)" % comtable)
        elif 'join' in self.switches or 'on' in self.switches:
            if not args:
                self.msg("Usage: %s/join [alias =] channelname." % self.cmdstring)
                return

            if self.rhs:  # rhs holds the channelname
                channelname = self.rhs
                alias = self.lhs
            else:
                channelname = args
                alias = None

            channel = find_channel(caller, channelname)
            if not channel:
                # custom search method handles errors.
                return

            # check permissions
            if not channel.access(caller, 'listen'):
                self.msg("%s: You are not able to receive this channel." % channel.key)
                return

            string = ''
            if not channel.has_connection(caller):
                # we want to connect as well.
                if not channel.connect(caller):
                    # if this would have returned True, the player is connected
                    self.msg("%s: You are not able to join this channel." % channel.key)
                    return
                else:
                    string += "You now listen to channel %s. " % channel.key
            else:
                string += "You already receive channel %s." % channel.key

            if alias:
                # create a nick and add it to the caller.
                caller.nicks.add(alias, channel.key, category="channel")
                string += " You can now refer to the channel %s with the alias '%s'."
                self.msg(string % (channel.key, alias))
            else:
                string += " No alias added."
            self.msg(string)
        elif 'part' in self.switches or 'off' in self.switches:
            if not args:
                self.msg("Usage: %s/part <alias or channel>" % self.cmdstring)
                return
            ostring = self.args.lower()

            channel = find_channel(caller, ostring, silent=True, noaliases=True)
            if channel:  # Given a channel name to part.
                if not channel.has_connection(caller):
                    self.msg("You are not listening to that channel.")
                    return
                chkey = channel.key.lower()
                # find all nicks linked to this channel and delete them
                for nick in [nick for nick in make_iter(caller.nicks.get(category="channel", return_obj=True))
                             if nick and nick.strvalue.lower() == chkey]:
                    nick.delete()
                disconnect = channel.disconnect(caller)
                if disconnect:
                    self.msg("You stop receiving channel '%s'. Any aliases were removed." % channel.key)
                return
            else:
                # we are removing a channel nick
                channame = caller.nicks.get(key=ostring, category="channel")
                channel = find_channel(caller, channame, silent=True)
                if not channel:
                    self.msg("No channel with alias '%s' was found." % ostring)
                else:
                    if caller.nicks.get(ostring, category="channel"):
                        caller.nicks.remove(ostring, category="channel")
                        self.msg("Your alias '%s' for channel %s was cleared." % (ostring, channel.key))
                    else:
                        self.msg("You had no such alias defined for this channel.")
        elif 'who' in self.switches:
            if not self.args:
                self.msg("Usage: %s/who <channel name or alias>" % self.cmdstring)
                return
            channel = find_channel(self.caller, self.lhs)
            if not channel:
                return
            if not channel.access(self.caller, "control"):
                string = "You do not control this channel."
                self.msg(string)
                return
            string = "\n|CChannel receivers|n"
            string += " of |w%s:|n " % channel.key
            subs = channel.db_subscriptions.all()
            if subs:
                string += ", ".join([player.key for player in subs])
            else:
                string += "<None>"
            self.msg(string.strip())
        elif 'lock' in self.switches:
            if not self.args:
                self.msg("Usage: %s/lock <alias or channel>" % self.cmdstring)
                return
            channel = find_channel(self.caller, self.lhs)
            if not channel:
                return
            if not self.rhs:  # no =, so just view the current locks
                string = "Current locks on %s:" % channel.key
                string = "%s %s" % (string, channel.locks)
                self.msg(string)
                return
            # we want to add/change a lock.
            if not channel.access(self.caller, "control"):
                string = "You don't control this channel."
                self.msg(string)
                return
            channel.locks.add(self.rhs)  # Try to add the lock
            string = "Lock(s) applied on %s:" % channel.key
            string = "%s %s" % (string, channel.locks)
            self.msg(string)
        elif 'emit' in self.switches or 'name' in self.switches:
            if not self.args or not self.rhs:
                switch = 'emit' if 'emit' in self.switches else 'name'
                string = "Usage: %s/%s <channel> = <message>" % (self.cmdstring, switch)
                self.msg(string)
                return
            channel = find_channel(self.caller, self.lhs)
            if not channel:
                return
            if not channel.access(self.caller, "control"):
                string = "You don't control this channel."
                self.msg(string)
                return
            message = self.rhs
            if 'name' in self.switches:
                message = "%s: %s" % (self.caller.key, message)
            channel.msg(message)
            if 'quiet' not in self.switches:
                string = "Sent to channel %s: %s" % (channel.key, message)
                self.msg(string)
        elif 'desc' in self.switches:
            if not self.rhs:
                self.msg("Usage: %s/desc <channel> = <description>" % self.cmdstring)
                return
            channel = find_channel(caller, self.lhs)
            if not channel:
                self.msg("Channel '%s' not found." % self.lhs)
                return
            if not channel.access(caller, 'control'):  # check permissions
                self.msg("You cannot describe this channel.")
                return
            channel.db.desc = self.rhs  # set the description
            channel.save()
            self.msg("Description of channel '%s' set to '%s'." % (channel.key, self.rhs))
        elif 'all' in self.switches:
            if not args:
                caller.execute_cmd("@channels")
                self.msg("Usage: %s/all on || off || who || clear" % self.cmdstring)
                return
            if args == "on":  # get names of all channels available to listen to and activate them all
                channels = [chan for chan in ChannelDB.objects.get_all_channels()
                            if chan.access(caller, 'listen')]
                for channel in channels:
                    caller.execute_cmd("@command/join %s" % channel.key)
            elif args == 'off':
                # get names all subscribed channels and disconnect from them all
                channels = ChannelDB.objects.get_subscriptions(caller)
                for channel in channels:
                    caller.execute_cmd("@command/part %s" % channel.key)
            elif args == 'who':
                # run a who, listing the subscribers on visible channels.
                string = "\n|CChannel subscriptions|n"
                channels = [chan for chan in ChannelDB.objects.get_all_channels()
                            if chan.access(caller, 'listen')]
                if not channels:
                    string += "No channels."
                for channel in channels:
                    if not channel.access(self.caller, "control"):
                        continue
                    string += "\n|w%s:|n\n" % channel.key
                    subs = channel.db_subscriptions.all()
                    if subs:
                        string += "  " + ", ".join([player.key for player in subs])
                    else:
                        string += "  <None>"
                self.msg(string.strip())
            else:
                # wrong input
                self.msg("Usage: %s/all on | off | who | clear" % self.cmdstring)
        elif 'remove' in self.switches or 'quiet' in self.switches:
            if not self.args or not self.rhs:
                switch = 'remove' if 'remove' in self.switches else 'quiet'
                string = "Usage: %s/%s <channel> = <player> [:reason]" % (self.cmdstring, switch)
                self.msg(string)
                return
            channel = find_channel(self.caller, self.lhs)
            if not channel:
                return
            reason = ''
            if ":" in self.rhs:
                playername, reason = self.rhs.rsplit(":", 1)
                searchstring = playername.lstrip('*')
            else:
                searchstring = self.rhs.lstrip('*')
            player = self.caller.search(searchstring, player=True)
            if not player:
                return
            if reason:
                reason = " (reason: %s)" % reason
            if not channel.access(self.caller, "control"):
                string = "You don't control this channel."
                self.msg(string)
                return
            if player not in channel.db_subscriptions.all():
                string = "Player %s is not connected to channel %s." % (player.key, channel.key)
                self.msg(string)
                return
            if 'quiet' not in self.switches:
                string = "%s boots %s from channel.%s" % (self.caller, player.key, reason)
                channel.msg(string)
            # find all player's nicks linked to this channel and delete them
            for nick in [nick for nick in
                         player.character.nicks.get(category="channel") or []
                         if nick.db_real.lower() == channel.key]:
                nick.delete()
            channel.disconnect(player)  # disconnect player
            CHANNELHANDLER.update()
        else:  # just display the subscribed channels with no extra info
            comtable = evtable.EvTable("|wchannel|n", "|wmy aliases|n",
                                       "|wdescription|n", align="l", maxwidth=_DEFAULT_WIDTH)
            for chan in subs:
                clower = chan.key.lower()
                nicks = caller.nicks.get(category="channel", return_obj=True)
                comtable.add_row(*["%s%s" % (chan.key, chan.aliases.all() and
                                   "(%s)" % ",".join(chan.aliases.all()) or ""),
                                   "%s" % ",".join(nick.db_key for nick in make_iter(nicks)
                                                   if nick and nick.strvalue.lower() == clower),
                                   chan.db.desc])
            caller.msg("\n|wChannel subscriptions|n (use |w@chan/list|n to list all, " +
                       "|w/join|n |w/part|n to join or part):|n\n%s" % comtable)
