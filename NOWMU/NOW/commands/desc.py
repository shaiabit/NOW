from evennia import default_cmds
from evennia.utils.eveditor import EvEditor

def _desc_load(caller):
    return caller.db.evmenu_target.db.desc or ""

def _desc_save(caller, buf):
    """
    Save line buffer to the desc prop. This should
    return True if successful and also report its status to the user.
    """
    caller.db.evmenu_target.db.desc = buf
    caller.msg("Saved.")
    return True

def _desc_quit(caller):
    caller.attributes.remove("evmenu_target")
    caller.msg("Exited editor.")

class CmdDesc(default_cmds.MuxCommand):
    """
    describe yourself
    Usage:
      desc <description>

    Switches:
      edit - Open up a line editor for more advanced editing.

    Add a description to your character, visible to characters who look at you.
    """
    key = "desc"
    locks = "cmd:all()"
    arg_regex = r"^/|\s|$"

    def edit_handler(self):
        if self.args:
            self.msg("|rYou may specify a description, or use the edit switch, "
                     "but not both.|n")
            return
        else:
            obj = self.caller

        def load(obj):
            return obj.db.evmenu_target.db.desc or ''

        def save(obj, buf):
            """
            Save line buffer to the desc prop. This should return True
            if successful and also report its status to the user.
            """
            obj.db.evmenu_target.db.desc = buf
            obj.msg("Saved.")
            return True

        def quit(obj):
            obj.attributes.remove("evmenu_target")
            obj.msg("Exited editor.")

        self.caller.db.evmenu_target = obj  # launch the editor
        EvEditor(obj, loadfunc=load, savefunc=save, quitfunc=quit, key="desc", persistent=True)
        return

    def func(self):
        "add the description"

        if 'edit' in self.switches:
            self.edit_handler()
            return

        if not self.args:
            self.caller.msg("You must supply a description to describe yourself.")
            return

        self.caller.db.desc = self.args.strip()
        self.caller.msg("You set your description.")
