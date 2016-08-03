# -*- coding: UTF-8 -*-
from builtins import range
from commands.command import MuxCommand
from evennia import CmdSet
from random import randint


class MyDieCmdSet(CmdSet):
    key = 'dice'

    def at_cmdset_creation(self):
        """Add command to the set - this set will be attached to the die object."""
        self.add(CmdMyDie())


class CmdMyDieDefault(MuxCommand):
    """Add command to the set - this set will be attached to the vehicle object (item or room)."""
    key = 'mydie'
    locks = 'cmd:all()'
    help_category = 'Game'
    player_caller = True

    def roll_dice(self, dicenum, dicetype, modifier=None, conditional=None, return_tuple=False):
        """many sided-dice roller"""
        dice_num = int(dicenum)
        dice_type = int(dicetype)
        rolls = tuple([randint(1, dice_type) for roll in range(dice_num)])
        result = sum(rolls)
        if modifier:  # make sure to check types well before eval
            mod, mod_value = modifier
            if mod not in ('+', '-', '*', '/'):
                raise TypeError("Non-supported dice modifier: %s" % mod)
            mod_value = int(mod_value)  # for safety
            result = eval("%s %s %s" % (result, mod, mod_value))
        outcome, diff = None, None
        if conditional:  # make sure to check types well before eval
            cond, cond_value = conditional
            if cond not in ('>', '<', '>=', '<=', '!=', '=='):
                raise TypeError("Non-supported dice result conditional: %s" % conditional)
            cond_value = int(cond_value)  # for safety
            outcome = eval("%s %s %s" % (result, cond, cond_value))  # True/False
            diff = abs(result - cond_value)
        if return_tuple:
            return result, outcome, diff, rolls
        else:
            return outcome if conditional else result


class CmdMyDie(CmdMyDieDefault):
    """

    Usage: 
      Mydie [/switch] [diename] [=character names/face name]
    
    Switch: 
      hidden - tells the room what diename is being rolled but only show results to self.
      secret - don't inform the room about neither roll nor result only to self.
      new - Create a new die with name set this to [default]
      add - add a face to the die name
      rem - remove the last face [or named face] from the particular die
      show - show all die faces.
      n times - roll the particular die n times 
      n shows- - show n faces of the die (no repeats)

    """
    aliases = ['1', '2', '3']

    def func(self):
        """ """
        # cmd = self.cmdstring
        # opt = self.switches
        # args = self.args.strip()
        # lhs, rhs = [self.lhs, self.rhs]
        # char = self.character
        # where = self.obj
        # here = char.location
        # outside = where.location
        # player = self.player
        # 
        # Check if user has mydie set on them
        #   Inform them if they do not of how to add and inform of help
        #   Is this Usage of Die or Modification of Die
        #     Roll the die and store the results    
        #     Usage check for appropriate switches (ignore incorrect ones typos/new/add/rem <show) actually shows all the die faces>
        #     Send to affected parties per swtiches
        #  Does Die Exist
        #     Use switches to determine what to do, check for conflict no add & rem
        #     Inform use they have create diename they now need to /add faces
        pass
