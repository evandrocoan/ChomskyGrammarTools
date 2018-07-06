#! /usr/bin/env python
# -*- coding: utf-8 -*-

import lark

_parser = lark.Lark( r"""
        grammar      : start_symbol "->" productions
        start_symbol : WHITE_SPACE* non_terminal WHITE_SPACE*

        productions : non_terminals "|" productions | non_terminals
        non_terminals  : WHITE_SPACE* non_terminal WHITE_SPACE* non_terminals | non_terminal

        non_terminal   : UPPER_CASE_LETTER non_terminal2
        ?non_terminal2 : UPPER_CASE_LETTER non_terminal2 | WHITE_SPACE | non_terminal3
        non_terminal3  : UPPER_CASE_LETTER2

        UPPER_CASE_LETTER  : /[A-ZÀ-Ö]/
        UPPER_CASE_LETTER2 : /[A-ZÀ-Ö]$/

        // Common definitions
        WHITE_SPACE : ( " " | /\t/ )
""", start='grammar', parser='earley', ambiguity="explicit" )

tree = _parser.parse( "S -> S SS AAA" )
print( tree.pretty() )

