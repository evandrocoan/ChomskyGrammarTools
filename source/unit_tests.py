#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import lark

import unittest
from collections import OrderedDict

from grammar.grammar import ChomskyGrammar

from grammar.utilities import wrap_text
from grammar.utilities import getCleanSpaces
from grammar.utilities import dictionary_to_string

from grammar.symbols import Terminal
from grammar.symbols import NonTerminal

from grammar.production import Production
from grammar.lockable_type import LockableType
from grammar.tree_transformer import ChomskyGrammarTreeTransformer

from grammar.testing_utilities import TestingUtilities


class TestChomskyGrammar(TestingUtilities):
    """
        Tests the Grammar class.
    """

    def tearDown(self):
        LockableType._USE_STRING = True

    def test_grammarProductionsDictionaryKeyError(self):
        LockableType._USE_STRING = False

        non_terminal_A = NonTerminal( 'A' )
        production_A = Production( 0, [non_terminal_A], True )

        # print( "production_A:", hash( production_A ) )
        # print( "non_terminal_A:", hash( non_terminal_A ) )

        dictionary = {}
        dictionary[production_A] = 'cow'

        self.assertTextEqual(
        """
            cow
        """, dictionary[non_terminal_A] )

    def test_grammarChapter5FirstExample1(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> Ab | A Bc
            B -> bB | Ad | &
            A -> aA | &
        """ ) )
        first = firstGrammar.first()

        self.assertTextEqual(
        """
            + A: & a
            + B: & a b d
            + S: a b c d
        """, dictionary_to_string( first ) )

    def test_grammarChapter5FollowExample1IsTheSameAsFirstExample2(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> A B C
            A -> aA | &
            B -> bB | A Cd
            C -> cC | &
        """ ) )
        first = firstGrammar.first()

        self.assertTextEqual(
        """
            + A: & a
            + B: a b c d
            + C: & c
            + S: a b c d
        """, dictionary_to_string( first ) )

    def test_grammarChapter5FollowExample2(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            E  -> T E'
            E' -> + T E' | &
            T  -> F T'
            T' -> * F T' | &
            F  -> ( E ) | id
        """ ) )
        first = firstGrammar.first()

        self.assertTextEqual(
        """
            +  E: ( id
            + E': & +
            +  F: ( id
            +  T: ( id
            + T': & *
        """, dictionary_to_string( first ) )

    def test_grammarChapter5FollowExample4(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> A C | C e B | B a
            A -> a A | B C
            C -> c C | &
            B -> b B | A B | &
        """ ) )
        # sys.setrecursionlimit( 2000 )
        first = firstGrammar.first()

        self.assertTextEqual(
        """
            + A: & a b c
            + B: & a b c
            + C: & c
            + S: & a b c e
        """, dictionary_to_string( first ) )

    def test_grammarSingleAmbiguityCase(self):
        firstGrammar = ChomskyGrammar.parse( wrap_text(
        """
            S -> S S | &
        """ ) )

        self.assertTextEqual(
        """
            + productions
            +   non_terminal_start
            +     non_terminal  S
            +   space
            +   non_terminals
            +     production
            +       space
            +       non_terminal  S
            +       space
            +       non_terminal  S
            +       space
            +     production
            +       space
            +       epsilon
        """, firstGrammar.pretty() )

    def test_grammarInvalidNonTerminalException(self):

        with self.assertRaisesRegex( RuntimeError, "Invalid Non Terminal `D` added to the grammar" ):
            firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
            """
                S -> Ab | A Dc
                B -> bB | Ad | &
                A -> aA | &
            """ ) )
            firstGrammar.assure_existing_symbols()

    def test_grammarTransformationTreeParsingParenStarPlusSymbols(self):
        LockableType._USE_STRING = False

        firstGrammar = ChomskyGrammar.parse( wrap_text(
        r"""
            E  -> T E'
            E' -> + T E' | &
            T  -> F T'
            T' -> * F T'
            F  -> ( E ) | id
        """ ) )
        firstGrammar = ChomskyGrammarTreeTransformer().transform( firstGrammar )

        self.assertTextEqual(
        r"""
            + Tree(productions, [Production locked: False, symbols: [NonTerminal locked: True, str: E, sequence:
            + 0, has_epsilon: False, len: 1;], sequence: 0, has_epsilon: False;, Tree(space, []), Tree(space, []),
            + Tree(non_terminals, [Production locked: False, symbols: [NonTerminal locked: True, str: T, sequence:
            + 1, has_epsilon: False, len: 1;, NonTerminal locked: True, str: E', sequence: 2, has_epsilon: False,
            + len: 1;], sequence: 2, has_epsilon: False;]), Tree(end_symbol, [Tree(new_line, [Token(NEWLINE,
            + '\n')])]), Production locked: False, symbols: [NonTerminal locked: True, str: E', sequence: 0,
            + has_epsilon: False, len: 1;], sequence: 0, has_epsilon: False;, Tree(space, []), Tree(non_terminals,
            + [Production locked: False, symbols: [Terminal locked: True, str: +, sequence: 1, has_epsilon: False,
            + len: 1;, NonTerminal locked: True, str: T, sequence: 2, has_epsilon: False, len: 1;, NonTerminal
            + locked: True, str: E', sequence: 3, has_epsilon: False, len: 1;], sequence: 3, has_epsilon: False;,
            + Production locked: False, symbols: [Terminal locked: True, str: &, sequence: 1, has_epsilon: True,
            + len: 0;], sequence: 1, has_epsilon: True;]), Tree(end_symbol, [Tree(new_line, [Token(NEWLINE,
            + '\n')])]), Production locked: False, symbols: [NonTerminal locked: True, str: T, sequence: 0,
            + has_epsilon: False, len: 1;], sequence: 0, has_epsilon: False;, Tree(space, []), Tree(space, []),
            + Tree(non_terminals, [Production locked: False, symbols: [NonTerminal locked: True, str: F, sequence:
            + 1, has_epsilon: False, len: 1;, NonTerminal locked: True, str: T', sequence: 2, has_epsilon: False,
            + len: 1;], sequence: 2, has_epsilon: False;]), Tree(end_symbol, [Tree(new_line, [Token(NEWLINE,
            + '\n')])]), Production locked: False, symbols: [NonTerminal locked: True, str: T', sequence: 0,
            + has_epsilon: False, len: 1;], sequence: 0, has_epsilon: False;, Tree(space, []), Tree(non_terminals,
            + [Production locked: False, symbols: [Terminal locked: True, str: *, sequence: 1, has_epsilon: False,
            + len: 1;, NonTerminal locked: True, str: F, sequence: 2, has_epsilon: False, len: 1;, NonTerminal
            + locked: True, str: T', sequence: 3, has_epsilon: False, len: 1;], sequence: 3, has_epsilon:
            + False;]), Tree(end_symbol, [Tree(new_line, [Token(NEWLINE, '\n')])]), Production locked: False,
            + symbols: [NonTerminal locked: True, str: F, sequence: 0, has_epsilon: False, len: 1;], sequence: 0,
            + has_epsilon: False;, Tree(space, []), Tree(space, []), Tree(non_terminals, [Production locked:
            + False, symbols: [Terminal locked: True, str: (, sequence: 1, has_epsilon: False, len: 1;,
            + NonTerminal locked: True, str: E, sequence: 2, has_epsilon: False, len: 1;, Terminal locked: True,
            + str: ), sequence: 3, has_epsilon: False, len: 1;], sequence: 3, has_epsilon: False;, Production
            + locked: False, symbols: [Terminal locked: True, str: id, sequence: 1, has_epsilon: False, len: 2;],
            + sequence: 1, has_epsilon: False;])])
        """, wrap_text( firstGrammar, wrap=100 ) )

    def test_grammarTransformationParsingComplexSingleProduction(self):
        LockableType._USE_STRING = False

        firstGrammar = ChomskyGrammar.parse( wrap_text(
        """
            S -> aABbbCC1aAbA BC | ba | c
        """ ) )
        firstGrammar = ChomskyGrammarTreeTransformer().transform( firstGrammar )

        self.assertTextEqual(
        """
            + productions
            +   S
            +   space
            +   non_terminals
            +     a AB bb CC 1a A b A BC
            +     ba
            +     c
        """, firstGrammar.pretty() )

        self.assertTextEqual( wrap_text(
        r"""
            + Tree(productions, [Production locked: False, symbols: [NonTerminal locked: True, str: S, sequence:
            + 0, has_epsilon: False, len: 1;], sequence: 0, has_epsilon: False;, Tree(space, []),
            + Tree(non_terminals, [Production locked: False, symbols: [Terminal locked: True, str: a, sequence: 1,
            + has_epsilon: False, len: 1;, NonTerminal locked: True, str: AB, sequence: 2, has_epsilon: False,
            + len: 1;, Terminal locked: True, str: bb, sequence: 3, has_epsilon: False, len: 2;, NonTerminal
            + locked: True, str: CC, sequence: 4, has_epsilon: False, len: 1;, Terminal locked: True, str: 1a,
            + sequence: 5, has_epsilon: False, len: 2;, NonTerminal locked: True, str: A, sequence: 6,
            + has_epsilon: False, len: 1;, Terminal locked: True, str: b, sequence: 7, has_epsilon: False, len:
            + 1;, NonTerminal locked: True, str: A, sequence: 8, has_epsilon: False, len: 1;, NonTerminal locked:
            + True, str: BC, sequence: 9, has_epsilon: False, len: 1;], sequence: 9, has_epsilon: False;,
            + Production locked: False, symbols: [Terminal locked: True, str: ba, sequence: 1, has_epsilon: False,
            + len: 2;], sequence: 1, has_epsilon: False;, Production locked: False, symbols: [Terminal locked:
            + True, str: c, sequence: 1, has_epsilon: False, len: 1;], sequence: 1, has_epsilon: False;])])
        """, trim_spaces=True ), wrap_text( str( firstGrammar ), wrap=100 ) )

    def test_grammarTreeParsingComplexSingleProduction(self):
        firstGrammar = ChomskyGrammar.parse( wrap_text(
        """
            S -> aABbbCC1aAbA BC | ba | c
        """ ) )

        self.assertTextEqual(
        """
            + productions
            +   non_terminal_start
            +     non_terminal  S
            +   space
            +   non_terminals
            +     production
            +       space
            +       terminal  a
            +       non_terminal
            +         A
            +         B
            +       terminal
            +         b
            +         b
            +       non_terminal
            +         C
            +         C
            +       terminal
            +         1
            +         a
            +       non_terminal  A
            +       terminal  b
            +       non_terminal  A
            +       space
            +       non_terminal
            +         B
            +         C
            +       space
            +     production
            +       space
            +       terminal
            +         b
            +         a
            +       space
            +     production
            +       space
            +       terminal  c
        """, firstGrammar.pretty() )

    def test_grammarInputParsingComplexSingleProduction(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines(
        """
            S  -> aABbbCC1aAbA BC | ba | c
            A  -> &
            AB -> &
            BC -> &
            CC -> &
        """ )

        self.assertTextEqual(
        """
            +  S -> a AB bb CC 1a A b A BC | ba | c
            +  A -> &
            + AB -> &
            + BC -> &
            + CC -> &
        """, str( firstGrammar ) )

    def test_grammarInputParsingSymbolMerging(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines(
        """
            S -> a b cd | AccD | Ac cD
            A -> &
            D -> &
        """ )

        self.assertTextEqual(
        """
            + S -> A cc D | abcd
            + A -> &
            + D -> &
        """, str( firstGrammar ) )

    def test_grammarTreeParsingABandB(self):
        firstGrammar = ChomskyGrammar.parse( wrap_text(
        """
            S -> aABb BC | b
        """ ) )

        self.assertTextEqual(
        """
            + productions
            +   non_terminal_start
            +     non_terminal  S
            +   space
            +   non_terminals
            +     production
            +       space
            +       terminal  a
            +       non_terminal
            +         A
            +         B
            +       terminal  b
            +       space
            +       non_terminal
            +         B
            +         C
            +       space
            +     production
            +       space
            +       terminal  b
        """, firstGrammar.pretty() )

    def test_grammarInputParsingEmptyEpsilon(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines(
        """
             S ->
            SS -> S |
        """ )

        self.assertTextEqual(
        """
            +  S -> &
            + SS -> & | S
        """, str( firstGrammar ) )

    def test_grammarTreeParsingEmptyEpsilon(self):
        firstGrammar = ChomskyGrammar.parse( wrap_text(
        """
             S ->
            SS -> S |
        """ ) )

        self.assertTextEqual(
        """
            + productions
            +   space
            +   non_terminal_start
            +     non_terminal  S
            +   space
            +   non_terminals
            +     production
            +       epsilon
            +   end_symbol
            +     new_line
            +
            +   non_terminal_start
            +     non_terminal
            +       S
            +       S
            +   space
            +   non_terminals
            +     production
            +       space
            +       non_terminal  S
            +       space
            +     production
            +       epsilon
        """, firstGrammar.pretty() )

    def test_grammarInputParsingSSandEpsilon(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines(
        """
            S   -> SS SSS | &
            SS  -> &
            SSS -> &
        """ )

        self.assertTextEqual(
        """
            +   S -> & | SS SSS
            +  SS -> &
            + SSS -> &
        """, str( firstGrammar ) )

    def test_grammarTreeParsingSSandEpsilon(self):
        firstGrammar = ChomskyGrammar.parse(
        """
            S -> S SS | &
        """ )

        self.assertTextEqual(
        """
            + productions
            +   new_line
            +
            +   space
            +   space
            +   space
            +   space
            +   space
            +   space
            +   space
            +   space
            +   space
            +   space
            +   space
            +   space
            +   non_terminal_start
            +     non_terminal  S
            +   space
            +   non_terminals
            +     production
            +       space
            +       non_terminal  S
            +       space
            +       non_terminal
            +         S
            +         S
            +       space
            +     production
            +       space
            +       epsilon
            +   end_symbol
            +     new_line
            +
            +     space
            +     space
            +     space
            +     space
            +     space
            +     space
            +     space
            +     space
        """, firstGrammar.pretty() )

    # def test_grammarGenerateSentencesOfnAsSize5(self):
    #     firstGrammar = Grammar.load_from_text_lines(
    #     """
    #         A -> aA | a
    #     """ )
    #     generate_sentences = []
    #     firstGrammar.generate_sentences_of_size_n( 5, generate_sentences )

    #     self.assertTextEqual(
    #     """
    #         + ['a', 'aa', 'aaa', 'aaaa', 'aaaaa']
    #     """, str( generate_sentences ) )


if __name__ == "__main__":
    unittest.main()

