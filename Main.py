#!/usr/bin/python
# Import PyQT module
from PyQt4 import QtGui,QtCore
# Import MainWindow class from QT Designer
from MainWindow import Ui_MainWindow
from Progress import Ui_Progress
import zproject
import crop

#from RunProcessing import *
import sys
import subprocess
import os
import re
# cPickle is faster than pickel and is pretty much the same
import pickle
import pprint
import time
import shutil
import uuid
from multiprocessing import Process
from PyQt4.uic.Compiler.qtproxies import QtCore
try:
    import Image
except ImportError:
    from PIL import Image

class MainWindow(QtGui.QMainWindow):
    '''
    Class to provide the main window for the Image processing GUI.
    Basically extend the QMainWindow class (from MainWindow.py) generated by QT Designer

    Also shows a dialog box after a submission the dialog box will then keep a track of the
    image processing (not yet developed).
    '''

    def __init__(self):
       '''  Constructor: Checks for buttons which have been pressed and responds accordingly. '''

       # Standard setup of class from qt designer Ui class
       super(MainWindow, self).__init__()
       self.ui=Ui_MainWindow()
       self.ui.setupUi(self)

       # Make unique ID if this is the first time mainwindow has been called
       self.unique_ID = uuid.uuid1()
       print "ID for session:"+str(self.unique_ID)

       # Initialise modality variable
       self.modality = "Not_selected"
       self.selected = "Not_selected"
       self.error = "None"
       self.stop = None


       # initialise non essential information
       self.scan_folder = ""
       self.recon_log_path = ""
       self.f_size_out_gb = ""
       self.pixel_size = ""


       # get input folder
       self.ui.pushButtonInput.clicked.connect(self.selectFileIn)

       # Get output folder
       self.ui.pushButtonOutput.clicked.connect(self.selectFileOut)

       # OPT selection
       self.ui.radioButtonOPT.clicked.connect(self.getOPTonly)

       # uCT selection
       self.ui.radioButtonuCT.clicked.connect(self.getuCTonly)

       # If Go button is pressed move onto track progress dialog box
       self.ui.pushButtonGo.clicked.connect(self.processGo)

       # Set cropping options
       # Auto crop (disable buttons)
       self.ui.radioButtonAuto.clicked.connect(self.manCropOff)
       # No crop (disable buttons)
       self.ui.radioButtonNo.clicked.connect(self.manCropOff)
       # Man crop (enable buttons).
       self.ui.radioButtonMan.clicked.connect(self.manCropOn)
       # If the get dimensions button is pressed
       self.ui.pushButtonGetDimensions.clicked.connect(self.getDimensions)

       #Get the output folder name when input updated
       self.ui.lineEditOutput.textChanged.connect(self.outputFolderChanged)
       self.ui.lineEditInput.textChanged.connect(self.inputFolderChanged)

       # Get recon file manually
       self.ui.pushButtonCTRecon.clicked.connect(self.getReconMan)

       # Get scan file manually
       self.ui.pushButtonScan.clicked.connect(self.getScanMan)

       # Get SPR file manually
       self.ui.pushButtonCTSPR.clicked.connect(self.getSPRMan)

       # Update name
       self.ui.pushButtonUpdate.clicked.connect(self.updateName)


       # to make the window visible
       self.show()



    def check(self):
        print "asdsada"

    def selectFileIn(self):
        ''' Get the info for the selected file'''
        self.fileDialog = QtGui.QFileDialog(self)
        folder = self.fileDialog.getExistingDirectory(self, "Select Directory")

        if folder == "":
            print "User has pressed cancel"
        else :
            self.ui.lineEditInput.setText(folder)
            self.getName()

            if self.error == "None" :
                self.autoFileOut()

            if self.error == "None" :
                self.getReconLog()

            if self.error == "None" :
                self.autouCTOnly()

            if self.error == "None" :
                self.folderSizeApprox()

            self.error = "None"


    def selectFileOut(self):
        ''' Select output folder (this should be blocked as standard'''
        self.fileDialog = QtGui.QFileDialog(self)
        folder = self.fileDialog.getExistingDirectory(self, "Select Directory")
        if folder == "":
            print "User has pressed cancel"
        else:
            self.ui.lineEditOutput.setText(folder)


    def inputFolderChanged(self, text):
        self.inputFolder = text

    def outputFolderChanged(self, text):
        self.outputFolder = text

    def cropCallback(self, box):
        print "callback test:", box
        self.ui.lineEditX.setText(str(box[0]))
        self.ui.lineEditY.setText(str(box[1]))
        self.ui.lineEditW.setText(str(box[2]))
        self.ui.lineEditH.setText(str(box[3]))

    def getDimensions(self):
        ''' Perform a z projection and then allows user to crop based on z projection'''
        #

        dir = os.path.dirname(os.path.abspath(__file__))

        # Opens MyMainWindow from crop.py
        input_folder = str(self.ui.lineEditInput.text())
        output_folder = str(self.ui.lineEditOutput.text())
        print input_folder
        zproj_path = os.path.join(str(self.outputFolder), "z_projection")
        self.stop = None

        if self.ui.checkBoxRF.isChecked():
            print "CheckBox has been checked so files will be replaced\n"
            if os.path.exists(zproj_path):
                print "zproj exists"
            else :
                os.makedirs(zproj_path)
            self.stop = None
        elif os.path.exists(zproj_path):
            print "Output folder for z project already exists and user has not approved overwrite"
            # Running dialog box to inform user of options
            message = QtGui.QMessageBox.question(self, 'Message', 'Folder already exists for Z projection. Can this file be overwritten?', QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            if message == QtGui.QMessageBox.Yes:
                self.stop = None
            if message == QtGui.QMessageBox.No:
                self.stop = True
        else :
            try:
                print "Creating output folder"
                os.makedirs(zproj_path)
                self.stop = None
            except IOError as e:
                print("cannot make directory for saving the z-projection: {0}".format(e))

        if self.stop == None :

            self.ui.textEditStatusMessages.setText("Z-projection in process, please wait")
            p = subprocess.Popen(["python", dir+"/zproject.py",input_folder,output_folder],stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print "Waiting"
            QtCore.QCoreApplication.processEvents()
            #message = QtGui.QMessageBox.information(self, 'Message', 'Maximum intensity (z projection) of slices is being calculated, press OK and the Z projection image will pop up when ready.')
            out, err = p.communicate()
            print out
            print err
            self.ui.textEditStatusMessages.setText("Z-projection finished")
            #self.ui.label_zwait.setText("z project done")
            self.runCrop(os.path.join(str(self.outputFolder), "z_projection", "max_intensity_z.tif"))
            self.ui.textEditStatusMessages.setText("Dimensions selected")


    def runCrop(self, img_path):
        cropper = crop.Crop(self.cropCallback, img_path, self)
        cropper.show()



    def manCropOff(self):
        ''' disables boxes for cropping manually '''
        self.ui.lineEditX.setEnabled(False)
        self.ui.lineEditY.setEnabled(False)
        self.ui.lineEditW.setEnabled(False)
        self.ui.lineEditH.setEnabled(False)
        self.ui.pushButtonGetDimensions.setEnabled(False)

    def manCropOn(self):
        ''' enables boxes for cropping manually '''
        self.ui.lineEditX.setEnabled(True)
        self.ui.lineEditY.setEnabled(True)
        self.ui.lineEditW.setEnabled(True)
        self.ui.lineEditH.setEnabled(True)
        self.ui.pushButtonGetDimensions.setEnabled(True)


    def getOPTonly(self):
        ''' unchecks uCT box (if checked) and checks OPT group box and creates or edits self.modality '''
        self.ui.groupBoxOPTOnly.setChecked(True)
        self.ui.groupBoxuCTOnly.setChecked(False)
        self.modality = "OPT"

    def getuCTonly(self):
        ''' Simply unchecks OPTT box (if checked) and checks group uCT box and creates or edits self.modality '''
        self.ui.groupBoxOPTOnly.setChecked(False)
        self.ui.groupBoxuCTOnly.setChecked(True)
        self.modality = "MicroCT"

    def folderSizeApprox(self):
        '''
        Gets the approx folder size of the original recon folder and updates the main window with
        this information. Calculating the folder size by going through each file takes a while on janus. This
        function just checks the first recon file and then multiples this by the number of recon files.

        Updates the following qt objects: labelFile, lcdNumberFile

        Creates self.f_size_out_gb: The file size in gb
        '''

        # Get the input folder information
        input = str(self.ui.lineEditInput.text())

        # create a regex get example recon file
        prog = re.compile("(.*)_rec\d+\.(bmp|tif)",re.IGNORECASE)

        try:
            filename = ""
            # for loop to go through the directory
            for line in os.listdir(input) :
                line =str(line)
                #print line+"\n"
                # if the line matches the regex break
                if prog.match(line) :
                    filename = line
                    break

            filename = input+"/"+filename
            file1_size = os.stat(filename).st_size

            num_files = len([f for f in os.listdir(input) if ((f[-4:] == ".bmp") or (f[-4:] == ".tif") or
                          (f[-7:] != "spr.bmp") or (f[-7:] != "spr.tif") or (f[-4:] == ".BMP") or (f[-4:] == ".TIF") or
                          (f[-7:] != "spr.BMP") or (f[-7:] != "spr.TIF"))])


            approx_size = num_files*file1_size

            # convert to gb
            f_size_out =  (approx_size/(1024*1024*1024.0))

            # Save file size as an object to be used later
            self.f_size_out_gb = "%0.4f" % (f_size_out)

            #Clean up the formatting of gb mb
            self.sizeCleanup(f_size_out,approx_size)
        except:
            self.error = "Unexpected error in folder size calc:", sys.exc_info()[0]
            print "Unexpected error in folder size calc:", sys.exc_info()[0]



    def sizeCleanup(self,f_size_out,approx_size):
        # Check if size should be shown as gb or mb
        # Need to change file size to 2 decimal places
        if f_size_out < 0.05 :
            # convert to mb
            f_size_out =  (approx_size/(1024*1024.0))
            # make to 2 decimal places
            f_size_out =  "%0.2f" % (f_size_out)
            # change label to show mb
            self.ui.labelFile.setText("Folder size (Mb)")
            # update lcd display
            self.ui.lcdNumberFile.display(f_size_out)
        else :
            # display as gb
            # make to 2 decimal places
            f_size_out =  "%0.2f" % (f_size_out)
            # change label to show mb
            self.ui.labelFile.setText("Folder size (Gb)")
            # update lcd display
            self.ui.lcdNumberFile.display(f_size_out)


    def getName(self):
        '''
        Gets the id from the folder name. Then fills out the text boxes on the main window with the relevant information

        Updates the followi        input = str(self.ui.lineEditInput.text())ng qt objects: lineEditDate, ...   ...

        Creates ...
        '''
        # Get input folder
        input = str(self.ui.lineEditInput.text())

        # Get the folder name
        path,folder_name = os.path.split(input)

        try:
            # Need to have exception to catch if the name is not in correct format.
            # If the name is not in the correc format it should flag to the user that this needs to be sorted
            print folder_name.split("_")
            name_list = folder_name.split("_")
            date = name_list[0]
            group = name_list[1]
            age = name_list[2]
            litter = name_list[3]
            zygosity = name_list[4]
            sex = name_list[5]


            #print date,group,age,litter,zygosity
            self.ui.lineEditDate.setText(date)
            self.ui.lineEditGroup.setText(group)
            self.ui.lineEditAge.setText(age)
            self.ui.lineEditLitter.setText(litter)
            self.ui.lineEditZygosity.setText(zygosity)
            self.ui.lineEditSex.setText(sex)
            self.ui.lineEditName.setText(folder_name)

            # The full name should be made changable at some point..
            self.full_name = folder_name

        except IndexError as e:
            pass
            message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: Name ID is not in the correct format.\nAutocomplete of name is not possible.\n')
            print "Name incorrect", sys.exc_info()[0]
            self.full_name = ""
        except:
            print "Auto-populate not possible. Unexpected error:", sys.exc_info()[0]
            message = QtGui.QMessageBox.warning(self, 'Message', 'Auto-populate not possible. Unexpected error:',sys.exc_info()[0])

    def updateName(self):
        ''' Function to update the name of the file and folder'''
        self.full_name = str(self.ui.lineEditName.text())

        try :
            name_list = self.full_name.split("_")
            self.ui.lineEditDate.setText(name_list[0])
            self.ui.lineEditGroup.setText(name_list[1])
            self.ui.lineEditAge.setText(name_list[2])
            self.ui.lineEditLitter.setText(name_list[3])
            self.ui.lineEditZygosity.setText(name_list[4])
            self.ui.lineEditSex.setText(name_list[5])

        except IndexError as e:
            print "Name incorrect", sys.exc_info()[0]
            message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: Name ID is not in the correct format.\n')
            self.ui.lineEditDate.setText("")
            self.ui.lineEditGroup.setText("")
            self.ui.lineEditAge.setText("")
            self.ui.lineEditLitter.setText("")
            self.ui.lineEditZygosity.setText("")
            self.ui.lineEditSex.setText("")
        except:
            print "Auto-populate not possible. Unexpected error:", sys.exc_info()[0]
            message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: Unexpected error when updating name',sys.exc_info()[0])

        # Get output folder
        output = str(self.ui.lineEditOutput.text())
        path,output_folder_name = os.path.split(output)
        self.ui.lineEditOutput.setText(os.path.join(path,self.full_name))



    def autouCTOnly(self):
        ''' Automatically fills out the uCT only section    '''
        input = str(self.ui.lineEditInput.text())
        # Set recon log path
        self.ui.lineEditCTRecon.setText(str(self.recon_log_path))

        # Set the scan folder
        self.scan_folder  = input.replace("recons", "scan")
        self.ui.lineEditScan.setText(self.scan_folder)

        # Get the SPR file. Sometimes fiels are saved with upper or lower case file extensions
        # The following is bit of a stupid way of dealing with this problem but I think it works....
        SPR_file_bmp = os.path.join(input,self.full_name+"_spr.bmp")
        SPR_file_BMP = os.path.join(input,self.full_name+"_spr.BMP")
        SPR_file_tif = os.path.join(input,self.full_name+"_spr.tif")
        SPR_file_TIF = os.path.join(input,self.full_name+"_spr.TIF")
        print SPR_file_bmp
        if os.path.isfile(SPR_file_bmp):
            self.ui.lineEditCTSPR.setText(SPR_file_bmp)
        elif os.path.isfile(SPR_file_BMP):
            self.ui.lineEditCTSPR.setText(SPR_file_BMP)
        elif os.path.isfile(SPR_file_tif):
            self.ui.lineEditCTSPR.setText(SPR_file_tif)
        elif os.path.isfile(SPR_file_TIF):
            self.ui.lineEditCTSPR.setText(SPR_file_TIF)
        else:
            self.error = "Cannot find SPR file, proceed if this is not a problem"
            self.errorDialog = ErrorMessage(self.error)


        self.ui.lineEditScan.setText(self.scan_folder)


    def getReconMan(self):
        self.fileDialog = QtGui.QFileDialog(self)
        file = self.fileDialog.getOpenFileName()
        if file == "":
            print "User has pressed cancel"
        else :
            self.ui.lineEditCTRecon.setText(file)
            self.recon_log_path = os.path.abspath(file)

    def getScanMan(self):
        self.fileDialog = QtGui.QFileDialog(self)
        folder = self.fileDialog.getExistingDirectory(self, "Select Directory")
        if folder == "":
            print "User has pressed cancel"
        else :
            self.ui.lineEditScan.setText(folder)#


    def getSPRMan(self):
        self.fileDialog = QtGui.QFileDialog(self)
        file= self.fileDialog.getOpenFileName()
        if file == "":
            print "User has pressed cancel"
        else :
            self.ui.lineEditCTSPR.setText(file)

    def getReconLog(self):
        '''
        Gets the recon log from the original recon folder and gets the pixel size information

        Updates the following qt objects: ... ...   ...

        Creates ...
        '''

        input = str(self.ui.lineEditInput.text())

        # Get the folder name
        path,folder_name = os.path.split(input)

        try:
            # This will change depending on the location of the program (e.g linux/windows and what drive the MicroCT folder is set to)
            recon_log_path = os.path.join(path,folder_name,folder_name+".txt")

            # To make sure the path is in the correct format (not sure if necessary
            self.recon_log_path = os.path.abspath(recon_log_path)

            # Open the log file as read only
            recon_log_file = open(self.recon_log_path, 'r')

            # create a regex to pixel size
            prog = re.compile("^Pixel Size \(um\)\=(\w+.\w+)")

            # for loop to go through the recon log file
            for line in recon_log_file:
                # "chomp" the line endings off
                line = line.rstrip()
                # if the line matches the regex print the (\w+.\w+) part of regex
                if prog.match(line) :
                    self.pixel_size = prog.match(line).group(1)
                    break
            # Display the number on the lcd display
            self.ui.lcdNumberPixel.display(self.pixel_size)

        except IOError as e:
            self.error = "Error finding recon file. Error:",sys.exc_info()[0]
            print "Error finding recon file",sys.exc_info()[0]
            message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: Could not find recon log file')
        except:
            print "Unexpected error:", sys.exc_info()[0]
            message = QtGui.QMessageBox.warning(self, 'Message', 'Warning: Unexpected error getting recon log file',sys.exc_info()[0])


    def autoFileOut(self):
        ''' Get info for the output file and create a new folder NEED TO ADD CREATE FOLDER FUNCTION
        '''
        try :
            input = str(self.ui.lineEditInput.text())
            # Get the folder name
            path,folder_name = os.path.split(input)

            output_path  = path.replace("recons", "processed recons")
            output_full = os.path.join(output_path,self.full_name)
            self.ui.lineEditOutput.setText(output_full)

        except:
            self.error = "Unexpected error in getting new folder output name", sys.exc_info()[0]
            print "Unexpected error in getting new folder output name:", sys.exc_info()[0]
            self.errorDialog = ErrorMessage(self.error)




    def processGo(self):
        '''
        This will set off all the processing scripts and shows the dialog box to keep track of progress
        '''
        print "\nOpen progress report for user"

        # Get the directory of the script
        dir = os.path.dirname(os.path.abspath(__file__))

        # Perform some checks before any processing is carried out
        self.errorCheck()

        if self.stop == None :

            self.close()

            self.getParamaters()

            # Perform analysis
            #runPro_p = subprocess.Popen(["python", dir+"/RunProcessing.py", "-i",self.config_path],stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Show progress dialog window to keep track of what is being processed
            self.pro = Progress(self.configOb)

            # Run the programs. A script needs to be written to run on linux to run the back end processing


    def errorCheck(self):
        '''
        To check the required inputs for the processing to be run
        '''
        # Get input and output folders (As the text is always from the text box it will hopefully keep track of
        #any changes the user might have made
        inputFolder = str(self.ui.lineEditInput.text())
        outputFolder = str(self.ui.lineEditOutput.text())

        # Input folder contains image files

        if self.ui.checkBoxRF.isChecked():
            print "CheckBox has been checked so files will be replaced\n"
            # Too dangerous to delete everything in a folder
            # shutil.rmtree(outputFolder)
            # os.makedirs(outputFolder)
            self.stop = None
        # Check if output folder already exists. Ask if it is ok to overwrite
        elif os.path.exists(outputFolder):
            print "Output folder already exists and user has not approved overwrite"
            # Running dialog box to inform user of options
            message = QtGui.QMessageBox.question(self, 'Message', 'Folder already exists for the location:\n{0}\nCan this folder be overwritten?'.format(outputFolder) , QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            if message == QtGui.QMessageBox.Yes:
                self.stop = None
            if message == QtGui.QMessageBox.No:
                self.stop = True
        else :
            print "Creating output folder"
            os.makedirs(outputFolder)
            self.stop = None


        # Check if name has been completed




    def getParamaters(self):
        '''
        Creates the config file for future processing
        '''
        # Get input and output folders (As the text is always from the text box it will hopefully keep track of
        #any changes the user might have made
        inputFolder = str(self.ui.lineEditInput.text())
        outputFolder = str(self.ui.lineEditOutput.text())

        #### Write to config file ####
        self.configOb = ConfigClass()

        # Create a folder for the metadata
        self.meta_path = os.path.join(outputFolder,"Metadata")
        if not os.path.exists(self.meta_path):
            os.makedirs(self.meta_path)

        # OS path used for compatibility issues between Linux and windows directory spacing
        self.config_path = os.path.join(self.meta_path,"configObject.txt")
        self.log_path = os.path.join(self.meta_path,"config4user.log")

        # Create config file and log file
        config = open(self.config_path, 'w')
        log = open(self.log_path, 'w')


        ##### Get cropping option #####
        if self.ui.radioButtonMan.isChecked() :
            xcrop = str(self.ui.lineEditX.text())
            ycrop = str(self.ui.lineEditY.text())
            wcrop = str(self.ui.lineEditW.text())
            hcrop = str(self.ui.lineEditH.text())
            crop = "Manual"
        elif self.ui.radioButtonAuto.isChecked() :
            crop = "Automatic"
        elif self.ui.radioButtonNo.isChecked() :
            crop = "No_crop"

        ##### Get Scaling factors ####
        if self.ui.checkBoxSF2.isChecked() :
            SF2 = "yes"
        else :
            SF2 = "no"

        if self.ui.checkBoxSF3.isChecked() :
            SF3 = "yes"
        else :
            SF3 = "no"

        if self.ui.checkBoxSF4.isChecked() :
            SF4 = "yes"
        else :
            SF4 = "no"


        # ID for session
        self.configOb.unique_ID = str(self.unique_ID)
        self.configOb.config_path = self.config_path
        self.configOb.full_name = self.full_name
        self.configOb.input_folder = inputFolder
        self.configOb.output_folder = outputFolder
        self.configOb.scan_folder = self.scan_folder
        self.configOb.meta_path = self.meta_path
        self.configOb.crop_option = str(crop)
        if crop =="Manual" :
            self.configOb.xcrop = xcrop
            self.configOb.ycrop = ycrop
            self.configOb.wcrop = wcrop
            self.configOb.hcrop = hcrop
            self.configOb.crop_manual = xcrop+" "+ycrop+" "+wcrop+" "+hcrop
        else :
            self.configOb.crop_manual = "Not_applicable"

        self.configOb.SF2 = SF2
        self.configOb.SF3 = SF3
        self.configOb.SF4 = SF4
        self.configOb.recon_log_file = self.recon_log_path
        self.configOb.recon_folder_size = self.f_size_out_gb
        self.configOb.recon_pixel_size = self.pixel_size

        # If using windows it is important to put \ at the end of folder name
        # Combining scaling and SF into input for imageJ macro
        self.configOb.cropped_path = os.path.join(self.configOb.output_folder,"cropped")
        self.configOb.scale_path = os.path.join(self.configOb.output_folder,"scaled_stacks")
        self.configOb.imageJ = self.configOb.cropped_path+os.sep+':'+self.configOb.scale_path+os.sep+":"+self.configOb.full_name

        # write the config information into an easily readable log file
        log.write("Session_ID    "+self.configOb.unique_ID+"\n");
        log.write("full_name    "+self.configOb.full_name+"\n");
        log.write("Input_folder    "+self.configOb.input_folder+"\n");
        log.write("Output_folder    "+self.configOb.output_folder+"\n");
        log.write("Scan_folder    "+self.configOb.scan_folder+"\n");
        log.write("Crop_option    "+self.configOb.crop_option+"\n");
        log.write("Crop_manual    "+self.configOb.crop_manual+"\n");
        log.write("Downsize_by_factor_2?    "+self.configOb.SF2+"\n");
        log.write("Downsize_by_factor_3?    "+self.configOb.SF3+"\n");
        log.write("Downsize_by_factor_4?    "+self.configOb.SF4+"\n");
        log.write("ImageJconfig    "+self.configOb.imageJ+"\n");
        log.write("Recon_log_file    "+self.configOb.recon_log_file+"\n");
        log.write("Recon_folder_size   "+self.configOb.recon_folder_size+"\n");
        log.write("Recon_pixel_size  "+self.configOb.recon_pixel_size+"\n");

        # Pickle the class to a file
        pickle.dump(self.configOb, config)

        config.close()
        log.close()


class ConfigClass :
    '''
    A simple Class is used to transfer config information
    '''
    def __init__(self):

        print "ConfigClass init"



# For some reason need to re-import PyQt4...... Not the best solution but seems to work
from PyQt4 import QtCore, QtGui

class Progress(QtGui.QDialog):
    '''
    Class to provide the dialog box to monitor current Image processing jobs.
    Basically extend the QDialog class (from Progress.py) generated by QT Designer
    '''

    # Create a constructor
    def __init__(self,configOb):
        print "Progress has started"
        self.threadPool = []
        super(Progress, self).__init__()
        self.ui=Ui_Progress()
        self.ui.setupUi(self)
        self.show()
        self.configOb = configOb
        self.value = 0

        self.ui.label_1.setText(configOb.full_name)

        self.thread(configOb)

        self.ui.pushButtonAddMore.clicked.connect(self.AddMore)

    def AddMore(self):
        dir = os.path.dirname(os.path.abspath(__file__))
        runPro_p = subprocess.Popen(["python", dir+"/Main.py"],stdout=subprocess.PIPE, stderr=subprocess.PIPE)


    def add(self,test):
        self.ui.label1_tracking.setText(test)

        if test == "Processing finished" :
            self.ui.progressBar_1.setValue(100)

        if test == "Crop finished" :
            self.ui.progressBar_1.setValue(50)

        print test
        value = 0

#         print self.value
#         while not test == "Processing finished":
#             print "while loop started"
#             print "loop",value
#             time.sleep(0.1)
#             QtCore.QCoreApplication.processEvents()
#             value = self.ui.progressBar_1.value() + 1
#
#             if test == "Processing finished" :
#                  self.ui.progressBar_1.setValue(100)
#                  break
#             if (self.value == 100):
#                  break
#             self.ui.progressBar_1.setValue(value)
#             QtGui.qApp.processEvents()


    def thread(self,configOb):
        self.threadPool = []
        self.threadPool.append( WorkThread(configOb) )
        self.connect( self.threadPool[len(self.threadPool)-1], QtCore.SIGNAL("update(QString)"), self.add )
        self.threadPool[len(self.threadPool)-1].start()



class WorkThread(QtCore.QThread):
    def __init__(self,configOb):
        QtCore.QThread.__init__(self)
        self.configOb = configOb

    def __del__(self):
        self.wait()

    def run(self):
        self.emit( QtCore.SIGNAL('update(QString)'), "Started Processing" )
        # Get the directory of the script
        self.dir = os.path.dirname(os.path.realpath(__file__))
        # Get the session log file
        self.session_log_path = os.path.join(self.configOb.meta_path,self.configOb.full_name+"_session.log")

        # Save as object to print to
        session = open(self.session_log_path, 'w+')
        session.write("Name of recon:"+self.configOb.full_name+"\n")

        ###############################################
        # Cropping
        ###############################################
        # Make crop folder
        # get cropped path from config object (shorten it so it is easier to read)
        cropped_path = self.configOb.cropped_path

        if not os.path.exists(cropped_path):
            os.makedirs(cropped_path)

        crop_run = os.path.join(self.dir, "autocrop.py")
        print crop_run
        if self.configOb.crop_option == "Manual" :
            session.write("########################Performing manual crop########################\n")
            self.emit( QtCore.SIGNAL('update(QString)'), "Performing manual crop" )

            manpro = subprocess.call(["python", crop_run,"-i",self.configOb.input_folder,"-o",
                         cropped_path, "-t", "tif","-d",self.configOb.xcrop, self.configOb.ycrop, self.configOb.wcrop, self.configOb.hcrop],
                            stdout=session, stderr=session)
            self.emit( QtCore.SIGNAL('update(QString)'), "Crop finished" )
            session.write("########################Crop finished########################\n")

        # Perform the automatic crop if required
        if self.configOb.crop_option == "Automatic" :
            session.write("########################Performing autocrop########################\n")
            self.emit( QtCore.SIGNAL('update(QString)'), "Performing autocrop" )

            aupro = subprocess.call(["python", crop_run,"-i",self.configOb.input_folder,"-o", cropped_path, "-t", "tif"],
                            stdout=session, stderr=session)
            self.emit( QtCore.SIGNAL('update(QString)'), "Crop finished" )
            session.write("########################Crop finished########################\n")

        # Do not perform any crop as user specified
        if self.configOb.crop_option == "None" :
            self.emit( QtCore.SIGNAL('update(QString)'), "No Crop carried out" )
            print "No crop carried out"
            session.write("No crop carried out\n")

        ###############################################
        # Copying of other files from recon directory
        ###############################################
        session.write("Copying other files from recon\n")
        for file in os.listdir(self.configOb.input_folder):
            suffix_txt, suffix_spr, suffix_log, suffix_crv = ".txt","spr",".log",".crv"
            if file.endswith((".txt",".log",".crv")) or re.search('spr', file, re.IGNORECASE):
                session.write("File"+file+"\n")
                file = os.path.join(self.configOb.input_folder,file)
                shutil.copy(file,cropped_path)

        ###############################################
        # Compression
        ###############################################
        #subprocess.call(["tar", "-cjf" check.tar.bz2 test
         #                   stdout=session, stderr=session)
        #self.emit( QtCore.SIGNAL('update(QString)'), "Crop finished" )


        ###############################################
        # Scaling
        ###############################################
        # First make subfolder for scaled stacks
        if not os.path.exists(self.configOb.scale_path):
            os.makedirs(self.configOb.scale_path)

        # Perform scaling as subprocess with Popen (they should be done in the background)
        if self.configOb.SF2 == "yes" :
            proSF2 = self.executeImagej(":0.5:x2")

        if self.configOb.SF3 == "yes" :
            proSF3 = self.executeImagej(":0.3333:x3")

        if self.configOb.SF4 == "yes" :
            proSF4 = self.executeImagej(":0.25:x4")

        if self.configOb.SF2 == "yes" :
            out2, err2 = proSF2.communicate()
            session.write(out2)
            session.write(err2)

        if self.configOb.SF3 == "yes" :
            out3, err3 = proSF3.communicate()
            session.write(out3)
            session.write(err3)

        if self.configOb.SF4 == "yes" :
            out4, err4 = proSF4.communicate()
            session.write(out4)
            session.write(err4)

        session.close()
        self.emit( QtCore.SIGNAL('update(QString)'), "Processing finished" )


    def executeImagej(self, scaleFactor):
        '''
        @param: str, scaleFactor eg ":0.5"
        '''
        self.emit( QtCore.SIGNAL('update(QString)'), "Performing scaling ({})".format(scaleFactor) )
        process = subprocess.Popen(["java", "-jar", "/usr/share/java/ij.jar", "-batch", os.path.join(self.dir, "siah_scale.txt"),
                                    self.configOb.imageJ + scaleFactor],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        return process


def main():
    app = QtGui.QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()