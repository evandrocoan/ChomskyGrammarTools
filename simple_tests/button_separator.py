#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys


import PyQt5

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QGridLayout

def main():
    app = QtWidgets.QApplication( sys.argv )
    programWindow = ProgramWindow()

    programWindow.show()
    sys.exit( app.exec_() )

class ProgramWindow(QtWidgets.QMainWindow):
    """
        How to increase QFrame.HLine line separator width and distance with the other buttons?
        https://stackoverflow.com/questions/50825126/how-to-increase-qframe-hline-line-separator-width-and-distance-with-the-other-bu
    """

    def __init__(self):
        QtWidgets.QMainWindow.__init__( self )
        self.setup_main_window()
        self.create_input_text()
        self.set_window_layout()

    def setup_main_window(self):
        self.resize( 400, 300  )
        self.centralwidget = QWidget()
        self.setCentralWidget( self.centralwidget )

    def create_input_text(self):
        self.separatorLine = QFrame()
        self.separatorLine.setFrameShape( QFrame.HLine )
        self.separatorLine.setFrameShadow( QFrame.Raised )

        self.separatorLine.setLineWidth( 150 )
        self.separatorLine.setMidLineWidth( 150 )

        rect = self.separatorLine.frameRect()
        print( "frameShape: %s" % rect )
        print( "width: %s" % self.separatorLine.width() )
        print( "height: %s" % self.separatorLine.height() )

        self.redoButton = QPushButton( "Redo Operations" )
        self.calculate  = QPushButton( "Compute and Follow" )
        self.open       = QPushButton( "Open File" )
        self.save       = QPushButton( "Save File" )

        self.verticalGridLayout = QGridLayout()
        self.verticalGridLayout.addWidget( self.redoButton    , 1 , 0)
        self.verticalGridLayout.addWidget( self.calculate     , 2 , 0)
        self.verticalGridLayout.addWidget( self.separatorLine , 3 , 0)
        self.verticalGridLayout.addWidget( self.open          , 4 , 0)
        self.verticalGridLayout.addWidget( self.save          , 5 , 0)
        self.verticalGridLayout.setSpacing( 0 )
        self.verticalGridLayout.setRowMinimumHeight(3, 20)
        self.verticalGridLayout.setAlignment(Qt.AlignTop)

        self.innerLayout = QHBoxLayout()
        self.innerLayout.addLayout( self.verticalGridLayout )

    def set_window_layout(self):
        main_vertical_layout = QVBoxLayout( self.centralwidget )
        main_vertical_layout.addLayout( self.innerLayout )

if __name__ == "__main__":
    main()

