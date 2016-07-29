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
        pass
