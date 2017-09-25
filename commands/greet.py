# -*- coding: UTF-8 -*-
from evennia.utils.evmenu import EvMenu

CONV = [['Say Hello', 'Well, hello there!  How are you this fine day?'],
        ['Ask about potions', 'You can buy potions of various effects in the potion shop below.'],
        ['Ask about reward fruits', 'You can earn up to 3 apples a day.'],
        ['Talk about weather', "Yes, it's quite foggy."]]
EvMenu(self.character, 'commands.greet', startnode='menu_start_node',
       cmd_on_exit=None, persistent=False, object=self.obj, conv=CONV)


def menu_start_node(caller):
    menu = caller.ndb._menutree
    obj, conv = menu.object, menu.conv
    text = obj.get_display_name(caller) + " greets you."
    options = ()
    for each in conv:
        options += ({'desc': each[0]},)
    options += ({"key": "_default", "goto": "conversation"},)
    return text, options


def conversation(caller, raw_string):
    menu = caller.ndb._menutree
    obj, conv = menu.object, menu.conv
    inp = raw_string.strip().lower()
    topics = {}
    for i, each in enumerate(conv):
        topics[str(i + 1)] = conv[i][1]
    if inp in topics.keys():
        text = topics[inp]
        options = ({'key': "_default", 'goto': 'conversation'})
    else:
        text = obj.get_display_name(caller) + " nods as you end the conversation."
        options = None
    return text, options
