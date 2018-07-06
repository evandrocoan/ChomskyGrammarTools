#! /usr/bin/env python
# -*- coding: utf-8 -*-

import lark

_parser = lark.Lark( r"""
        grammar      : start_symbol "->" production
        start_symbol : WHITE_SPACE* symbols

        production  : WHITE_SPACE* symbols "|" production
                    | WHITE_SPACE* symbols

        symbols : non_terminal symbols | non_terminal

        non_terminal   : UPPER_CASE_LETTER non_terminal2
        non_terminal2  : UPPER_CASE_LETTER non_terminal2 | non_terminal3
        non_terminal3  : white_space+ | UPPER_CASE_LETTER2

        UPPER_CASE_LETTER  : /[A-ZÀ-Ö]/
        UPPER_CASE_LETTER2 : /[A-ZÀ-Ö]$/

        // Common definitions
        WHITE_SPACE : ( " " | /\t/ )
        ?white_space : WHITE_SPACE
""", start='grammar', parser='earley', ambiguity="explicit" )
# """, start='grammar', parser='lalr' )

tree = _parser.parse( "S -> S SS AAA  |  B  |  C  " )
print( tree.pretty() )

