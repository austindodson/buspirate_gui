import sys, os, subprocess, time
from PyQt5.QtWidgets import QMainWindow, QApplication, \
    QPushButton, QWidget, QAction, QTabWidget,QVBoxLayout, QRadioButton, QGroupBox,\
    QHBoxLayout, QCheckBox, QLabel, QLineEdit, QTableWidget, QTableWidgetItem
from PyQt5 import QtCore
from PyQt5.QtGui import QIcon, QGuiApplication
from PyQt5.QtCore import pyqtSlot
import serial
from serial.tools import list_ports

global bp_location
global ser

def send(ser,cmd):
        """send the command and listen to the response."""
        byts = 0
        recvd = bytearray()
        update = bytes(1)
        if "[" in cmd and "r" in cmd:
            byts = int(cmd.split(":")[-1].strip("]"))
        print(cmd)
        ser.write(str(cmd+'\n').encode('ascii')) # send our command
        if byts > 512:
            print("greater")
            time.sleep(.5)
            recvd = ser.read(ser.inWaiting())
            time.sleep(.5)
            recvd += ser.read(ser.inWaiting())
            time.sleep(.5)
            recvd = ser.read(ser.inWaiting())
            time.sleep(.125)
            recvd = ser.read(ser.inWaiting())
            time.sleep(.125)
            recvd = ser.read(ser.inWaiting())
            time.sleep(.125)
            recvd = ser.read(ser.inWaiting())
            time.sleep(.125)
            recvd = ser.read(ser.inWaiting())
            time.sleep(.125)
            recvd = ser.read(ser.inWaiting())
        elif byts >= 128:
            while update != bytes("", "ascii"):
                update = ser.read(ser.inWaiting())
                time.sleep(.125)
                recvd.extend(update)
        elif byts == 0:
            time.sleep(.05)
            recvd = ser.read(ser.inWaiting())
        else:
            time.sleep(.125)
            recvd = ser.read(ser.inWaiting())
        print(recvd)
        return recvd

class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.title = 'buspirate'
        self.left = 0
        self.top = 0
        self.width = 600
        self.height = 1000
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        
        self.table_widget = MyTableWidget(self)
        self.setCentralWidget(self.table_widget)
        
        self.show()
    
class MyTableWidget(QWidget):
    
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        self.i2cspeed = 0 
        
        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tabs.resize(300,200)
        
        # Add tabs
        self.tabs.addTab(self.tab1,"I2C")
        self.tabs.addTab(self.tab2,"SPI")

        self.tab1.layout = QVBoxLayout(self)

        groupbox = QGroupBox("Connect")
        groupbox.setFixedSize(650,100)

        groupbox.setCheckable(False)
        self.tab1.layout.addWidget(groupbox)

        hbox = QHBoxLayout()
        groupbox.setLayout(hbox)
        
        '''
         1. ~5KHz
         2. ~50KHz
         3. ~100KHz
         4. ~400KHz
        '''
        # Add tabs to widget
        radiobutton = QRadioButton("~5KHz")
        radiobutton.speed = "~5KHz"
        radiobutton.index = 1
        radiobutton.toggled.connect(self.onClickedRadio)
        hbox.addWidget(radiobutton)

        radiobutton = QRadioButton("~50KHz")
        radiobutton.speed = "~50KHz"
        radiobutton.index = 2
        radiobutton.toggled.connect(self.onClickedRadio)
        hbox.addWidget(radiobutton)

        radiobutton = QRadioButton("~100KHz")
        radiobutton.speed = "~100KHz"
        radiobutton.index = 3
        radiobutton.toggled.connect(self.onClickedRadio)
        hbox.addWidget(radiobutton)

        radiobutton = QRadioButton("~400KHz")
        radiobutton.speed = "~400KHz"
        radiobutton.index = 4
        radiobutton.toggled.connect(self.onClickedRadio)
        hbox.addWidget(radiobutton)

        hbox.addStretch()

        self.pushButton1 = QPushButton("Connect BP to I2C")
        self.pushButton1.clicked.connect(self.onClickedButton)


        hbox.addWidget(self.pushButton1)
        self.tab1.setLayout(self.tab1.layout)

        self.connectionstatusLabel = QLabel("Not Connected")
        hbox.addWidget(self.connectionstatusLabel)

        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

        """
        " Power Options Box
        """
        groupboxpo = QGroupBox("Power Options")
        groupboxpo.setFixedSize(650,100)

        groupboxpo.setCheckable(False)
        

        hboxpo = QHBoxLayout()
        groupboxpo.setLayout(hboxpo)

        checkbox = QCheckBox("Power")
        checkbox.option = "Power"
        checkbox.state = -1
        checkbox.code = "w"
        checkbox.setChecked(False)
        checkbox.clicked.connect(self.toggle)
        hboxpo.addWidget(checkbox)

        checkbox = QCheckBox("PU Resistor")
        checkbox.option = "PU Resistor"
        checkbox.state = -1
        checkbox.code = "p"
        checkbox.setChecked(False)
        checkbox.clicked.connect(self.toggle)
        hboxpo.addWidget(checkbox)

        checkbox = QCheckBox("Aux")
        checkbox.option = "Aux"
        checkbox.state = -1
        checkbox.code = "a"
        checkbox.setChecked(False)
        checkbox.clicked.connect(self.toggle)
        hboxpo.addWidget(checkbox)

        hboxpo.addStretch()

        self.tab1.layout.addWidget(groupboxpo)


        """
        " Read Write Box
        """
        groupboxrw = QGroupBox("Read/Write")
        groupboxrw.setFixedSize(650,100)

        groupboxrw.setCheckable(False)
        

        hboxrw = QHBoxLayout()
        groupboxrw.setLayout(hboxrw)

        lbl = QLabel("Data Size")
        self.labelIn = QLineEdit()
        self.labelIn.setFixedSize(60,20)
        labelBtn = QPushButton("Submit")
        labelBtn.clicked.connect(self.onClickedSize)
        hboxrw.addWidget(lbl)
        hboxrw.addWidget(self.labelIn)
        hboxrw.addWidget(labelBtn)


        cmdLbl = QLabel("Cmd:")
        hboxpo.addStretch()
        self.cmd = QLineEdit()
        self.cmd.setFixedSize(250,20)
        hboxrw.addWidget(cmdLbl)
        hboxrw.addWidget(self.cmd)

        self.pushButton2 = QPushButton("Send")
        self.pushButton2.clicked.connect(self.onClickedCmd)
        hboxrw.addWidget(self.pushButton2)


        self.tab1.layout.addWidget(groupboxrw)

        self.dataBox = QTableWidget()
        self.dataBox.setRowCount(8)
        self.dataBox.setColumnCount(8)
        self.tab1.layout.addWidget(self.dataBox)

    def onClickedSize(self):
        print(self.labelIn.text())
        self.dataBox.setRowCount(int(self.labelIn.text())/8)
        self.dataBox.repaint()

    def onClickedCmd(self):
        global ser
        if ser.isOpen():
            text = self.cmd.text()
            recvd = send(ser, text).decode("ascii")
            if "READ:" in recvd:
                data = recvd.split("READ:")[-1]
                data_list = data.split()
                row = 0
                column = 0
                for i in data_list:
                    entry = i
                    if entry == "ACK" or entry == "STOP" or entry == "I2C>" or entry == "BIT" or entry == "NACK" or entry == "I2C":
                        continue
                    else:
                        self.dataBox.setItem(row,column, QTableWidgetItem(i))
                        column+=1
                        if column ==8:
                            row+=1
                            column =0 
                self.dataBox.repaint()


    def toggle(self):
        global ser
        checkBox = self.sender()
        checkBox.state = checkBox.state*-1
        if checkBox.state == 1:
            print(checkBox.code.upper())
            if ser.isOpen():
                send(ser, checkBox.code.upper())
        else:
            print(checkBox.code)
            if ser.isOpen():
                send(ser, checkBox.code)

    def onClickedRadio(self):
        radioButton = self.sender()
        if radioButton.isChecked():
            print("Speed is " + radioButton.speed + " index "+ str(radioButton.index))
            self.i2cspeed = radioButton.index

    def onClickedButton(self):
        global bp_location
        global ser

        button = self.sender()
        if self.i2cspeed == 0:
            self.connectionstatusLabel.setText("Not Connected")
            self.connectionstatusLabel.setStyleSheet('color: red')
            self.connectionstatusLabel.repaint()
            return
        print("Opening buspirate with speed: " + str(self.i2cspeed))
        ser = serial.Serial(bp_location, 115200)
        try:
            assert ser.isOpen()
            self.connectionstatusLabel.setText("Connected")
            self.connectionstatusLabel.setStyleSheet('color: green')
            self.connectionstatusLabel.repaint()
            button.setEnabled(False)
        except:
            self.connectionstatusLabel.setText("Connection Error")
            self.connectionstatusLabel.setStyleSheet('color: red')
            self.connectionstatusLabel.repaint()
            return
        print(ser.name)
        
        ser.write("\r".encode('ascii'))
        time.sleep(.05)
        print(ser.read(ser.inWaiting()))
        send(ser, '#')
        send(ser,'m')
        send(ser, '4')
        send(ser, str(self.i2cspeed))

if __name__ == '__main__':
    global bp_location
    x = list(list_ports.comports())
    for dev in x:
        dev_info = str(dev)
        if "usbserial" in dev_info.split(" - ")[0] or "ACM" in dev_info.split(" - ")[0]:
            bp_location = dev_info.split(" - ")[0]
            print(bp_location)
    print(bp_location)
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())


