#! /usr/bin/env python
# -*- coding: utf-8 -*-

import lark
import unittest

from source.grammar import ChomskyGrammar

from source.utilities import wrap_text
from source.utilities import getCleanSpaces
from source.utilities import ChomskyGrammarTreeTransformer

from source.testing_utilities import TestingUtilities


class TestChomskyGrammar(TestingUtilities):
    """
        Tests the Grammar class.
    """

    def test_grammarTransformationParsingComplexSingleProduction(self):
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
            + Tree(productions, [{locked: False, sequence: 0, productions: [{locked: True,
            + symbols: S, sequence: 0, len: 1, str: S}]}, Tree(space, []), Tree(non_terminals,
            + [{locked: False, sequence: 9, productions: [{locked: True, symbols: a, sequence:
            + 1, len: 1, str: a}, {locked: True, symbols: AB, sequence: 2, len: 2, str: AB},
            + {locked: True, symbols: bb, sequence: 3, len: 2, str: bb}, {locked: True,
            + symbols: CC, sequence: 4, len: 2, str: CC}, {locked: True, symbols: 1a,
            + sequence: 5, len: 2, str: 1a}, {locked: True, symbols: A, sequence: 6, len: 1,
            + str: A}, {locked: True, symbols: b, sequence: 7, len: 1, str: b}, {locked: True,
            + symbols: A, sequence: 8, len: 1, str: A}, {locked: True, symbols: BC, sequence:
            + 9, len: 2, str: BC}]}, {locked: False, sequence: 1, productions: [{locked: True,
            + symbols: ba, sequence: 1, len: 2, str: ba}]}, {locked: False, sequence: 1,
            + productions: [{locked: True, symbols: c, sequence: 1, len: 1, str: c}]}])])
        """, wrap_at_80=True, trim_spaces=True ), wrap_text( str( firstGrammar ), wrap_at_80=True ) )

    def test_grammarInputParsingComplexSingleProduction(self):
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

    def test_grammarTreeParsingComplexSingleProduction(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines(
        """
            S -> aABbbCC1aAbA BC | ba | c
        """ )

        self.assertTextEqual(
        """
            + S -> a AB bb CC 1a A b A BC | ba | c
        """, str( firstGrammar ) )

    def test_grammarInputParsingABandB(self):
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

    def test_grammarTreeParsingSSandEpsilon(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines(
        """
            S -> SS SSS | &
        """ )

        self.assertTextEqual(
        """
            + S -> & | SS SSS
        """, str( firstGrammar ) )

    def test_grammarInputParsingSSandEpsilon(self):
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

