#! /usr/bin/env python
# -*- coding: utf-8 -*-

from contextlib import suppress

from debug_tools import getLogger

# level 4 - Abstract Syntax Tree Parsing
log = getLogger( 127-4, __name__ )


class DynamicIterable(object):
    """
        Dynamically creates creates a unique iterable which can be used one time.

        Why have an __iter__ method in Python?
        https://stackoverflow.com/questions/36681312/why-have-an-iter-method-in-python
    """

    def __init__(self, iterable_access, empty_slots, end_index=None, new_empty_slots=set()):
        """
            Receives a iterable an initialize the object to start an iteration.

            @param `iterable_access` a function pointer to function which returns the next element given its index
            @param `end_index` it must be a list with one integer element
            @param `empty_slots` it must be a set with indexes of free place to put new elements
        """
        ## The current index used when iterating over this collection items
        self.current_index = -1

        ## List the empty free spots for old items, which should be skipped when iterating over
        self.empty_slots = empty_slots

        ## List the empty free spots for new items, which should be skipped when iterating over
        self.new_empty_slots = new_empty_slots

        ## The iterable access method to get the next item given a index
        if end_index:
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
        empty_slots = self.empty_slots
        current_index = self.current_index + 1
        new_empty_slots = self.new_empty_slots

        while current_index in empty_slots or current_index in new_empty_slots:
            current_index += 1

        try:
            self.current_index = current_index
            # log( 1, "current_index: %s", current_index )
            return self.iterable_access( current_index )

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
        its elements as in `for element in dynamic_set`

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

        ## List the empty free spots for old items, used globally before the iteration starts
        self.empty_slots = set()

        ## List the empty free spots for old items, used globally after the iteration starts with `new_items_skip_count`
        self.new_empty_slots = set()

        ## A dictionary with the indexes of the elements in this collection
        self.items_dictionary = dict()

        ## Whether the iteration process is allowed to use new items added on the current iteration
        self.new_items_skip_count = 0

        ## Holds the global maximum iterable index used when `new_items_skip_count` is set
        self.maximum_iterable_index = [0]

        if initial:

            if isinstance( initial, dict ):

                for key, value in initial.items():
                    self[key] = value

            else:
                self.fromkeys( initial )

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

    def __call__(self, how_many_times=-1):
        """
            Return a iterable for the keys elements of this collection when calling its object as a
            function call.

            `how_many_times` is for how many iterations it should keep ignoring the new items.
        """
        return self.get_iterator( self.get_key, how_many_times )

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
            empty_slots = self.empty_slots
            values_list = self.values_list

            if empty_slots:
                free_slot = empty_slots.pop()
                self.new_empty_slots.add( free_slot )

                values_list[free_slot] = value
                self.keys_list[free_slot] = key

            else:
                free_slot = len( values_list )
                values_list.append( value )
                self.keys_list.append( key )

            self.items_dictionary[key] = free_slot

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

        self.empty_slots.add( item_index )
        del items_dictionary[key]

    def trim_indexes_sorted(self):
        """
            Fix the the outdated indexes on the internal lists after their dictionary removal,
            keeping the items original ordering O(n).
        """
        new_index = -1
        clean_keys = []
        clean_values = []

        values_list = self.values_list
        items_dictionary = self.items_dictionary

        for key, value_index in items_dictionary.items():
            new_index += 1
            items_dictionary[key] = new_index
            clean_keys.append( key )
            clean_values.append( values_list[value_index] )

        self.keys_list = clean_keys
        self.values_list = clean_values

    def trim_indexes_unsorted(self):
        """
            Fix the the outdated indexes on the internal lists after their dictionary removal.
            keeping the items original ordering O(k), where `k` is length of `self.empty_slots`.
        """
        keys_list = self.keys_list
        values_list = self.values_list
        empty_slots = self.empty_slots
        last_slot = -1

        while empty_slots:
            empty_slot = empty_slots.pop()
            keys_list[empty_slot] = keys_list.pop()
            values_list[empty_slot] = values_list.pop()

            if last_slot < empty_slot:
                last_slot = empty_slot

        if last_slot > -1:
            del keys_list[last_slot:]
            del values_list[last_slot:]

    def keys(self, how_many_times=-1):
        """
            Return a DynamicIterable over the keys stored in this collection.

            `how_many_times` is for how many iterations it should keep ignoring the new items.
        """
        return self.get_iterator( self.get_key, how_many_times )

    def values(self, how_many_times=-1):
        """
            Return a DynamicIterable over the values stored in this collection.

            `how_many_times` is for how many iterations it should keep ignoring the new items.
        """
        return self.get_iterator( self.get_value, how_many_times )

    def items(self, how_many_times=-1):
        """
            Return a DynamicIterable over the (key, value) stored in this collection.

            `how_many_times` is for how many iterations it should keep ignoring the new items.
        """
        return self.get_iterator( self.get_key_value, how_many_times )

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
            Given a `index` returns its corresponding (key, value) pair.
        """
        return ( self.keys_list[index], self.values_list[index] )

    def get_iterator(self, target_generation, how_many_times=-1):
        """
            Get fully configured iterable given the `target_generation` function.

            `how_many_times` is for how many iterations it should keep ignoring the new items.
        """
        self.not_iterate_over_new_items( how_many_times )
        self.new_items_skip_count -= 1

        if self.new_items_skip_count > 0:
            return DynamicIterable( target_generation, self.empty_slots, self.maximum_iterable_index, self.new_empty_slots )

        return DynamicIterable( target_generation, self.empty_slots )

    def not_iterate_over_new_items(self, how_many_times=1):
        """
            If called before start iterating over this dictionary, it will not iterate over the
            new keys added until the current iteration is over.

            `how_many_times` is for how many iterations it should keep ignoring the new items.
        """

        if how_many_times > -1:
            self.new_empty_slots.clear()
            self.new_items_skip_count = how_many_times + 1
            self.maximum_iterable_index[0] = len( self.keys_list )

    def fromkeys(self, iterable):
        """
            Initialize a dictionary with any default value, acting like a indexed set.
        """

        for key in iterable:
            self[key] = None

    def append(self, element):
        """
            Add a new element to the end of the list.
        """
        self[element] = None

    def remove(self, element):
        """
            Remove new `element` anywhere in the container.
        """
        del self[element]

    def add(self, element):
        """
            Add a new element to the end of the list.
        """
        self[element] = None

    def discard(self, element):
        """
            Remove new `element` anywhere in the container.
        """

        with suppress(KeyError):
            del self[element]

    def clear(self):
        """
            Remove all items from this dict.
        """
        self.empty_slots.clear()
        self.new_empty_slots.clear()

        self.keys_list.clear()
        self.values_list.clear()
        self.items_dictionary.clear()

