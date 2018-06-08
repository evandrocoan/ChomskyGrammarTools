#! /usr/bin/env python
# -*- coding: utf-8 -*-

import lark
import unittest

from source.grammar import Grammar

from source.utilities import wrap_text
from source.utilities import getCleanSpaces
from source.testing_utilities import TestingUtilities


class TestRegularGrammar(TestingUtilities):
    """
        Tests the Grammar class.
    """

    def test_grammarGenerateSentencesOfnAsSize5(self):
        firstGrammar = Grammar.load_from_text_lines(
        """
            A -> aA | a
        """ )
        generate_sentences = []
        firstGrammar.generate_sentences_of_size_n( 5, generate_sentences )

        self.assertTextEqual(
        """
            + ['a', 'aa', 'aaa', 'aaaa', 'aaaaa']
        """, str( generate_sentences ) )


if __name__ == "__main__":
    unittest.main()

