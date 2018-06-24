#! /usr/bin/env python
# -*- coding: utf-8 -*-

from contextlib import suppress

from debug_tools import getLogger

# level 4 - Abstract Syntax Tree Parsing
log = getLogger( 127-4, __name__ )


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

