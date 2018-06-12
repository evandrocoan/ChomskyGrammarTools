#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os

from .utilities import get_unique_hash
from .utilities import get_representation

from debug_tools import getLogger

# level 4 - Abstract Syntax Tree Parsing
log = getLogger( 127-4, os.path.basename( os.path.dirname( os.path.abspath ( __file__ ) ) ) )


class LockableType(object):
    """
        An object type which can have its attributes changes locked/blocked after its `lock()`
        method being called.

        After locking, ts string representation attribute is going to be saved as an attribute and
        returned when needed.
    """

    _USE_STRING = True
    _EMQUOTE_STRING = False

    def __init__(self):
        """
            How to handle call to __setattr__ from __init__?
            https://stackoverflow.com/questions/3870982/how-to-handle-call-to-setattr-from-init
        """
        super().__setattr__('locked', False)

        """
            An unique identifier for any LockableType object
        """
        self.unique_hash = get_unique_hash()

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

        if isinstance( self, LockableType ) is isinstance( other, LockableType ):
            return hash( self ) == hash( other )

        raise TypeError( "'=' not supported between instances of '%s' and '%s'" % (
                self.__class__.__name__, other.__class__.__name__ ) )

    def __hash__(self):
        return self._hash

    def __repr__(self):

        if self._USE_STRING:
            string = self.__str__()

            if self._EMQUOTE_STRING:
                return emquote_string( string )

            return string

        return get_representation( self, ignore={'unique_hash'} )

    def __str__(self):
        """
            Python does not allow to dynamically/monkey patch its build in functions. Then, we create
            out own function and call it from the built-in function.
        """
        return self._str()

    def _str(self):

        if self._USE_STRING:
            return super().__str__()

        return get_representation( self, ignore={'unique_hash'} )

    def __len__(self):
        """
            Python does not allow to dynamically/monkey patch its build in functions. Then, we create
            out own function and call it from the built-in function.
        """
        return self._len()

    def _len(self):
        raise TypeError( "object of type '%s' has no len()" % self.__class__.__name__ )

    def lock(self):
        """
            Block further changes to this object attributes and save its string representation for
            faster access.
        """

        if self.locked:
            return

        self.str = str( self )
        self._str = lambda : self.str

        self._hash = hash( self._str() )
        self.locked = True


