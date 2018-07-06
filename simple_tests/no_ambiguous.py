#! /usr/bin/env python
# -*- coding: utf-8 -*-

import lark

_parser = lark.Lark( r"""
        grammar : ( start_symbol "->" productions new_line+ )* ( start_symbol "->" productions )

        // Rename the start symbol, so when parsing the tree it is simple to find it
        start_symbol : tokens
        productions  : tokens ( "|" tokens )*

        token  : terminals | non_terminals
        tokens : SPACES* ( token+ SPACES+ )* token*

        terminals     : ( LOWER_CASE_LETTER | EPSILON | DIGIT | signs | signs_extra | parens )+
        non_terminals : UPPER_CASE_LETTER ( UPPER_CASE_LETTER | DIGIT | QUOTE )*

        // https://stackoverflow.com/questions/20690499/concrete-javascript-regex-for-accented-characters-diacritics
        UPPER_CASE_LETTER : /[A-ZÀ-Ö]/
        LOWER_CASE_LETTER : /[a-zØ-öø-ÿ]/

        // Common definitions
        EPSILON  : "&"
        QUOTE    : "'"
        DIGIT    : "0".."9"
        SPACES   : ( " " | /\t/ )
        CR       : /\r/
        LF       : /\n/
        new_line : ( CR? LF )+

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
""", start='grammar', parser='lalr' )
# """, start='grammar', parser='earley', ambiguity="explicit" )

tree = _parser.parse( "S -> S SS | &" )
# tree = _parser.parse( "S -> a & 1)\" | aa S1 a SS AAA  |  B  |  C  a\nB -> BB\nC -> CC" )
# tree = _parser.parse( "S SS -> AA BBBB | EEE\nC -> CC\nD-> DD DDD" )
print( tree.pretty() )

