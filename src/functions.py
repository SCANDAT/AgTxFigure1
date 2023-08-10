#functions.py
import numpy as np

def format_pvalue(p):
    if p >= 0.01:
        return "{:.2f}".format(p)
    else:
        return np.format_float_scientific(p, precision=2)