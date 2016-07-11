from random import *

def half(accessing_obj, accessed_obj, *args, **kwargs):
    if random() > 0.5:
	return False
    return True

def roll(accessing_obj, accessed_obj, *args, **kwargs):
    return True if args else False