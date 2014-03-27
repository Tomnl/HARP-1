# For some reason need to re-import PyQt4...... Not the best solution but seems to work
from PyQt4 import QtGui, QtCore
import sys
import subprocess
import os, signal
import re
import pickle
import pprint
import time
import shutil
import uuid
import logging
from sys import platform as _platform

from Progress import Ui_Progress


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

        self.ui.pushButtonCancel_1.clicked.connect(self.cancel)
        self.ui.pushButtonAddMore.clicked.connect(self.addMore)

    def cancel(self):
        self.close()

    def addMore(self):
        dir = os.path.dirname(os.path.abspath(__file__))
        runPro_p = subprocess.Popen(["python", dir+"/Main.py"],stdout=subprocess.PIPE, stderr=subprocess.PIPE)


    def add(self,test):
        self.ui.label1_tracking.setText(test)

        if test == "Processing finished" :
            self.ui.progressBar_1.setValue(100)

        if test == "Crop finished" :
            self.ui.progressBar_1.setValue(50)

        if test == "Error" :
            self.threadPool[len(self.threadPool)-1].terminate()

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

    def closeEvent(self, event):
        """ Function doc """
        reply = QtGui.QMessageBox.question(self,  'Message',  'Are you sure to quit?',  QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            event.accept()
            self.threadPool[len(self.threadPool)-1].terminate()

            self.pid_log_path = os.path.join(self.configOb.meta_path,"pid.log")
            ins = open( self.pid_log_path, "r" )
            for line in ins:

                try :
                    if _platform == "linux" or _platform == "linux2":
                        os.kill(int(line),signal.SIGKILL)
                        print "killed:", int(line)
                    elif _platform == "win32" or _platform == "win64":
                        os.system('taskkill /f /t /im '+str(line))
                except OSError as e:
                    print("os.kill could not kill process, reason: {0}".format(e))


        else:
            event.ignore()


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

        # Get the session log files
        self.session_log_path = os.path.join(self.configOb.meta_path,"session.log")
        self.pid_log_path = os.path.join(self.configOb.meta_path,"pid.log")
        self.crop_log_path = os.path.join(self.configOb.meta_path,"crop.log")
        self.scale_log_path = os.path.join(self.configOb.meta_path,"scale.log")

        # Save as object to print to
        if os.path.exists(self.session_log_path):
            os.remove(self.session_log_path)

        logging.basicConfig(filename=self.session_log_path,level=logging.DEBUG,format='%(asctime)s %(message)s')

        #session = open(self.session_log_path, 'w+')
        session_pid = open(self.pid_log_path, 'w+')
        session_crop = open(self.crop_log_path, 'w+')
        session_scale = open(self.scale_log_path, 'w+')

        # Special log path to be used

        logging.info("Name of recon:"+self.configOb.full_name)
        logging.info("ImageJ:"+self.configOb.imageJ)


        ###############################################
        # Copy temp files (pre-processing log and zprojection image)
        ###############################################
        if self.configOb.crop_option == "Manual" :
            print os.path.join(self.configOb.tmp_dir,"max_intensity_z.tif")
            shutil.copyfile(os.path.join(self.configOb.tmp_dir,"max_intensity_z.tif"), os.path.join(self.configOb.meta_path,"max_intensity_z.tif"))


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
            logging.info("Performing manual crop")
            self.emit( QtCore.SIGNAL('update(QString)'), "Performing manual crop" )
            manpro = subprocess.Popen(["python", crop_run,"-i",self.configOb.input_folder,"-o",
                         cropped_path, "-t", "tif","-d",self.configOb.xcrop, self.configOb.ycrop, self.configOb.wcrop, self.configOb.hcrop],
                            stdout=session_crop, stderr=session_crop)
            session_pid.write(str(manpro.pid)+"\n")
            session_pid.close()
            manpro.communicate()
            self.emit( QtCore.SIGNAL('update(QString)'), "Crop finished" )
            logging.info("Crop finished")

        # Perform the automatic crop if required
        if self.configOb.crop_option == "Automatic" :
            logging.info("Performing autocrop")
            self.emit( QtCore.SIGNAL('update(QString)'), "Performing autocrop" )

            aupro = subprocess.Popen(["python", crop_run,"-i",self.configOb.input_folder,"-o", cropped_path, "-t", "tif"],
                            stdout=session_crop,stderr=session_crop)
            session_pid.write(str(aupro.pid)+"\n")
            session_pid.close()
            aupro.communicate()
            self.emit( QtCore.SIGNAL('update(QString)'), "Crop finished" )
            logging.info("Crop finished")

        # Do not perform any crop as user specified
        if self.configOb.crop_option == "None" :
            self.emit( QtCore.SIGNAL('update(QString)'), "No Crop carried out" )
            print "No crop carried out"
            logging.info("No crop carried out")
            session_pid.close()

        ###############################################
        # Copying of other files from recon directory
        ###############################################
        logging.info("Copying other files from recon")
        for file in os.listdir(self.configOb.input_folder):
            suffix_txt, suffix_spr, suffix_log, suffix_crv = ".txt","spr",".log",".crv"
            if file.endswith((".txt",".log",".crv")) or re.search('spr', file, re.IGNORECASE):
                logging.info("File copied:"+file)
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

        logging.info("imageJ:")
        logging.info(self.configOb.imageJ)
        # Perform scaling as subprocess with Popen (they should be done in the background)
        if self.configOb.SF2 == "yes" :
            logging.info("Performing scaling by factor 2")
            proSF2 = self.executeImagej("^0.5^x2",session_pid,session_scale)
            out2, err2 = proSF2.communicate()
            logging.info("Finished scaling by factor 2")

        if self.configOb.SF3 == "yes" :
            logging.info("Performing scaling by factor 3")
            proSF3 = self.executeImagej("^0.3333^x3",session_pid,session_scale)
            out3, err3 = proSF3.communicate()
            logging.info("Finished scaling by factor 3")

        if self.configOb.SF4 == "yes" :
            logging.info("Performing scaling by factor 4")
            proSF4 = self.executeImagej("^0.25^x4",session_pid,session_scale)
            out4, err4 = proSF4.communicate()
            logging.info("Performing scaling by factor 4")

        session_scale.close()
        self.emit( QtCore.SIGNAL('update(QString)'), "Processing finished" )
        logging.info("Processing finished")
        logging.shutdown()
        session_pid.close()
        session_crop.close()
        session_scale.close()


    def executeImagej(self, scaleFactor,session_pid,session_scale):
        '''
        @param: str, scaleFactor eg ":0.5"
        '''
        # for saving pid again
        session_pid = open(self.pid_log_path, 'a+')

        if _platform == "linux" or _platform == "linux2":
            self.emit( QtCore.SIGNAL('update(QString)'), "Performing scaling ({})".format(scaleFactor) )
            process = subprocess.Popen(["java", "-jar", "/usr/share/java/ij.jar", "-batch", os.path.join(self.dir, "siah_scale.txt"),
                                    self.configOb.imageJ + scaleFactor],stdout=session_scale,stderr=session_scale)
            session_pid.write(str(process.pid)+"\n")
            session_pid.close()
            return process

        elif _platform == "win32" or _platform == "win64":
            ijpath = os.path.join('c:', os.sep, 'Program Files', 'ImageJ', 'ij.jar')

            self.emit( QtCore.SIGNAL('update(QString)'), "Performing scaling ({})".format(scaleFactor) )
            process = subprocess.Popen(["java", "-jar", ijpath, "-batch", os.path.join(self.dir, "siah_scale.txt"),
                                    self.configOb.imageJ + scaleFactor],stdout=session_scale,stderr=session_scale)
            session_pid.write(str(process.pid)+"\n")
            session_pid.close()
            return process







def main():
    app = QtGui.QApplication(sys.argv)
    ex = Progress(configOb)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
