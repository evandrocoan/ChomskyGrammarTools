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

    def test_grammarFirstSinpleCase(self):
        firstGrammar = ChomskyGrammar.load_from_text_lines( wrap_text(
        """
            S -> Ab | A Bc
            B -> bB | Ad | &
            A -> aA | &
        """ ) )

        self.assertEqual(
        {
        }, firstGrammar.first() )

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
            +   non_terminals
            +     production
            +       non_terminal  S
            +       space
            +       non_terminal  S
            +       space
            +     production
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
        firstGrammar = ChomskyGrammar.parse( wrap_text(
        """
            S -> aABbbCC1aAbA BC | ba | c
        """ ) )
        firstGrammar = ChomskyGrammarTreeTransformer().transform( firstGrammar )

        self.assertTextEqual(
        """
            + productions
            +   S
            +   non_terminals
            +     a AB bb CC 1a A b A BC
            +     ba
            +     c
        """, firstGrammar.pretty() )

        self.assertTextEqual( wrap_text(
        """
            + Tree(productions, [{locked: False, symbols: [{locked: True, symbols: S, sequence: 0, len: 1, str:
            + S}], sequence: 0}, Tree(non_terminals, [{locked: False, symbols: [{locked: True, symbols: a,
            + sequence: 1, len: 1, str: a}, {locked: True, symbols: AB, sequence: 2, len: 2, str: AB}, {locked:
            + True, symbols: bb, sequence: 3, len: 2, str: bb}, {locked: True, symbols: CC, sequence: 4, len: 2,
            + str: CC}, {locked: True, symbols: 1a, sequence: 5, len: 2, str: 1a}, {locked: True, symbols: A,
            + sequence: 6, len: 1, str: A}, {locked: True, symbols: b, sequence: 7, len: 1, str: b}, {locked:
            + True, symbols: A, sequence: 8, len: 1, str: A}, {locked: True, symbols: BC, sequence: 9, len: 2,
            + str: BC}], sequence: 9}, {locked: False, symbols: [{locked: True, symbols: ba, sequence: 1, len: 2,
            + str: ba}], sequence: 1}, {locked: False, symbols: [{locked: True, symbols: c, sequence: 1, len: 1,
            + str: c}], sequence: 1}])])
        """, trim_spaces=True ), wrap_text( str( firstGrammar ), wrap_at_80=True ) )

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
            +   non_terminals
            +     production
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
            +       terminal
            +         b
            +         a
            +     production
            +       terminal  c
        """, firstGrammar.pretty() )

    def test_grammarTreeParsingComplexSingleProduction(self):
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
            +   non_terminals
            +     production
            +       terminal  a
            +       non_terminal
            +         A
            +         B
            +       terminal  b
            +       non_terminal
            +         B
            +         C
            +       space
            +     production
            +       terminal  b
        """, firstGrammar.pretty() )

    def test_grammarTreeParsingSSandEpsilon(self):
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
            +   non_terminal_start
            +     non_terminal  S
            +   non_terminals
            +     production
            +       non_terminal  S
            +       space
            +       non_terminal
            +         S
            +         S
            +       space
            +     production
            +       epsilon
            +   end_symbol
            +     new_line
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

