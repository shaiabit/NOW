from evennia import default_cmds
from evennia.utils import prettytable

class CmdInventory(default_cmds.MuxCommand):
    """
    view inventory
    Usage:
      inventory
      inv
    Shows your inventory: carrying, wielding, wearing, obscuring.
    """

    key = "inventory"
    aliases = ["inv", "i"]
    locks = "cmd:all()"

    def func(self):
        "check inventory"
        items = self.caller.contents
        if not items:
            string = "You are not carrying anything."
        else:
            table = prettytable.PrettyTable(["name", "desc_brief"])
            table.header = False
            table.border = False
            for item in items:
                imass = item.get_mass() if hasattr(item, 'get_mass') else '- unknown -'
                second = imass if 'weight' in self.switches else item.db.desc_brief
                table.add_row(["%s" % item.mxp_name(self.caller.sessions, '@verb #%s' % item.id) if hasattr(item, "mxp_name") \
                    else item.get_display_name(self.caller.sessions), second and second or ""])
            imass = self.caller.get_mass() if hasattr(item, 'get_mass') else '- unknown -'
            string = "|wYou and what you carry total %s g:\n%s" % (imass, table)
        self.caller.msg(string)

