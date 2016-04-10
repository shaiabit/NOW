# -*- coding: UTF-8 -*-
"""
Commands

Commands describe the input the player can do to the world.

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


from past.builtins import cmp
from django.conf import settings
from evennia.comms.models import ChannelDB, Msg
#from evennia.comms import irc, imc2, rss
from evennia.players.models import PlayerDB
from evennia.players import bots
from evennia.comms.channelhandler import CHANNELHANDLER
from evennia.utils import create, utils, evtable
from evennia.utils.utils import make_iter
from evennia.commands.default.muxcommand import MuxCommand, MuxPlayerCommand

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


class CmdChannelWizard(MuxPlayerCommand):
    """
    Creates (or destroys) a new channel controlled by you.
    Usage:
     !channel <new channel>[;alias;alias...] = description
    Switch:
     !channel/destroy <channel name>
    """

    key = "!channel"
    locks = "cmd:not pperm(channel_banned) and perm(Wizard)"
    help_category = "Admin"

    def func(self):
        "Implement the command"

        caller = self.caller

        if not 'destroy' in self.switches:
            if not self.args:
                self.msg("Usage %s <channelname>[;alias;alias..] = description" % self.cmdstring)
                return

            description = ""

            if self.rhs:
                description = self.rhs
            lhs = self.lhs
            channame = lhs
            aliases = None
            if ';' in lhs:
                channame, aliases = lhs.split(';', 1)
                aliases = [alias.strip().lower() for alias in aliases.split(';')]
            channel = ChannelDB.objects.channel_search(channame)
            if channel:
                self.msg("A channel with that name already exists.")
                return
            # Create and set the channel up
            lockstring = "send:all();listen:all();control:id(%s)" % caller.id
            new_chan = create.create_channel(channame.strip(),
                                             aliases,
                                             description,
                                             locks=lockstring)
        else:
            new_chan.connect(caller)
            CHANNELHANDLER.update()
            self.msg("Created channel %s and connected to it." % new_chan.key)

            if not self.args:
                self.msg("Usage: %s/destroy <channelname>" % self.cmdstring)
                return
            channel = find_channel(caller, self.args)
            if not channel:
                self.msg("Could not find channel %s." % self.args)
                return
            if not channel.access(caller, 'control'):
                self.msg("You are not allowed to do that.")
                return
            channel_key = channel.key
            message = "%s is being destroyed. Make sure to change your aliases." % channel_key
            msgobj = create.create_message(caller, message, channel)
            channel.msg(msgobj)
            channel.delete()
            CHANNELHANDLER.update()
            self.msg("Channel '%s' was destroyed." % channel_key)


class CmdChannels(MuxPlayerCommand):
    """
    list all channels available to you
    Usage:
      @chan
      @channel
      @channels
    Lists channels you are currently receiving.
      Use /list to display all available channels.
      Use /join or /part to join or depart channels.
    Batch:
      Use /all to affect all channels at once:
      Use /all on  to join all available channels.
      Use /all off  to part all channels currently on.
    If you control a channel:
      Use /all who  to list who listens to all channels.
      Use /who to see who listens to a specific channel.
      Use /lock to set a lock on a channel.
      Use /desc to describe a channel.
      Use /emit to emit on a channel.
        Use /name when emitting, to display your name.
      Use /remove to remove a player from the channel.
        Use /quiet to remove the user quietly.
    """
    key = "@channel"
    aliases = ["@chan", "@channels"]
    help_category = "Communication"
    locks = "cmd: not pperm(channel_banned)"

    def func(self):
        """Implement function"""

        caller = self.caller
        args = self.args

        # all channels we have available to listen to
        channels = [chan for chan in ChannelDB.objects.get_all_channels()
                    if chan.access(caller, 'listen')]
        if not channels:
            self.msg("No channels available.")
            # Suggest use of /join switch and brief-list join-able channels.
            return
        # all channel we are already subscribed to
        subs = ChannelDB.objects.get_subscriptions(caller)

        if 'list' in self.switches:
            # full listing (of channels caller is able to listen to)
            comtable = evtable.EvTable("|wsub|n", "|wchannel|n", "|wmy aliases|n",
                                       "|wlocks|n", "|wdescription|n", maxwidth=_DEFAULT_WIDTH)
            #comtable = prettytable.PrettyTable(["|wsub", "|wchannel", "|wmy aliases", "|wlocks", "|wdescription"])
            for chan in channels:
                clower = chan.key.lower()
                nicks = caller.nicks.get(category="channel", return_obj=True)
                nicks = nicks or []
                comtable.add_row(*[chan in subs and "|gYes|n" or "|rNo|n",
                                  "%s%s" % (chan.key, chan.aliases.all() and
                                  "(%s)" % ",".join(chan.aliases.all()) or ""),
                                  "%s" % ",".join(nick.db_key for nick in make_iter(nicks)
                                  if nick.strvalue.lower() == clower),
                                  str(chan.locks),
                                  chan.db.desc])
            caller.msg("\n|wAvailable channels|n" +
                       " (Use |w/list|n,|w/join|n and |w/part|n to manage received channels.):\n%s" % comtable)
        elif 'join' in self.switches:
            if not args:
                self.msg("Usage: %s/join [alias =] channelname." % self.cmdstring)
                return

            if self.rhs: # rhs holds the channelname
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
        elif 'part' in self.switches:
            if not args:
                self.msg("Usage: %s/part <alias or channel>" % self.cmdstring)
                return
            ostring = self.args.lower()

            channel = find_channel(caller, ostring, silent=True, noaliases=True)
            if channel:
                # we have given a channel name - unsubscribe
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
            if not self.rhs: # no =, so just view the current locks
                string = "Current locks on %s:" % channel.key
                string = "%s %s" % (string, channel.locks)
                self.msg(string)
                return
            # we want to add/change a lock.
            if not channel.access(self.caller, "control"):
                string = "You don't control this channel."
                self.msg(string)
                return
            channel.locks.add(self.rhs) # Try to add the lock
            string = "Lock(s) applied on %s:" % channel.key
            string = "%s %s" % (string, channel.locks)
            self.msg(string)
        elif 'emit' in self.switches:
            if not self.args or not self.rhs:
                string = "Usage: %s/emit[/name] <channel> = <message>" % self.cmdstring
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
            if "name" in self.switches:
                message = "%s: %s" % (self.caller.key, message)
            channel.msg(message)
            if not "quiet" in self.switches:
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
            if not channel.access(caller, 'control'): # check permissions
                self.msg("You cannot describe this channel.")
                return
            channel.db.desc = self.rhs  # set the description
            channel.save()
            self.msg("Description of channel '%s' set to '%s'." % (channel.key, self.rhs))
        elif 'all' in self.switches:
            if not args:
                caller.execute_cmd("@channels")
                self.msg("Usage: %s/all on | off | who | clear" % self.cmdstring)
                return

            if args == "on":
                # get names of all channels available to listen to
                # and activate them all
                channels = [chan for chan in ChannelDB.objects.get_all_channels()
                            if chan.access(caller, 'listen')]
                for channel in channels:
                    caller.execute_cmd("@command/join %s" % channel.key)
            elif args == "off":
                # get names all subscribed channels and disconnect from them all
                channels = ChannelDB.objects.get_subscriptions(caller)
                for channel in channels:
                    caller.execute_cmd("@command/part %s" % channel.key)
            elif args == "who":
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
        elif 'remove' in self.switches:
            if not self.args or not self.rhs:
                string = "Usage: %s/remove [/quiet] <channel> = <player> [:reason]" % self.cmdstring
                self.msg(string)
                return
            channel = find_channel(self.caller, self.lhs)
            if not channel:
                return
            reason = ""
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
            if not player in channel.db_subscriptions.all():
                string = "Player %s is not connected to channel %s." % (player.key, channel.key)
                self.msg(string)
                return
            if not "quiet" in self.switches:
                string = "%s boots %s from channel.%s" % (self.caller, player.key, reason)
                channel.msg(string)
            # find all player's nicks linked to this channel and delete them
            for nick in [nick for nick in
                         player.character.nicks.get(category="channel") or []
                         if nick.db_real.lower() == channel.key]:
                nick.delete()
            channel.disconnect(player)  # disconnect player
            CHANNELHANDLER.update()
        else: # just display the subscribed channels with no extra info
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
            caller.msg("\n|wChannel subscriptions|n (use |w@chan/list|n to list all, "
                       "|w/join|n |w/part|n to join or part):|n\n%s" % comtable)

import time
from builtins import range
from django.conf import settings
from evennia.server.sessionhandler import SESSIONS
from evennia.commands.default.muxcommand import MuxPlayerCommand
from evennia.utils import ansi, utils, create, search, prettytable


class CmdLook(MuxCommand):
    """
    look at location or object
    Usage:
      look
      look <obj>
      look *<player>
    Observes your location or objects in your vicinity.
    """
    key = "look"
    aliases = ["l", "ls"]
    locks = "cmd:all()"
    arg_regex = r"\s|$"

    def func(self):
        """
        Handle looking at objects.
        """
        if not self.args:
            target = self.caller.location
            if not target:
                self.caller.msg("You have no location to look at!")
                return
        else:
            target = self.caller.search(self.args)
            if not target:
                return
        self.msg(self.caller.at_look(target))


class CmdQuit(MuxPlayerCommand):
    """
    Gracefully disconnect your current session
      quit
      @quit
    Use the /all switch to disconnect from all sessions.
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
                player.msg(msg % (nsess - 1), session=self.session)
            else:
                # we are quitting the last available session - give connect time.
                online = utils.time_format(time.time() - self.session.conn_time, 1)
                msg = bye + ' after ' + online + ' online. ' + exit_msg
                player.msg(msg, session=self.session)
            player.disconnect_session_from_player(self.session)


class CmdAccess(MuxCommand):
    """
    Displays your current world access levels.
    Usage:
      @access
    Displays the system's permission hierarchy and the
    permissions for your current character and player account.
    """

    key = "@access"
    locks = "cmd:all()"
    help_category = "System"
    arg_regex = r"$"

    def func(self):
        "Load the permission groups"

        caller = self.caller
        hierarchy_full = settings.PERMISSION_HIERARCHY
        string = "\n|wPermission Hierarchy|n (climbing):\n %s" % ", ".join(hierarchy_full)
        #hierarchy = [p.lower() for p in hierarchy_full]

        if self.caller.player.is_superuser:
            cperms = "<Superuser>"
            pperms = "<Superuser>"
        else:
            cperms = ", ".join(caller.permissions.all())
            pperms = ", ".join(caller.player.permissions.all())

        string += "\n|wYour access|n:"
        string += "\nCharacter |c%s|n: %s" % (caller.key, cperms)
        if hasattr(caller, 'player'):
            string += "\nPlayer |c%s|n: %s" % (caller.player.key, pperms)
        caller.msg(string)


class CmdOoc(MuxCommand):
    """
    Send an out-of-character message to your current location.
    Usage:
      ooc <message>
      ooc :<message>
      ooc "<message>
    """

    key = "ooc"
    aliases = ['_']
    locks = "cmd:all()"

    def func(self):
        "Run the ooc command"

        caller = self.caller
        args = self.args.strip()

        if not args:
            caller.execute_cmd("help ooc")
            return
        elif args[0] == '"' or args[0] == "'":
            caller.execute_cmd('say/o ' + caller.location.at_say(caller, args[1:]))
        elif args[0] == ':' or args[0] == ';':
            caller.execute_cmd('pose/o %s' % args[1:])
        else:
            caller.location.msg_contents('[OOC |c%s|n] %s' % (caller.name, args))


class CmdSpoof(MuxCommand):
    """
    Send a spoofed message to your current location.
    Usage:
      spoof <message>
    """

    key = "spoof"
    aliases = ['~', '`', 'sp']
    locks = "cmd:all()"

    def func(self):
        "Run the spoof command"

        caller = self.caller

        if not self.args:
            caller.execute_cmd("help spoof")
            return
        # Strip any markup to secure the spoof.
        spoof = ansi.strip_ansi(self.args)

        # calling the speech hook on the location.
        # An NPC would know who spoofed.
        spoof = caller.location.at_say(caller, spoof)
        caller.location.msg_contents('|m%s|n' % spoof)


class CmdSay(MuxCommand):
    """
    Speak as your character.
    Usage:
      say <message>
    Switch:
      /o or /ooc - Out-of-character to the room.
      /v or /verb - set default say verb.
    """

    key = "say"
    aliases = ['"', "'"]
    locks = "cmd:all()"

    def func(self):
        "Run the say command"

        caller = self.caller

        if not self.args:
            caller.execute_cmd("help say")
            return

        if 'v' in self.switches or 'verb' in self.switches:
            caller.attributes.add('say-verb', self.args)
            emit_string = '|c%s|n warms up vocally with "%s|n"' % (caller.name, self.args)
            caller.location.msg_contents(emit_string)
            return

        if 'q' in self.switches or 'quote' in self.switches:
            caller.quote = self.args # Not yet implemented.
            return

        speech = caller.location.at_say(caller, self.args) # Notify NPCs and listeners.

        if 'o' in self.switches or 'ooc' in self.switches:
            emit_string = '[OOC]|n |c%s|n says, "%s"' % (caller.name, speech)
        else:
            verb = caller.attributes.get('say-verb') if caller.attributes.has('say-verb') else 'says'
            emit_string = '|c%s|n %s, "%s|n"' % (caller.name, verb, speech)
        caller.location.msg_contents(emit_string)


class CmdVerb(MuxPlayerCommand):
    """
    Set a verb lock.
    Usage:
      @verb <object>
    """

    key = "@verb"
    locks = "cmd:all()"

    def func(self):
        """
        Here's where the @verbing magic happens.
        """

        my_char = self.caller.get_puppet(self.session)
        args = self.args
        if my_char and my_char.location:
            obj_list = my_char.search(args, location=[my_char, my_char.location]) if args else my_char
            if obj_list:
                obj = obj_list
                verb_msg = "Verbs of %s: " % obj_list
            else:
                obj = my_char
                verb_msg = "Verbs on you: "
            verbs = obj.locks
            collector = ''
            for verb in ("%s" % verbs).split(';'):
                element = verb.split(':')[0]
                name = element[2:] if element[:2] == 'v-' else element
                # obj lock checked against character
                if obj.access(my_char, element):
                    collector += "|g%s " % name
                else:
                    collector += "|r%s " % name
            collector = collector + '|n'
            my_char.msg(verb_msg + "%s" % collector)


class CmdWho(MuxPlayerCommand):
    """
    list who is currently online
    Usage:
      who
    Shows who is currently online. Use the /f switch to see
    character locations, and more info for those with permissions.
    """
    key = "who"
    aliases = "ws"
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
        if 'f' in self.switches or 'full' in self.switches:
            if show_session_data:
                # privileged info - who/f by wizard or immortal
                table = prettytable.PrettyTable(["|wPlayer Name",
                                                 "|wOn for",
                                                 "|wIdle",
                                                 "|wCharacter",
                                                 "|wRoom",
                                                 "|wCmds",
                                                 "|wProtocol",
                                                 "|wHost"])
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
                table = prettytable.PrettyTable(["|wCharacter", "|wOn for", "|wIdle", "|wLocation"])
                for session in session_list:
                    if not session.logged_in:
                        continue
                    delta_cmd = time.time() - session.cmd_last_visible
                    delta_conn = time.time() - session.conn_time
                    character = session.get_puppet()
                    location = character.location.key if character and character.location else "None"
                    table.add_row([utils.crop(character.key if character else "- Unknown -", width=25),
                                   utils.time_format(delta_conn, 0),
                                   utils.time_format(delta_cmd, 1),
                                   utils.crop(location, width=25)])
        else:
            if 's' in self.switches or 'species' in self.switches or self.cmdstring == 'ws':
                table = prettytable.PrettyTable(["|wCharacter", "|wOn for", "|wIdle", "|wSpecies"])
                for session in session_list:
                    character = session.get_puppet()
                    my_character = self.caller.get_puppet(self.session)
                    if not session.logged_in or character.location != my_character.location:
                        continue
                    delta_cmd = time.time() - session.cmd_last_visible
                    delta_conn = time.time() - session.conn_time
                    character = session.get_puppet()
                    species = character.attributes.get('species', default='- None -')
                    table.add_row([utils.crop(character.key if character else "- Unknown -", width=25),
                                   utils.time_format(delta_conn, 0),
                                   utils.time_format(delta_cmd, 1),
                                   utils.crop(species, width=25)])
            else:
                # unprivileged info - who
                table = prettytable.PrettyTable(["|wCharacter", "|wOn for", "|wIdle"])
                for session in session_list:
                    if not session.logged_in:
                        continue
                    delta_cmd = time.time() - session.cmd_last_visible
                    delta_conn = time.time() - session.conn_time
                    character = session.get_puppet()
                    table.add_row([utils.crop(character.key if character else "- Unknown -", width=25),
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
    Switch:
      /o or /ooc - Out-of-character to the room.

    Example:
      > pose is standing by the tree, smiling.
      Rulan is standing by the tree, smiling.

      > pose get anvil::puts his back into it.
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
        
        Also parse for a verb and optional noun, which if blank is assumed
        to be the character, in a power pose of the form:
        verb noun::pose
        verb::pose
        
        verb noun::
        verb::

        or using the try command, just
        verb noun
        verb
        """

        super(CmdPose, self).parse()
        args = unicode(self.args)
        caller = self.caller

        if not self.args:
            caller.execute_cmd("help pose")
            return

        self.verb = None
        self.obj = None
        non_space_chars = ["®", "©", "°", "·", "~", "@", "-", "'", "’", ",", ";", ":", ".", "?", "!", "…"]

        if 'magnet' in self.switches or 'm' in self.switches:
            caller.msg("Pose magnet glyphs are %s." % non_space_chars)

        if self.cmdstring == 'try':
            args += '::'
        if len(args.split('::')) > 1:
            verbnoun, pose = args.split('::', 1)
            if 0 < len(verbnoun.split()) <= 2:
                args = pose
                if len(verbnoun.split()) == 2:
                    self.verb, noun = verbnoun.split()
                else:
                    self.verb = verbnoun.strip()
                    noun = 'me'
                self.obj = caller.search(noun, location=[caller, caller.location])
        if args and not args[0] in non_space_chars:
            args = " %s" % args.strip()
        self.args = args

    def func(self):
        "Hook function"

        caller = self.caller
        if self.args:
            if 'o' in self.switches or 'ooc' in self.switches:
                msg = '[OOC]|n |c%s|n%s' % (caller.name, self.args)
            else:
                msg = "|c%s|n%s" % (caller.name, self.args)
            caller.location.msg_contents(msg)

#    def at_post_command(self):
#        "Verb response here."

#        super(CmdPose, self).at_post_command()
        if self.obj:
            obj = self.obj
            verb = self.verb
            caller = self.caller
            if obj.access(caller, verb):
                if verb == 'get' or verb == 'drop':
                    caller.execute_cmd(verb + ' ' + obj.name)
                else:
                    msg = "|g%s|n is able to %s %s." % (caller.name, verb, obj.name)
                    caller.location.msg_contents(msg)
            else:
                if self.obj.locks.get(verb): # Test to see if a lock string exists.
                    msg = "|r%s|n fails to %s %s." % (caller.name, verb, obj.name)
                    caller.location.msg_contents(msg, exclude=caller)
                    caller.msg("You failed to %s %s." % (verb, obj.name))
                else:
                    caller.msg("It is not possible to %s %s." % (verb, obj.name))
