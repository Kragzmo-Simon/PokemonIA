# -*- coding: utf-8 -*-
"""
Created on Mon Dec  2 02:38:32 2019

@author: admin
"""

from .room import Move


new_attaque=Move('Flamethrower')
new_attaque.update_smogon_data('Fire','Special','90','100','The target is scorched with an intense blast of fire. This may also leave the target with a burn. ')
print(new_attaque.get_name+new_attaque.get_power)