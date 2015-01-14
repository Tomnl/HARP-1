"""Creates a YAMl file in app directory that stores details such as last directory browsed

"""
from lib import appdirs
import os
import yaml
from os.path import expanduser
import os
import collections

default_ignore = ['spr.bmp', 'spr.tif', 'spr.tiff', 'spr.jpg', 'spr.jpeg', '.txt', '.text', '.log', '.crv']
default_use = ['*rec*.bmp', '*rec*.BMP', '*rec*.tif', '*rec*.tiff', '*rec*.jpg', '*rec*.jpeg']


class AppData(object):
    def __init__(self):
        self.using_appdata = True  # Set to false if we weren't able to find a directory to save the appdata
        appname = 'harp'
        appdata_dir = appdirs.user_data_dir(appname)
        self.app_data = {}

        if not os.path.isdir(appdata_dir):
            try:
                os.mkdir(appdata_dir)
            except WindowsError:
                #Can't find the AppData directory. So just make one in home directory
                appdata_dir = os.path.join(expanduser("~"), '.' + appname)
                if not os.path.isdir(appdata_dir):
                    try:
                        os.mkdir(appdata_dir)
                    except:
                        self.using_appdata = False
            except OSError:
                self.using_appdata = False

        if self.using_appdata:
            self.app_data_file = os.path.join(appdata_dir, 'app_data.yaml')

            if os.path.isfile(self.app_data_file):
                with open(self.app_data_file, 'r') as fh:
                    self.app_data = yaml.load(fh)

    def save(self):
        if self.using_appdata:
            with open(self.app_data_file, 'w') as fh:
                fh.write(yaml.dump(self.app_data))

    @property
    def last_dir_browsed(self):
        if self.using_appdata:
            if self.app_data:
                if not self.app_data.get('last_dir_browsed'):
                    self.app_data['last_dir_browsed'] = expanduser("~")
                return self.app_data['last_dir_browsed']

    @last_dir_browsed.setter
    def last_dir_browsed(self, path):
        if not self.app_data:
            self.app_data = {}
        if self.using_appdata:
            self.app_data['last_dir_browsed'] = path

    @property
    def files_to_ignore(self):
        if self.using_appdata:
            if self.app_data:
                if not self.app_data.get('files_to_ignore'):
                    self.app_data['files_to_ignore'] = default_ignore
                return self.app_data['files_to_ignore']

    @files_to_ignore.setter
    def files_to_ignore(self, pattern_list):
        if self.using_appdata:
            self.app_data['files_to_ignore'] = pattern_list

    @property
    def files_to_use(self):
        if self.using_appdata:
            if self.app_data:
                if not self.app_data.get('files_to_use'):
                    self.app_data['files_to_use'] = default_use
                return self.app_data['files_to_use']

    @files_to_use.setter
    def files_to_use(self, pattern_list):
        if self.using_appdata:
            self.app_data['files_to_use'] = pattern_list

    def reset_ignore_file(self):
        self.app_data['files_to_ignore'] = default_ignore

    def reset_use_file(self):
        self.app_data['files_to_use'] = default_use

