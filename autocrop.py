#!/usr/bin/python

try:
    import Image
except ImportError:
    from PIL import Image

import argparse
import os
import fnmatch
import numpy as np
from multiprocessing import Pool
import sys
import time
import math
from collections import Counter


imdims = None

class Processor:
    '''Processes each image file individually
    Implements __call__() so it can be used in multithreading by '''

    def __init__(self, threshold):
        self.threshold = threshold

    def __call__(self, filename):
        '''
        @param: filename path of an image to process
        @returns: tuple of bounding box coords

        Reads image into array. Flips it around each time
        with column/row of interest as the top top row
        '''
        im = Image.open(filename)
        matrix = np.array(im)
        crops = {}
        crops["x"] = np.std(matrix, axis=0)
        crops["y"] = np.std(matrix, axis=1)

        return(crops)


class Cropper:
    def __init__(self, crop_box, out_dir):
        self.crop_box = crop_box
        self.out_dir = out_dir

    def __call__(self, img):
        im = Image.open(img)
        im = im.crop((self.crop_box[0], self.crop_box[1], self.crop_box[2], self.crop_box[3] ))
        filename = os.path.basename(img)
        crop_out = os.path.join(self.out_dir,filename)
        im.save(crop_out)


def do_the_crop(images, crop_vals, out_dir,  padding=0):
    '''
    @param: images list of image files
    @param: crop_vals tuple of the crop box (x, y, w, h)
    @param: out_dir str dir to output cropped images

    '''
    print("doing the crop")
    global imdims
    print imdims

    lcrop = crop_vals[0] - padding
    if lcrop < 0: lcrop = 0

    tcrop = crop_vals[1] - padding
    if tcrop < 0: tcrop = 0

    #Get distance from left side
    #rcrop = imdims[0] - crop_vals[2] + padding
    rcrop = crop_vals[2] + padding
    if rcrop > imdims[0] -1: rcrop = imdims[0] -1

    #get distance from top
    #bcrop = imdims[1] - crop_vals[3] + padding
    bcrop = crop_vals[3] + padding
    if bcrop > imdims[1] -1: bcrop = imdims[1] -1

    print("cropping with the following box: left:{0}, top:{1}, right:{2}, bottom{3}".format(
        lcrop, tcrop, rcrop, bcrop))
    print("ImageJ friendly box: makeRectangle({0},{1},{2},{3})".format(
        lcrop, tcrop, rcrop -lcrop, bcrop - tcrop))

    cropper = Cropper((lcrop, tcrop, rcrop, bcrop), out_dir)
    pool = Pool()
    pool.map(cropper, images)
    return


def get_cropping_box(slices, side, threshold, rev = False):

    #Vals = array of arrays with each sub-array containing the
    # the metric calculated in Process for each row/column
    #vals = [x[side] for x in slices]
    vals = [lowvals(x[side]) for x in slices]

    #filterout low values
    means = map(np.std, zip(*vals))

    if rev == True:
        return next((i for i, v in enumerate(reversed(means)) if v > threshold ), -1)
    else:
        return next((i for i, v in enumerate(means) if v > threshold ), -1)



def entropy(array):
    '''
    not currently used
    '''
    p, lns = Counter(round_down(array, 4)), float(len(array))
    return -sum( count/lns * math.log(count/lns, 2) for count in p.values())


def round_down(array, divisor):
    for n in array:
        yield n - (n%divisor)


def lowvals(array):
    low_values_indices = array < 10  # Where values are low
    array[low_values_indices] = 0
    return array




def run(args):
    #Get the file list exclude ones we dont want
    #Note fnmatch is case insensitive by default so with fnd BMP and bmp
    files = []


    for fn in os.listdir(args.in_dir):
        if fnmatch.fnmatch(fn, '*spr.bmp'):
            continue
        if fnmatch.fnmatch(fn, '*.bmp') or fnmatch.fnmatch(fn, '*.BMP'):
            files.append(os.path.join(args.in_dir, fn))
    if len(files) < 1:
        sys.exit("no image files found in" + args.in_dir)

    #get image dimensions from first file
    img = Image.open(files[0])
    global imdims
    imdims = img.size
    #map(open_files, files)
    #sys.exit()

    if args.def_crop:
        do_the_crop(files, args.def_crop, args.out_dir)
        sys.exit()
    else: #Do the autocrop
        print("No region specified. Trying autocrop")
        threshold = 0.01
        proc = Processor(threshold)
        pool = Pool(8)
        #Just use a subset of files to determine crop
        sparse_files = files [0::10]
        slices = pool.map(proc, sparse_files)
        #end = time.time()
        #curr_time = end - start
        #print("Files read and means calculated. Time to here: {0}".format(curr_time) )
        #print slices
        #sys.exit()

        #Distances of cropping boxes from their respective sides
        ldist = get_cropping_box(slices, "x", threshold)
        tdist = get_cropping_box(slices, "y", threshold)
        rdist = get_cropping_box(slices, "x", threshold, True)
        bdist = get_cropping_box(slices, "y", threshold, True)
        cropBox = convertDistFromEdgesToXYWH((ldist, tdist, rdist, bdist))

        padding = int(np.mean(imdims)*0.01)
        do_the_crop(files, cropBox, args.out_dir, padding)
        sys.exit()


def convertDistFromEdgesToXYWH(distances):
    global imdims
    width = imdims[0] - distances[2]
    height = imdims[1] - distances[3]
    return((distances[0], distances[1], width, height))


def main():
    '''
    Parse the arguments
    '''
    global start
    start = time.time()

    parser = argparse.ArgumentParser(description='crop a stack of bitmaps')
    parser.add_argument('-i', dest='in_dir', help='dir with bmps to crop', required=True)
    parser.add_argument('-o', dest='out_dir', help='destination for cropped images', required=True)
    parser.add_argument('-t', dest='file_type', help='tif or bmp', default="bmp")
    parser.add_argument('-d', nargs=4, type=int, dest='def_crop', help='set defined boundaries for crop')
    parser.add_argument('-p', dest='p', help='set defined boundaries for crop')
    args = parser.parse_args()
    run(args)
    #sys.exit()


if __name__ == '__main__':
    main()
