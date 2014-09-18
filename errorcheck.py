from PyQt4 import QtGui, QtCore
import os
import re


def errorCheck(self):
    """ To check the required inputs and parameters. Gives messages for problems encountered


    :param obj self:
        Although not technically part of the class, can still use this method as if it was part of the HARP class.
    :ivar Boolean self.stop: Switch. True if adding to the processing list should be stopped. None if it is ok
    """

    # Get input and output folders (As the text is always from the text box it will hopefully keep track of
    #any changes the user might have made
    inputFolder = str(self.ui.lineEditInput.text())
    outputFolder = str(self.ui.lineEditOutput.text())

    # reset the stop switch
    self.stop = None

    # Check input and output folders assigned
    if not inputFolder :
        QtGui.QMessageBox.warning(self, 'Message', 'Warning: input directory not defined')
        self.stop = True
        return

    if not outputFolder :
        QtGui.QMessageBox.warning(self, 'Message', 'Warning: output directory not defined')
        self.stop = True
        return

    # Check if input folder exists
    if not os.path.exists(inputFolder):
        QtGui.QMessageBox.warning(self, 'Message', 'Warning: input folder does not exist')
        self.stop = True
        return

    # Check if a directory
    if not os.path.isdir(inputFolder):
        QtGui.QMessageBox.warning(self, 'Message', 'Warning: input folder is not a directory')
        self.stop = True
        return

    #Check if folder is empty
    if os.listdir(inputFolder) == []:
        QtGui.QMessageBox.warning(self, 'Message', 'Warning: input folder is empty')
        self.stop = True
        return

    #Check if input folder contains any image files
    prog = re.compile("(.*).(bmp|tif|jpg|jpeg)",re.IGNORECASE)

    file_check = None
    # for loop to go through the directory
    for line in os.listdir(inputFolder) :
        line =str(line)
        #print line+"\n"
        # if the line matches the regex break
        if prog.match(line):
            file_check = True
            break

    if file_check:
        self.stop = None
    else:
        QtGui.QMessageBox.warning(self, 'Message', 'Warning: input folder does not contain image files')
        self.stop = True
        return


    # Check if scan folder available if compression is required
    if self.ui.checkBoxScansReconComp.isChecked():
        if self.scan_folder == "":
            QtGui.QMessageBox.warning(self, 'Message', 'Warning: Scan folder not defined')
            self.stop = True
            return
        elif not os.path.exists(self.scan_folder):
            QtGui.QMessageBox.warning(self, 'Message', "Warning: Scan folder does not exist")
            self.stop = True
            return

    # Check pixel size is a number
    if self.ui.checkBoxPixel.isChecked() :

        try:
            float(self.ui.lineEditPixel.text())
        except ValueError:
            if not self.ui.lineEditPixel.text():
                QtGui.QMessageBox.warning(self, 'Message', 'Warning: User has not specified a new pixel size value')
                self.stop = True
                return
            else :
                QtGui.QMessageBox.warning(self, 'Message', 'Warning: User defined pixel is not a numerical value')
                self.stop = True
                return

    # Check user has not selected to scale by pixel without having a recon folder
    if self.ui.checkBoxPixel.isChecked() and self.pixel_size == "":
        QtGui.QMessageBox.warning(self, 'Message',
                                  'Warning: Pixel size could not be obtained from original recon log. Scaling '
                                  '"By Pixel (um) is not possible"')
        self.stop = True
        return

    # Check cropping parameters ok
    if self.ui.radioButtonMan.isChecked():
        try:
            testing = float(self.ui.lineEditX.text())
            testing = float(self.ui.lineEditY.text())
            testing = float(self.ui.lineEditW.text())
            testing = float(self.ui.lineEditH.text())
        except ValueError:
            QtGui.QMessageBox.warning(self, 'Message', 'Warning: Cropping dimensions have not been defined')
            self.stop = True
            return

    # Check input directory contains something
    if os.listdir(inputFolder) == []:
        QtGui.QMessageBox.warning(self, 'Message', 'Warning: input folder is empty, please check')
        self.stop = True
        return

    # Check if item is already on the processing list
    count = 0
    while True:
        twi0 = self.ui.tableWidget.item(count, 1)
        if not twi0:
            self.stop = None
            break
        if twi0.text() == outputFolder:
            QtGui.QMessageBox.warning(self, 'Message', 'Warning: Output folder is already on the processing list')
            self.stop = True
            return
        count = count+1

    # Check if a crop folder is available if UseOldCrop is used
    if self.ui.radioButtonUseOldCrop.isChecked() and self.ui.checkBoxCropYes.isChecked():
        if not os.path.exists(os.path.join(str(self.ui.lineEditOutput.text()),"cropped")):
            self.stop = True
            QtGui.QMessageBox.warning(self,'Message','Warning: Use old crop option selected. '
                                                               'This requires a previous crop to have been performed')
            return

    if self.ui.radioButtonuCT.isChecked() and self.ui.radioButtonDerived.isChecked():
            self.stop = True
            QtGui.QMessageBox.warning(self,'Message','Warning: Derived Dimension crop option is not available for'
                                                     ' uCT processing')
            return

    # seeing if output folder exists
    if self.ui.checkBoxRF.isChecked():
        # I think it is too dangerous to delete everything in a folder
        # shutil.rmtree(outputFolder)
        # os.makedirs(outputFolder)
        self.stop = None
    # Check if output folder already exists. Ask if it is ok to overwrite
    elif os.path.exists(outputFolder):
        # Running dialog box to inform user of options
        message = QtGui.QMessageBox.question(self, 'Message',
                                             'Folder already exists for the location:\n{0}\n'
                                             'Is it OK to overwrite files in this folder?'
                                             'NOTE: If you are using the "old crop" option you will not overwrite the '
                                             'original cropped recon'.format(outputFolder),
                                             QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        if message == QtGui.QMessageBox.Yes:
            self.stop = None
        if message == QtGui.QMessageBox.No:
            self.stop = True
            return
    else:
        os.makedirs(outputFolder)
        self.stop = None






