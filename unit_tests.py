#! /usr/bin/env python
# -*- coding: utf-8 -*-

import lark
import unittest
from collections import OrderedDict

from source.grammar import ChomskyGrammar

from source.utilities import wrap_text
from source.utilities import getCleanSpaces
from source.utilities import sort_dictionary_lists

from source.utilities import Production
from source.utilities import Terminal
from source.utilities import NonTerminal

from source.utilities import LockableType
from source.utilities import ChomskyGrammarTreeTransformer

from source.testing_utilities import TestingUtilities


class TestChomskyGrammar(TestingUtilities):
    """
        Tests the Grammar class.
    """

    def test_grammarProductionsDictionaryKeyError(self):
        LockableType.USE_STRING = False

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

    def test_grammarFirstSinpleCase(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> Ab | A Bc
            B -> bB | Ad | &
            A -> aA | &
        """ ) )
        first = firstGrammar.first()

        self.assertTextEqual(
        """
            + {S: [a, b, c, d], A: [&, a], B: [&, a, b, d]}
        """, sort_dictionary_lists( first ) )

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

    def test_grammarTransformationParsingComplexSingleProduction(self):
        LockableType.USE_STRING = False

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
        """
            + Tree(productions, [Production locked: False, symbols: [NonTerminal locked: True, str: S, sequence:
            + 0, has_epsilon: False, len: 1.], sequence: 0, has_epsilon: False., Tree(space, []),
            + Tree(non_terminals, [Production locked: False, symbols: [Terminal locked: True, str: a, sequence: 1,
            + has_epsilon: False, len: 1., NonTerminal locked: True, str: AB, sequence: 2, has_epsilon: False,
            + len: 1., Terminal locked: True, str: bb, sequence: 3, has_epsilon: False, len: 2., NonTerminal
            + locked: True, str: CC, sequence: 4, has_epsilon: False, len: 1., Terminal locked: True, str: 1a,
            + sequence: 5, has_epsilon: False, len: 2., NonTerminal locked: True, str: A, sequence: 6,
            + has_epsilon: False, len: 1., Terminal locked: True, str: b, sequence: 7, has_epsilon: False, len:
            + 1., NonTerminal locked: True, str: A, sequence: 8, has_epsilon: False, len: 1., NonTerminal locked:
            + True, str: BC, sequence: 9, has_epsilon: False, len: 1.], sequence: 9, has_epsilon: False.,
            + Production locked: False, symbols: [Terminal locked: True, str: ba, sequence: 1, has_epsilon: False,
            + len: 2.], sequence: 1, has_epsilon: False., Production locked: False, symbols: [Terminal locked:
            + True, str: c, sequence: 1, has_epsilon: False, len: 1.], sequence: 1, has_epsilon: False.])])
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

