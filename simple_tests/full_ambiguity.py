#! /usr/bin/env python
# -*- coding: utf-8 -*-

import lark

_parser = lark.Lark( r"""
    productions   : new_line* ( non_terminal_start "->" non_terminals end_symbol )* non_terminal_start "->" non_terminals end_symbol?
    non_terminals : production ( "|" production )*
    production    : ( non_terminal? ( space+ | epsilon | terminal ) )*

    // Forces them to appear in the tree as branches
    epsilon         : "&"+
    end_symbol      : ( ";" | new_line )+
    terminal        : ( SIGNED_NUMBER | LCASE_LETTER | dash_phi_hyphen )+
    non_terminal    : UCASE_LETTER ( UCASE_LETTER | DIGIT | quote )*
    new_line        : NEWLINE
    quote           : "'"
    dash_phi_hyphen : "-"
    space           : " "

    // Rename the start symbol, so when parsing the tree it is simple to find it
    non_terminal_start : non_terminal

    // Stops Lark from automatically filtering out these literals from the tree
    null   : "null"
    true   : "true"
    false  : "false"

    // Import common definitions
    %import common.INT
    %import common.DIGIT
    %import common.UCASE_LETTER
    %import common.LCASE_LETTER
    %import common.SIGNED_NUMBER
    %import common.NEWLINE
    %import common.WS_INLINE

    // Set to ignore white spaces
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
