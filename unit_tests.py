#! /usr/bin/env python
# -*- coding: utf-8 -*-

import lark
import unittest

from source.grammar import ChomskyGrammar

from source.utilities import wrap_text
from source.utilities import getCleanSpaces
from source.testing_utilities import TestingUtilities


class TestChomskyGrammar(TestingUtilities):
    """
        Tests the Grammar class.
    """

    def test_grammarInputParsing(self):
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

    def test_grammarInputParsingSDoubleSSandEpsilonProduction(self):
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

