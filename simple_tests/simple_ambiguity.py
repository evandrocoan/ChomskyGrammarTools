#! /usr/bin/env python
# -*- coding: utf-8 -*-

import lark

_parser = lark.Lark( r"""
    productions   : new_line* non_terminal_start "->" non_terminals end_symbol?
    non_terminals : production
    production    : ( ( epsilon | terminal | non_terminal )+ space )+

    epsilon         : "&"
    end_symbol      : new_line
    terminal        : LCASE_LETTER
    non_terminal    : UCASE_LETTER
    new_line        : NEWLINE
    quote           : "'"
    dash_phi_hyphen : "-"
    space           : " "

    non_terminal_start : non_terminal

    %import common.UCASE_LETTER
    %import common.LCASE_LETTER
    %import common.NEWLINE
    %import common.WS_INLINE
    %ignore WS_INLINE
""", start='productions', parser='earley', ambiguity="explicit" )

tree = _parser.parse( "S -> S S " )
print( tree.pretty() )

# _ambig
#   productions
#     non_terminal_start
#       non_terminal  S
#     non_terminals
#       production
#         non_terminal    S
#         non_terminal    S
#         space
#   productions
#     non_terminal_start
#       non_terminal  S
#     non_terminals
#       production
#         non_terminal    S
#         space
#         non_terminal    S
#         space
