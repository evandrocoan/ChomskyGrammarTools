#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

import random

import PyQt5
import textwrap

from PyQt5 import QtWidgets

from natsort import natsorted
from debug_tools import getLogger

# level 4 - Abstract Syntax Tree Parsing
log = getLogger( 127-4, __name__ )

# An unique identifier for any created object
initial_hash = random.getrandbits( 32 )


def get_unique_hash():
    """
        Generates an unique identifier which can be used to uniquely identify distinct object
        instances.
    """
    global initial_hash

    initial_hash += 1
    return initial_hash


def get_duplicated_elements(elements_list):
    """
        Given an `elements_list` with duplicated elements, return a set only with the duplicated
        elements in the list. If there are not duplicated elements, an empty set is returned.

        How do I find the duplicates in a list and create another list with them?
        https://stackoverflow.com/questions/9835762/how-do-i-find-the-duplicates-in-a-list-and-create-another-list-with-them
    """
    visited_elements = set()
    visited_and_duplicated = set()

    add_item_to_visited_elements = visited_elements.add
    add_item_to_visited_and_duplicated = visited_and_duplicated.add

    for item in elements_list:

        if item in visited_elements:
            add_item_to_visited_and_duplicated(item)

        else:
            add_item_to_visited_elements(item)

    return visited_and_duplicated


def trimMessage(message):
    """
        Cuts a message maximum width and length and add an ellipsis (...) when it exceeds 30 lines
        or 150 characters of line size.
    """
    message_lines = message.split( '\n' )
    clean_message = []

    if len( message_lines ) > 30:
        message_lines = message_lines[:30]
        message_lines.append( '\n...' )

    for line in message_lines:

        if len( line ) > 150:
            line = line[:150] + '...'

        clean_message.append( line )

    return "\n".join( clean_message )


def emquote_string(string):
    """
        Return a string escape into single or double quotes accordingly to its contents.
    """
    string = str( string )
    is_single = "'" in string
    is_double = '"' in string

    if is_single and is_double:
        return '"{}"'.format( string.replace( "'", "\\'" ) )

    if is_single:
        return '"{}"'.format( string )

    return "'{}'".format( string )


def sort_dictionary_lists(dictionary):
    """
        Give a dictionary, call `sorted` on all its elements.
    """

    for key, value in dictionary.items():
        dictionary[key] = sorted( value )

    return dictionary


def sort_alphabetically_and_by_length(iterable):
    """
        Give an `iterable`, sort its elements accordingly to the following criteria:
            1. Sorts normally by alphabetical order
            2. Sorts by descending length

        How to sort by length of string followed by alphabetical order?
        https://stackoverflow.com/questions/4659524/how-to-sort-by-length-of-string-followed-by-alphabetical-order
    """
    return sorted( sorted( natsorted( iterable, key=lambda item: str( item ).lower() ),
                          key=lambda item: str( item ).istitle() ),
                  key=lambda item: len( str( item ) ) )


def sort_correctly(iterable):
    """
        Sort the given iterable in the way that humans expect.

        How to sort alpha numeric set in python
        https://stackoverflow.com/questions/2669059/how-to-sort-alpha-numeric-set-in-python
    """
    convert = lambda text: int( text ) if text.isdigit() else text
    alphanum_key = lambda key: [convert( characters ) for characters in re.split( '([0-9]+)', str( key ).lower() )]
    return sorted( sorted( iterable, key=alphanum_key ), key=lambda item: str( item ).istitle() )


def get_largest_item_size(iterable):
    """
        Given a iterable, get the size/length of its largest key value.
    """
    largest_key = 0

    for key in iterable:

        if len( key ) > largest_key:
            largest_key = len( key )

    return largest_key


def dictionary_to_string(dictionary):
    """
        Given a dictionary with a list for each string key, call `sort_dictionary_lists()` and
        return a string representation by line of its entries.
    """
    strings = []
    elements_strings = []

    dictionary = sort_dictionary_lists( dictionary )
    largest_key = get_largest_item_size( dictionary.keys() ) + 1

    for key, values in dictionary.items():
        elements_strings.clear()

        for item in values:
            elements_strings.append( "{}".format( str( item ) ) )

        strings.append( "{:>{largest_key}}: {}".format( str( key ), " ".join( elements_strings ),
                largest_key=largest_key ) )

    return "\n".join( strings )


def convert_to_text_lines(iterable, use_repr=True, new_line=True, sort=None):
    """
        Given a dictionary with a list for each string key, call `sort_dictionary_lists()` and
        return a string representation by line of its entries.
    """
    strings = []

    if sort:
        iterable = sort( iterable )

    else:
        iterable = sort_alphabetically_and_by_length( iterable )

    for item in iterable:
        strings.append( "{}".format( repr( item ) ) )

    return ( "\n" if new_line else "" ).join( strings )


def ignore_exceptions(function_to_decorate):
    """
        Decorator to catch any exceptions threw and show them to the user on a dialog/message box.
    """

    def wrapper(*args, **kargs):

        try:
            return function_to_decorate( *args, **kargs )

        except Exception as error:
            log.exception( "" )
            ignore_exceptions.send_string_signal.emit( str( error ) )

    return wrapper


def setTextWithoutCleaningHistory(textWidget, textToSet):
    """
        Making changes to a QTextEdit without adding an undo command to the undo stack
        https://stackoverflow.com/questions/27113262/making-changes-to-a-qtextedit-without-adding-an-undo-command-to-the-undo-stack

        http://doc.qt.io/qt-5/qtextcursor.html#SelectionType-enum
        http://doc.qt.io/qt-5/qtextdocument.html#clearUndoRedoStacks
        http://www.qtcentre.org/threads/43268-Setting-Text-in-QPlainTextEdit-without-Clearing-Undo-Redo-History
    """
    textCursor = textWidget.textCursor()

    # Autoscroll PyQT QTextWidget
    # https://stackoverflow.com/questions/7778726/autoscroll-pyqt-qtextwidget
    verticalScrollBar = textWidget.verticalScrollBar()
    horizontalScrollBar = textWidget.horizontalScrollBar()

    textCursor.beginEditBlock()
    textCursor.select( PyQt5.QtGui.QTextCursor.Document );
    textCursor.removeSelectedText();
    textCursor.insertText( textToSet );
    textCursor.endEditBlock()

    verticalScrollBar.setValue( horizontalScrollBar.maximum() )
    horizontalScrollBar.setValue( horizontalScrollBar.minimum() )


def getCleanSpaces(inputText, minimumLength=0, lineCutTrigger="", keepSpaceSepators=False):
    """
        Removes spaces and comments from the input expression.

        `minimumLength` of a line to not be ignored
        `lineCutTrigger` all lines after a line starting with this string will be ignored
        `keepSpaceSepators` it will keep at a single space between sentences as `S S`, given `S    S`
    """

    if keepSpaceSepators:
        removeNewSpaces = ' '.join( inputText.split( ' ' ) )
        lineCutTriggerNew = ' '.join( lineCutTrigger.split( ' ' ) ).strip( ' ' )

    else:
        removeNewSpaces = re.sub( r"\t| ", "", inputText )
        lineCutTriggerNew = re.sub( r"\t| ", "", lineCutTrigger )

    # log( 1, "%s", inputText, minimumLength=0 )
    lines = removeNewSpaces.split( "\n" )
    clean_lines = []

    for line in lines:

        if keepSpaceSepators:
            line = line.strip( ' ' )

        if minimumLength:

            if len( line ) < minimumLength:
                continue

        if lineCutTrigger:

            if line.startswith( lineCutTriggerNew ):
                break

        if line.startswith( "#" ):
            continue

        clean_lines.append( line )

    return clean_lines


def wrap_text(text, wrap=0, trim_tabs=False, trim_spaces=False, trim_lines=False):
    """
        1. Remove input text leading common indentation, trailing white spaces
        2. If `wrap`, wraps big lists on 80 characters.
        3. If `trim_spaces`, remove leading '+' symbols and if `trim_tabs` replace tabs with 2 spaces.
        4. If `trim_lines`, remove all new line characters.
    """
    clean_lines = []

    if not isinstance( text, str ):
        text = str( text )

    if trim_tabs:
        text = text.replace( '\t', '  ' )

    dedent_lines = textwrap.dedent( text ).strip( '\n' )

    if trim_spaces:

        for line in dedent_lines.split( '\n' ):
            line = line.rstrip( ' ' ).lstrip( '+' )
            clean_lines.append( line )

        dedent_lines = textwrap.dedent( "\n".join( clean_lines ) )

    if wrap:
        clean_lines.clear()

        for line in dedent_lines.split( '\n' ):
            line = textwrap.fill( line, width=wrap )
            clean_lines.append( line )

        dedent_lines = "\n".join( clean_lines )

    if trim_lines:
        dedent_lines = "".join( dedent_lines.split( '\n' ) )

    return dedent_lines


def get_representation(self, ignore=[], emquote=False):
    """
        Given a object, iterating through all its public attributes and return then as a string
        representation.

        `ignore` a list of attributes to be ignored
        `emquote` if True, puts the attributes values inside single or double quotes accordingly.
    """
    valid_attributes = self.__dict__.keys()
    clean_attributes = []

    if emquote:

        def pack_attribute(string):
            return emquote_string( string )

    else:

        def pack_attribute(string):
            return string

    for attribute in valid_attributes:

        if not attribute.startswith( '_' ) and attribute not in ignore:
            clean_attributes.append( "{}: {}".format( attribute, pack_attribute( self.__dict__[attribute] ) ) )

    return "%s %s;" % ( self.__class__.__name__, ", ".join( clean_attributes ) )


class DynamicIterationSet(object):
    """
        A `set()` like object which allows to dynamically add and remove items while iterating over
        its elements as if a `for element in dynamic_set`
    """

    def __init__(self, initial=[]):
        """
            Fully initializes and create a new set.

            `initial` is any list related object used to initialize the set if new values.
        """
        ## The set with the items which were already iterated while iterating over this set
        self.iterated_items = set()

        ## The set with the items which are going to be iterated while iterating over this set
        self.non_iterated_items = set( initial )

    def __repr__(self):
        """
            Return a full representation of all public attributes of this object set state for
            debugging purposes.
        """
        return get_representation( self )

    def __str__(self):
        """
            Return a nice string representation of this set.

            On the first part is showed all already iterated elements, followed by the not yet
            iterated. When the iteration process is not running, it shows the last state registered.
        """
        return "%s %s" % ( self.iterated_items, self.non_iterated_items )

    def __contains__(self, key):
        """
            Determines whether this set contains or not a given element.
        """
        return key in self.iterated_items or key in self.non_iterated_items

    def __len__(self):
        """
            Return the total length of this set.
        """
        return len( self.iterated_items ) + len( self.non_iterated_items )

    def __iter__(self):
        """
            Called by Python automatically when iterating over this set and python wants to start
            the iteration process.
        """

        for item in self.iterated_items:
            self.non_iterated_items.add( item )

        self.iterated_items.clear()
        return self

    def __next__(self):
        """
            Called by Python automatically when iterating over this set and python wants to know the
            next element to iterate.

            Raises `StopIteration` when the iteration has been finished.
        """

        for first_element in self.non_iterated_items:
            self.non_iterated_items.discard( first_element )
            break

        else:
            self.iterated_items, self.non_iterated_items = self.non_iterated_items, self.iterated_items
            raise StopIteration

        self.iterated_items.add( first_element )
        return first_element

    def add(self, item):
        """
            An new element to the set, if it is not already present.

            The element can be the immediate next if there is an iteration running.
        """

        if item not in self.iterated_items and item not in self.non_iterated_items:
            self.non_iterated_items.add( item )

    def discard(self, item):
        """
            Remove an element from the set, either the element was iterated or not in the current
            iteration.
        """
        self.iterated_items.discard( item )
        self.non_iterated_items.discard( item )

