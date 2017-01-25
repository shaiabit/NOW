# -*- coding: UTF-8 -*-
from commands.command import MuxCommand
from evennia.utils import evtable
from world.helpers import mass_unit


class CmdInventory(MuxCommand):
    """
    Shows your inventory: carrying, wielding, wearing, obscuring.
    Usage:
      inventory
    Switches:
    /weight   shows inventory item weight and carry total
    """
    key = 'inventory'
    aliases = ['inv', 'i']
    locks = 'cmd:all()'
    arg_regex = r'^/|\s|$'

    def func(self):
        """check inventory"""
        you = self.character
        items = you.contents
        mass = you.traits.mass.actual if you.traits.mass else 0
        if not items:
            if mass:
                string = 'You (%s) are not carrying anything.' % mass_unit(mass)
            else:
                string = 'You are not carrying anything.'
        else:
            table = evtable.EvTable(border='header')
            for item in items:
                i_mass = mass_unit(item.get_mass()) if hasattr(item, 'get_mass') else 0
                second = '(|y%s|n) ' % i_mass if 'weight' in self.switches else ''
                second += item.db.desc_brief or item.db.desc or ''
                table.add_row('%s' % item.get_display_name(you.sessions, mxp=('sense %s' % item.key)),
                              second or '')
            my_mass, my_total_mass = [mass, you.get_mass() if hasattr(you, 'get_mass') else 0]
            string = "|wYou (%s) and what you carry (%s) total |y%s|n:\n%s" %\
                     (mass_unit(mass), mass_unit(my_total_mass - my_mass),
                      mass_unit(my_total_mass), table)
        you.msg(string)
