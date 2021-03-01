# -*- coding: utf-8 -*-
"""
Created on Sat Feb 27 23:20:37 2021

@author: ljh119
"""

def final_well(n):
    """Determines well containing the final sample from sample number.
    
    """
    letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    row = letters[n%8-1]
    col = (n-1)//8 + 1

    return row + str(col)