"""
Helpers

Methods that are helpful to have in a module.

"""

def make_bar(value, maximum, length, gradient):
    """
    Make a bar of length, of color value along the gradient.
    """

    maximum = float(maximum)
    length = float(length)
    value = min(float(value), maximum)
    barcolor = gradient[max(0, (int(round((value / maximum) * len(gradient))) - 1))]
    rounded_percent = int(min(round((value / maximum) * length), length - 1))
    barstring = (("{:<%i}" % int(length)).format("%i / %i" % (int(value), int(maximum))))
    barstring = ("|555" + barcolor + barstring[:rounded_percent] + '|[011' + barstring[rounded_percent:])
    return barstring[:int(length) + 13] + "|n"
