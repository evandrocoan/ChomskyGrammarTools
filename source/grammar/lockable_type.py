#! /usr/bin/env python
# -*- coding: utf-8 -*-

#
# Licensing
#
# Python Lockable Objects
# Copyright (C) 2018 Evandro Coan <https://github.com/evandrocoan>
#
#  This program is free software; you can redistribute it and/or modify it
#  under the terms of the GNU General Public License as published by the
#  Free Software Foundation; either version 3 of the License, or ( at
#  your option ) any later version.
#
#  This program is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#  General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os
import copy

from debug_tools.utilities import get_unique_hash
from debug_tools.utilities import get_representation

from debug_tools import getLogger

# level 4 - Abstract Syntax Tree Parsing
log = getLogger( 127-4, __name__ )


class LockableType(object):
    """
        An object type which can have its attributes changes locked/blocked after its `lock()`
        method being called.

        After locking, its string representation attribute is going to be saved as an attribute and
        returned when needed.
    """

    USE_STRING = True
    EMQUOTE_STRING = False

    def __init__(self):
        """
            How to handle call to __setattr__ from __init__?
            https://stackoverflow.com/questions/3870982/how-to-handle-call-to-setattr-from-init
        """
        super().__setattr__('locked', False)

        ## Controls whether the attributes changes of this object are allow or not
        self.locked = False

        ## Caches the string representation of this object, after locking its attributes changes with `lock()`
        self.str = ""

        ## The caches the length of this object, used while this object is in locked state
        self.len = 0

        ## An unique identifier for any LockableType object
        self._hash = get_unique_hash()

        self._original_len = self._len
        self._original_str = self._str
        self._original_hash = self._hash

    def __setattr__(self, name, value):
        """
            Block attributes from being changed after it is activated.
            https://stackoverflow.com/questions/17020115/how-to-use-setattr-correctly-avoiding-infinite-recursion
        """

        if self.locked:
            raise AttributeError( "Attributes cannot be changed after `locked` is set to True! %s" % self.__repr__() )

        else:
            super().__setattr__( name, value )

    def __eq__(self, other):
        """
            Determines whether this object is equal to another one based on their hashes.
        """

        if isinstance( self, LockableType ) is isinstance( other, LockableType ):
            return hash( self ) == hash( other )

        raise TypeError( "'=' not supported between instances of '%s' and '%s'" % (
                self.__class__.__name__, other.__class__.__name__ ) )

    def __hash__(self):
        """
            Return the hash of this object based on its string representation.
        """
        return self._hash

    def repr(self):
        """
            See `__repr__()` for details.
        """
        return get_representation( self, ignore={'hash'}, emquote=self.EMQUOTE_STRING )

    def __repr__(self):
        """
            Prints a representation of this object within all its attributes.
        """

        if self.USE_STRING:
            return self.__str__()

        return self.repr()

    def __str__(self):
        """
            Python does not allow to dynamically/monkey patch its build in functions. Then, we create
            out own function and call it from the built-in function.
        """
        return self._str()

    def _str(self):
        """
            Caches the string representation of this object, after locking its attributes changes with `lock()`
        """

        if self.USE_STRING:
            return super().__str__()

        return get_representation( self, ignore={'hash'}, emquote=self.EMQUOTE_STRING )

    def __len__(self):
        """
            Python does not allow to dynamically/monkey patch its build in functions. Then, we create
            out own function and call it from the built-in function.
        """
        return self._len()

    def _len(self):
        raise TypeError( "object of type '%s' has no len()" % self.__class__.__name__ )

    def _unlock(self):
        """
            Unblock the object changes allowing its attributes to be freely set.

            Do not call it if this object is inside a hashtable as list or set, because an object
            cannot have its hash changed while they are inside it. Otherwise, the hashmap will not
            get updated and the new version of the object will point as non existent.
        """

        if not self.locked:
            return

        self.__dict__['locked'] = False
        self._len = self._original_len
        self._str = self._original_str
        self._hash = self._original_hash

    def lock(self):
        """
            Block further changes to this object attributes and cache its length and string
            representation for faster access.
        """

        if self.locked:
            return

        self.str = str( self )
        self._str = lambda: self.str

        self.len = len( self )
        self._len = lambda: self.len

        self._hash = hash( self._str() )
        self.locked = True

    def new(self, unlocked=True):
        """
            Creates and return a new copy of the current a object.
        """
        new_copy = copy.deepcopy( self )
        # log( 1, "self: %s", self )
        # log( 1, "new_copy: %s", new_copy )

        if unlocked:
            new_copy._unlock()

        else:
            new_copy.lock()

        return new_copy

