"""
Command sets

All commands in the game must be grouped in a cmdset.  A given command
can be part of any number of cmdsets and cmdsets can be added/removed
and merged onto entities at runtime.

To create new commands to populate the cmdset, see
`commands/command.py`.

This module wraps the default command sets of Evennia; overloads them
to add/remove commands from the default lineup. You can create your
own cmdsets by inheriting from them or directly from `evennia.CmdSet`.
"""

from evennia import default_cmds

#[Traversal of path-exits]
from typeclasses.exits import CmdStop, CmdContinue, CmdBack, CmdSetSpeed

#[commands modules]
from commands import prelogin
from commands import exitdirections
from commands import desc
from commands.desc import CmdDesc
from commands.inventory import CmdInventory
from commands.teleport import CmdTeleport
from commands.home import CmdHome
#from commands import destroy # Not ready for testing.
from commands.command import CmdLook, CmdQuit, CmdPose, CmdSay, CmdWho, CmdVerb, CmdForge
from commands.command import CmdOoc, CmdSpoof, CmdAccess, CmdChannels, CmdAbout
# from commands.command import CmdOoc, CmdSpoof, CmdAccess, CmdChannels, CmdChannelWizard, CmdSysinfo


class CharacterCmdSet(default_cmds.CharacterCmdSet):
    """
    The `CharacterCmdSet` contains general in-game commands available to
    in-world Character objects. It is merged with the `PlayerCmdSet` when
    a Player puppets a Character.
    """
    key = "DefaultCharacter"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """

        super(CharacterCmdSet, self).at_cmdset_creation()
        # any commands you add below will overload the default ones.
        self.remove(default_cmds.CmdGet)
        self.remove(default_cmds.CmdDrop)
        self.remove(default_cmds.CmdAbout)
        self.remove(default_cmds.CmdAccess)
        self.remove(default_cmds.CmdDestroy) # Need an alternate destroy method
        self.remove(default_cmds.CmdTeleport) # Teleport that costs and has conditions.
# [...]
        self.add(CmdSay)
        self.add(CmdOoc)
        self.add(CmdHome)
        self.add(CmdLook)
        self.add(CmdDesc)
        self.add(CmdPose)
        self.add(CmdVerb)
        self.add(CmdSpoof)
        self.add(CmdTeleport)
        self.add(CmdInventory)
# [...]
        self.add(CmdStop)
        self.add(CmdBack)
        self.add(CmdSetSpeed)
        self.add(CmdContinue)
# [...]
        self.add(exitdirections.CmdExitNorth())
        self.add(exitdirections.CmdExitSouth())
        self.add(exitdirections.CmdExitEast())
        self.add(exitdirections.CmdExitWest())
        self.add(exitdirections.CmdExitNortheast())
        self.add(exitdirections.CmdExitNorthwest())
        self.add(exitdirections.CmdExitSoutheast())
        self.add(exitdirections.CmdExitSouthwest())


class PlayerCmdSet(default_cmds.PlayerCmdSet):
    """
    This is the cmdset available to the Player at all times. It is
    combined with the `CharacterCmdSet` when the Player puppets a
    Character. It holds game-account-specific commands, channel
    commands, etc.
    """
    key = "DefaultPlayer"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super(PlayerCmdSet, self).at_cmdset_creation()
        # any commands you add below will overload the default ones.
        self.remove(default_cmds.CmdCWho)
        self.remove(default_cmds.CmdCBoot)
        self.remove(default_cmds.CmdPage)
        self.remove(default_cmds.CmdCdesc)
        self.remove(default_cmds.CmdClock)
        self.remove(default_cmds.CmdCemit)
        self.remove(default_cmds.CmdAddCom)
        self.remove(default_cmds.CmdDelCom)
        self.remove(default_cmds.CmdAllCom)
        self.remove(default_cmds.CmdCdestroy)
        self.remove(default_cmds.CmdChannelCreate)
        self.add(CmdWho)
        self.add(CmdQuit)
        self.add(CmdAbout)
        self.add(CmdAccess)
        self.add(CmdChannels)
        # self.add(CmdForge) # TODO: Make this a verb, along with "quench" and place on forge room.
        # self.add(CmdChannelWizard) # TODO: Too dangerous to add without testing.


class UnloggedinCmdSet(default_cmds.UnloggedinCmdSet):
    """
    Command set available to the Session before being logged in.  This
    holds commands like creating a new account, logging in, etc.
    """
    key = "DefaultUnloggedin"

    def at_cmdset_creation(self):
        """
        Populates the cmdset
        """
        super(UnloggedinCmdSet, self).at_cmdset_creation()
        # any commands you add below will overload the default ones.
        self.add(prelogin.CmdWhoUs())


class SessionCmdSet(default_cmds.SessionCmdSet):
    """
    This cmdset is made available on Session level once logged in. It
    is empty by default.
    """
    key = "DefaultSession"

    def at_cmdset_creation(self):
        """
        This is the only method defined in a cmdset, called during
        its creation. It should populate the set with command instances.

        As and example we just add the empty base `Command` object.
        It prints some info.
        """
        super(SessionCmdSet, self).at_cmdset_creation()
        # any commands you add below will overload the default ones.
