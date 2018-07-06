#! /usr/bin/env python
# -*- coding: utf-8 -*-

import lark

_parser = lark.Lark( r"""
        grammar      : start_symbol "->" production
        start_symbol : WHITE_SPACE* production_symbols+

        production  : WHITE_SPACE* production_symbols+ "|" production
                    | WHITE_SPACE* production_symbols+

        production_symbols   : terminals_begin | non_terminals_begin
        terminal_symbols     : LOW_CASE_LETTER
        non_terminal_symbols : UPPER_CASE_LETTER | QUOTE | DIGIT

        non_terminals_begin : non_terminal_symbols non_terminals_end
        non_terminals_end   : non_terminal_symbols non_terminals_end | WHITE_SPACE+ | UPPER_CASE_LETTER2 | QUOTE2 | DIGIT2

        terminals_begin : terminal_symbols terminals_end
        terminals_end   : terminal_symbols terminals_end | WHITE_SPACE+ | LOW_CASE_LETTER2

        LOW_CASE_LETTER  : /[a-zØ-öø-ÿ]/
        LOW_CASE_LETTER2 : /[a-zØ-öø-ÿ]$/

        UPPER_CASE_LETTER  : /[A-ZÀ-Ö]/
        UPPER_CASE_LETTER2 : /[A-ZÀ-Ö]$/

        QUOTE  : "'"
        QUOTE2 : /'$/

        DIGIT  : "0".."9"
        DIGIT2 : /[0-9]$/

        CR        : /\r/
        LF        : /\n/
        NEWLINE   : (CR? LF)+

        // Common definitions
        WHITE_SPACE : ( " " | /\t/ )
""", start='grammar', parser='lalr' )
# """, start='grammar', parser='earley', ambiguity="explicit" )

tree = _parser.parse( "S -> a 1 | aa S1 a SS AAA  |  B  |  C  " )
print( tree.pretty() )

