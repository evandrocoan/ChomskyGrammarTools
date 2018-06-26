#! /usr/bin/env python
# -*- coding: utf-8 -*-

#
# Licensing
#
# Run Functions Asynchronously
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

from PyQt5 import QtGui
from PyQt5 import QtCore

from PyQt5.QtCore import Qt
from debug_tools import getLogger

from .utilities import ignore_exceptions

# level 4 - Abstract Syntax Tree Parsing
log = getLogger( 127-4, __name__ )


class RunFunctionAsyncThread(QtCore.QThread):
    """
        Dynamically updates the user interface with new sentences generated by the program.
    """

    ## Send the given `function` full or partial results to the `results_dialog` window
    send_string_signal = QtCore.pyqtSignal( [str] )

    ## Disables the `results_dialog` window stop button when the function has finished it given task
    disable_stop_button_signal = QtCore.pyqtSignal()

    ## Save the current caret/cursor position to restore it later
    save_cursor_position_signal = QtCore.pyqtSignal()

    ## Restore the saved cursor/caret position by `save_cursor_position_signal`
    restore_cursor_position_signal = QtCore.pyqtSignal()

    ## Restore the saved cursor/caret position by `save_cursor_position_signal`
    set_scroll_to_maximum_signal = QtCore.pyqtSignal()

    def __init__(self, function, initial_message):
        """
            Qt- What is the difference between new QThread(this) and new QThread()?
            https://stackoverflow.com/questions/46293674/qt-what-is-the-difference-between-new-qthreadthis-and-new-qthread
        """
        QtCore.QThread.__init__(self)

        ## The function which will run asynchronously on this background thread
        self.function = function

        ## The initial message to display right after the the computation is finished
        self.initial_message = initial_message

        ## The thread which will continually running the given `function`
        self.process_thread = None

        ## Determines whether the waiting message was displayed one or not
        self.has_showed_waiting = False

        if hasattr( function, 'force_first_run' ):
            ## Whether or not the to force the `waiting` function to run at least one time, as it
            ## can some time never be called
            self.force_first_run = True

        else:
            self.force_first_run = False

        if hasattr( function, 'waiting' ):
            ## A function to perform some periodic task one the thread has started
            self.waiting = function.waiting

        else:

            def default(self):
                self.send_string_signal.emit( "Computing... No results available yet... " )
                self.sleep( 1 )

            self.waiting = default

    @ignore_exceptions
    def run(self):
        """
            Process asynchronously in background the given function.

            After starting, periodically calls each second the function `self.waiting()`.
        """

        class ProcessThread(QtCore.QThread):

            def __init__(self, parent, function):
                QtCore.QThread.__init__(self, parent)
                self.function = function

            def run(self):
                self.function()

        self.process_thread = ProcessThread( self.parent(), self.function )
        self.process_thread.start()

        force_first_run = self.force_first_run
        self.sleep( 1 )

        while self.process_thread.isRunning() or force_first_run:
            force_first_run = False
            self.has_showed_waiting = True

            self.set_scroll_to_maximum_signal.emit()
            self.waiting( self )

            if self.function.isToStop[0]:
                self.sleep( 1 )

                if self.process_thread.isRunning():
                    self.process_thread.terminate()

        # If it was not stopped by the close event setting isToStop, then append the success message
        self.process_thread.wait()
        self.send_string_signal.emit( self.initial_message )

        if self.has_showed_waiting:
            self.send_string_signal.emit("")

        self.save_cursor_position_signal.emit()
        self.send_string_signal.emit( self.function.results )
        self.msleep( 300 )

        self.disable_stop_button_signal.emit()
        self.restore_cursor_position_signal.emit()


@ignore_exceptions
def run_function_async(function, results_dialog, initial_message):
    """
        Create the updating thread and connect
        it's received signal to append
        every received chunk of data/text will be appended to the text
    """
    qtUpdateThread = RunFunctionAsyncThread( function, initial_message )
    qtUpdateThread.send_string_signal.connect( results_dialog.appendText )
    qtUpdateThread.disable_stop_button_signal.connect( results_dialog.disableStopButton )
    qtUpdateThread.save_cursor_position_signal.connect( results_dialog.saveCursorPosition )
    qtUpdateThread.restore_cursor_position_signal.connect( results_dialog.restoreCursorPosition )
    qtUpdateThread.set_scroll_to_maximum_signal.connect( results_dialog.setScrollToMaximum )
    qtUpdateThread.start()

    # Block QMainWindow while child widget is alive, pyqt
    # https://stackoverflow.com/questions/22410663/block-qmainwindow-while-child-widget-is-alive-pyqt
    results_dialog.setWindowModality( Qt.ApplicationModal )
    results_dialog.show()

    return qtUpdateThread

