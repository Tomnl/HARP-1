//siah_scale
//An ImageJ macro to scale a folder of bmps and save as tiff stack
//Run it like this:
//java -jar /usr/share/java/ij.jar -batch /home/neil/.imagej/macros/siah_scale.txt '/home/neil/test_stack/:/home/neil/test_stack/test_stack:0.5,0.25,0.14'
//or
//Fiji --headless -batch /home/neil/harwell-ct-pipleine/siah_scale.txt '/home/neil/test_stack/:/home/neil/test_stack/test_stack:0.5'

//Might have to specify path to macro
//args are in one string seperated by :
//Arg[0] = dir with tifs
//Arg[1] = out directory
//Arg[1....] = scale factors seperated by commas


//TODO: Can't select the window by title of the supposedly newly created window from the (Scale.. ) commannd
print("###############################");
print("siah_scale macro started");
print("###############################");


args = getArgument;
if (args=="") exit ("No argument!");

arg_array = split(args,":");
print("input folder:");
print(arg_array[0]);

image_list = getFileList(arg_array[0]);
//Not sure what this is for
run("Close All");

setBatchMode(true);

out_path = arg_array[1];
scale = arg_array[2];

print("output folder:");
print(out_path);
print("scale factor:");
print(scale);

//open the image sequence as a stack
run("Image Sequence...", "open=[" + arg_array[0] + image_list[0] + "] file=[] or=[] sort use");
rename("unscaled");
//run('Nrrd ... ', "nrrd=" + "/home/neil/test/test.nrrd");


//Set number of images in stack
zdepth = floor(image_list.length * scale);



//run the scaling

scale_string = replace(scale, '.', '-');
run("Scale...", "x=" + scale + " y=" + scale +  " z="+scale + " depth=" + zdepth + " average process create title=scaled");
selectWindow("scaled");


//Create directory
File.makeDirectory(out_path + scale_string);
saveAs("Tiff", out_path + scale_string + "/"+ scale_string + ".tif");
//run('Nrrd ... ', "nrrd=" + out_path + scale_string + "/"+ scale_string + ".nrrd");



