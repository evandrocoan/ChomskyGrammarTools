#! /usr/bin/env python
# -*- coding: utf-8 -*-

import lark

_parser = lark.Lark( r"""
        productions : start_symbol "->" production_symbols

        production_symbols : WHITE_SPACE* token+ "|" production_symbols
                           | WHITE_SPACE* token+

        // Rename the start symbol, so when parsing the tree it is simple to find it
        start_symbol : WHITE_SPACE* token+

        token                : terminal_begin | non_terminal_begin
        terminal_symbols     : LOW_CASE_LETTER | DIGIT | EPSILON | signs | signs_extra | parens
        non_terminal_symbols : UPPER_CASE_LETTER | DIGIT | QUOTE

        terminal_begin : terminal_symbols terminal_end
        terminal_end   : terminal_symbols terminal_end
                        | LOW_CASE_LETTER2
                        | WHITE_SPACE+
                        | WHITE_SPACE+ new_line productions
                        | new_line productions

        non_terminal_begin : UPPER_CASE_LETTER non_terminal_end
        non_terminal_end   : non_terminal_symbols non_terminal_end
                            | QUOTE2
                            | DIGIT2
                            | UPPER_CASE_LETTER2
                            | WHITE_SPACE+
                            | WHITE_SPACE+ new_line productions
                            | new_line productions

        // https://stackoverflow.com/questions/20690499/concrete-javascript-regex-for-accented-characters-diacritics
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
        new_line  : (CR? LF)+

        // Tells the tree-builder to inline this branch if it has only one member
        ?signs    : MINUS |  PLUS | STAR | COMMA | COLON | EQUALS | SEMICOLON | SLASH | BACKSLASH | DOT
        SEMICOLON : ";"
        COMMA     : ","
        COLON     : ":"
        DOT       : "."
        EQUALS    : "="
        MINUS     : "-"
        STAR      : "*"
        PLUS      : "+"
        SLASH     : "/"
        BACKSLASH : "\\"

        ?signs_extra : QUESTION | DOUBLE_QUOTE | PERCENTAGE | DOLLAR | AT_SIGN | SHARP | EXCLAMATION | TICK | BACKTICK | CARET | TILDE
        SHARP        : "#"
        DOLLAR       : "$"
        QUESTION     : "?"
        AT_SIGN      : "@"
        TICK         : "´"
        CARET        : "^"
        TILDE        : "~"
        BACKTICK     : "`"
        PERCENTAGE   : "%"
        EXCLAMATION  : "!"
        DOUBLE_QUOTE : "\""

        ?parens       : OPEN_PAREN | CLOSE_PAREN | OPEN_BRACKET | CLOSE_BRACKET | OPEN_BRACE | CLOSE_BRACE
        OPEN_BRACKET  : "["
        CLOSE_BRACKET : "]"
        OPEN_BRACE    : "{"
        CLOSE_BRACE   : "}"
        OPEN_PAREN    : "("
        CLOSE_PAREN   : ")"

        // Common definitions
        EPSILON     : "&"+
        WHITE_SPACE : ( " " | /\t/ )
""", start='productions', parser='lalr' )
# """, start='productions', parser='earley', ambiguity="explicit" )

tree = _parser.parse( "S -> a & 1)\" | aa S1 a SS AAA  |  B  |  C  a\n B -> BB\nC -> CC" )
print( tree.pretty() )

