#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

import time
import random

import PyQt5
import textwrap

from PyQt5 import QtWidgets
from PyQt5.QtCore import QCoreApplication

from natsort import natsorted
from contextlib import suppress
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


def dictionary_to_string(dictionary, sort=None):
    """
        Given a dictionary with a list for each string key, call `sort_dictionary_lists()` and
        return a string representation by line of its entries.
    """

    if not len( dictionary ):
        return " No elements found."

    if sort:
        iterable = sort( iterable )

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

    if isinstance( iterable, dict):
        return dictionary_to_string( iterable )

    if not len( iterable ):
        return " No elements found."

    strings = []

    if sort:
        iterable = sort( iterable )

    else:
        iterable = sort_alphabetically_and_by_length( iterable )

    for item in iterable:
        strings.append( " {}".format( repr( item ) ) )

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


def setTextWithoutCleaningHistory(editTextWidget, textToSet):
    """
        Making changes to a QTextEdit without adding an undo command to the undo stack
        https://stackoverflow.com/questions/27113262/making-changes-to-a-qtextedit-without-adding-an-undo-command-to-the-undo-stack

        http://doc.qt.io/qt-5/qtextcursor.html#SelectionType-enum
        http://doc.qt.io/qt-5/qtextdocument.html#clearUndoRedoStacks
        http://www.qtcentre.org/threads/43268-Setting-Text-in-QPlainTextEdit-without-Clearing-Undo-Redo-History
    """
    textCursor = editTextWidget.textCursor()

    # Autoscroll PyQT QTextWidget
    # https://stackoverflow.com/questions/7778726/autoscroll-pyqt-qtextwidget
    verticalScrollBar = editTextWidget.verticalScrollBar()
    horizontalScrollBar = editTextWidget.horizontalScrollBar()

    textCursor.beginEditBlock()
    textCursor.select( PyQt5.QtGui.QTextCursor.Document );
    textCursor.removeSelectedText();
    textCursor.insertText( textToSet );
    textCursor.endEditBlock()

    verticalScrollBar.setValue( horizontalScrollBar.maximum() )
    horizontalScrollBar.setValue( horizontalScrollBar.minimum() )

    # PyQT force update textEdit before calling other function
    # https://stackoverflow.com/questions/47654327/pyqt-force-update-textedit-before-calling-other-function
    editTextWidget.repaint()
    QCoreApplication.processEvents()


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


class IntermediateGrammar(object):
    """
        Represents a grammar operation history entry, to be parsed later.
    """

    ## A constant for the beginning of the time
    BEGINNING = 0

    ## A constant for the end of the time
    END = 1

    ## A constant for any point between the beginning and end of the time
    MIDDLE = 2

    class Stage(object):
        """
            Represents a point in the grammar history, to determine whether this the beginning of
            the history, middle or end.
        """

        def __init__(self, value):
            """
                Initializes the history with a history point constant.
            """
            ## The value of the current time constant
            self.value = value

        def __eq__(self, other):
            """
                Determines whether this stage history entry is equal or not to another one given.
            """

            if isinstance(self, other.__class__):
                return self.value == other.value

            return False

        def __str__(self):
            """
                Return the current history point stage name.
            """

            if self.value == IntermediateGrammar.BEGINNING:
                return ", Beginning"

            if self.value == IntermediateGrammar.END:
                return ", End"

            return ""

    def __init__(self, grammar, name, stage):
        """
            Creates a full history entry for the current state of the given `grammar`.
        """
        ## The precise time when this history entry was created, useful to merge history for different grammars
        self.timestamp = time.time()

        ## The string representation of the grammar saved
        self.grammar = str( grammar )

        ## The name of the operation which originates the current grammar history entry
        self.name = name

        ## The stage name for the current grammar state
        self.stage = IntermediateGrammar.Stage( stage )

        ## Additional information to be displayed
        self.extra_text = []

    def __str__(self):
        """
            Return the full history representation of the saved grammar.
        """

        if self.extra_text:
            return wrap_text( """%s%s\n# %s\n%s
                """ % ( self.name, self.stage, "".join( self.extra_text ), self.grammar ) )

        return wrap_text( """%s%s\n%s
            """ % ( self.name, self.stage, self.grammar ) )

    def __eq__(self, other):
        """
            Determines whether this grammar history entry is equal or not to another one given.
        """

        if isinstance(self, other.__class__):
            return ( self.stage.value == self.MIDDLE or other.stage.value == self.MIDDLE or self.stage == other.stage ) \
                    and str( self.grammar ) == str( other.grammar ) and self.extra_text == other.extra_text

        return False


class ListSetLike(list):
    """
        A extended python list version, allowing dynamic patching.

        This is required to monkey patch the builtin type because they are implemented in CPython
        and are not exposed to the interpreter.
    """

    def add(self, element):
        """
            Add a new element to the end of the list.
        """
        if element not in self:
            self.append( element )

    def discard(self, element):
        """
            Remove new element anywhere in the list.
        """
        with suppress(ValueError, AttributeError):
            self.remove( element )


class DynamicIterationSet(object):
    """
        A `set()` like object which allows to dynamically add and remove items while iterating over
        its elements as if a `for element in dynamic_set`
    """

    def __init__(self, initial=[], container_type=set):
        """
            Fully initializes and create a new set.

            @param `initial` is any list related object used to initialize the set if new values.
            @param `container_type` you can choose either list or set to store the elements internally
        """
        container_type = type( container_type )

        if container_type is type( list ):
            container_type = ListSetLike

        elif container_type is type( set ):
            container_type = set

        else:
            raise RuntimeError( "Invalid type passed by: `%s`" % container_type )

        ## The set with the items which were already iterated while iterating over this set
        self.iterated_items = container_type()

        ## The set with the items which are going to be iterated while iterating over this set
        self.non_iterated_items = container_type( initial )

        ## Whether the iteration process is allowed to use new items added on the current iteration
        self.new_items_skip_count = 0

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

    def not_iterate_over_new_items(self, how_many_times=1):
        """
            If called before start iterating over this dictionary, it will not iterate over the
            new keys added until the current iteration is over.

            `how_many_times` is for how many iterations it should keep ignoring the new items.
        """
        self.new_items_skip_count = how_many_times + 1

    def __iter__(self):
        """
            Called by Python automatically when iterating over this set and python wants to start
            the iteration process.
        """
        self.new_items_skip_count -= 1

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

            if self.new_items_skip_count > 0:
                self.iterated_items.add( item )

            else:
                self.non_iterated_items.add( item )

    def discard(self, item):
        """
            Remove an element from the set, either the element was iterated or not in the current
            iteration.
        """
        self.iterated_items.discard( item )
        self.non_iterated_items.discard( item )


class DynamicIterable(object):
    """
        Dynamically creates creates a unique iterable which can be used one time.

        Why have an __iter__ method in Python?
        https://stackoverflow.com/questions/36681312/why-have-an-iter-method-in-python
    """

    def __init__(self, iterable_access, end_index=None):
        """
            Receives a iterable an initialize the object to start an iteration.
        """
        ## The current index used when iterating over this collection items
        self.current_index = -1

        ## The iterable access method to get the next item given a index
        if end_index:
            int( end_index[0] ) # ensure it is a list starting with a integer
            self.iterable_access = lambda index: iterable_access( index ) if index < end_index[0] else self.stop_iteration( index )

        else:
            self.iterable_access = iterable_access

    def __next__(self):
        """
            Called by Python automatically when iterating over this set and python wants to know the
            next element to iterate. Raises `StopIteration` when the iteration has been finished.

            How to make a custom object iterable?
            https://stackoverflow.com/questions/21665485/how-to-make-a-custom-object-iterable
            https://stackoverflow.com/questions/4019971/how-to-implement-iter-self-for-a-container-object-python
        """
        self.current_index += 1

        try:
            return self.iterable_access( self.current_index )

        except IndexError:
            raise StopIteration

    def stop_iteration(self, index):
        """
            Raise the exception `StopIteration` to stop the current iteration.
        """
        raise StopIteration

    def __iter__(self):
        """
            Resets the current index and return a copy if itself for iteration.
        """
        self.current_index = -1
        return self


class DynamicIterationDict(object):
    """
        A `dict()` like object which allows to dynamically add and remove items while iterating over
        its elements as if a `for element in dynamic_set`

        https://wiki.python.org/moin/TimeComplexity
        https://stackoverflow.com/questions/4014621/a-python-class-that-acts-like-dict
    """

    def __init__(self, initial=None):
        """
            Fully initializes and create a new dictionary.

            @param `initial` is a dictionary used to initialize it with new values.
        """
        ## The list with the keys of this collection elements
        self.keys_list = list()

        ## The list with the elements of this collection
        self.values_list = list()

        ## A dictionary with the indexes of the elements in this collection
        self.items_dictionary = dict()

        ## Whether the iteration process is allowed to use new items added on the current iteration
        self.new_items_skip_count = 0

        ## Holds the global maximum iterable index used when `new_items_skip_count` is set
        self.maximum_iterable_index = [0]

        if initial:

            for key in initial:
                self[key] = initial[key]

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
        return "(%s) (%s; %s)" % ( self.items_dictionary, self.keys_list, self.values_list )

    def __contains__(self, key):
        """
            Determines whether this dictionary contains or not a given `key`.
        """
        return key in self.items_dictionary

    def __len__(self):
        """
            Return the total length of this set.
        """
        return len( self.items_dictionary )

    def __iter__(self):
        """
            Called by Python automatically when iterating over this set and python wants to start
            the iteration process.

            Why have an __iter__ method in Python?
            https://stackoverflow.com/questions/36681312/why-have-an-iter-method-in-python
        """
        return self.get_iterator( self.get_key )

    def __setitem__(self, key, value):
        """
            Given a `key` and `item` add it to this dictionary as a non yet iterated item, replacing
            the existent value. It a iteration is running, and the item was already iterated, then
            it will be updated on the `niterated_items` dict.
        """
        items_dictionary = self.items_dictionary

        if key in items_dictionary:
            item_index = items_dictionary[key]
            self.values_list[item_index] = value

        else:
            values_list = self.values_list
            self.items_dictionary[key] = len( values_list )

            values_list.append( value )
            self.keys_list.append( key )

    def __getitem__(self, key):
        """
            Given a `key` returns its existent value.
        """
        # log( 1, "index: %s, key: %s", self.items_dictionary[key], key )
        return self.values_list[self.items_dictionary[key]]

    def __delitem__(self, key):
        """
            Given a `key` deletes if from this dict.
        """
        # log( 1, "key: %s, self: %s", key, self )
        items_dictionary = self.items_dictionary
        keys_list = self.keys_list
        item_index = items_dictionary[key]

        del self.keys_list[item_index]
        del self.values_list[item_index]
        del items_dictionary[key]

        # Fix the maximum index, when some item bellow the maximum was remove
        if item_index < self.maximum_iterable_index[0]:
            self.maximum_iterable_index[0] -= 1

        # Fix the the outdated indexes in the dictionary after the removal
        for key_index in range( item_index, len( items_dictionary ) ):
            key_name = keys_list[key_index]
            items_dictionary[key_name] = items_dictionary[key_name] - 1

    def keys(self):
        """
            Return a DynamicIterable over the keys stored in this collection.
        """
        return self.get_iterator( self.get_key )

    def values(self):
        """
            Return a DynamicIterable over the values stored in this collection.
        """
        return self.get_iterator( self.get_value )

    def items(self):
        """
            Return a DynamicIterable over the (key, value) stored in this collection.
        """
        return self.get_iterator( self.get_key_value )

    def get_key(self, index):
        """
            Given a `index` returns its corresponding key.
        """
        return self.keys_list[index]

    def get_value(self, index):
        """
            Given a `index` returns its corresponding value.
        """
        return self.values_list[index]

    def get_key_value(self, index):
        """
            Given a `index` returns its corresponding ( key, value ) pair.
        """
        return ( self.keys_list[index], self.values_list[index] )

    def get_iterator(self, target_generation):
        """
            Get fully configured iterable given the `target_generation` function.
        """
        self.new_items_skip_count -= 1

        if self.new_items_skip_count > 0:
            self.maximum_iterable_index[0] = len( self )
            return DynamicIterable( target_generation, self.maximum_iterable_index )

        return DynamicIterable( target_generation )

    def not_iterate_over_new_items(self, how_many_times=1):
        """
            If called before start iterating over this dictionary, it will not iterate over the
            new keys added until the current iteration is over.

            `how_many_times` is for how many iterations it should keep ignoring the new items.
        """
        self.new_items_skip_count = how_many_times + 1

    def clear(self):
        """
            Remove all items from this dict.
        """
        self.keys_list.clear()
        self.values_list.clear()
        self.items_dictionary.clear()

