import logging
import os
import sys
from argparse import ArgumentParser
from subprocess import call

import numpy as np
from cytomine import CytomineJob
from cytomine.models import Annotation, AnnotationTerm, Job, ImageInstanceCollection, Property, AnnotationCollection
from shapely.ops import cascaded_union
from shapely.affinity import affine_transform
from shapely.geometry import Point
from skimage import io
from sldc import locator


def readcoords(fname):
    X = []
    Y = []
    F = open(fname,'r')
    i = 1
    for index,l in enumerate(F.readlines()):
        if index<2: continue
        t = l.split('\t')
        print(t)
        if len(t)>1:
            X.append(float(t[5]))
            Y.append(float(t[6]))
        i=i+1
    F.close()
    return X,Y

def makedirs(path):
    if not os.path.exists(path):
        os.makedirs(path)

home_dir = os.getenv("HOME")
base_path = "{}/icy/data".format(home_dir)

parser = ArgumentParser(prog="Icy-SpotDetection.py", description="Icy workflow to detect spots in 2D images")
parser.add_argument('--cytomine_host', dest="cytomine_host", default='http://localhost-core')
parser.add_argument('--cytomine_public_key', dest="cytomine_public_key", default="")
parser.add_argument('--cytomine_private_key', dest="cytomine_private_key", default="")
parser.add_argument("--cytomine_id_project", dest="cytomine_id_project", default="5378")
parser.add_argument("--cytomine_id_software", dest="cytomine_id_software", default="")
parser.add_argument("--icy_scale3sensitivity", dest="scale3sens", default="40")
params, others = parser.parse_known_args(sys.argv)

with CytomineJob(params.cytomine_host, params.cytomine_public_key, params.cytomine_private_key,
                 params.cytomine_id_software, params.cytomine_id_project, verbose=logging.INFO) as cj:
    cj.job.update(status=Job.RUNNING, progress=0, statusComment="Initialisation...")

    working_path = os.path.join(base_path, str(cj.job.id))
    in_path = os.path.join(working_path, "in")
    makedirs(in_path)
    out_path = os.path.join(working_path, "out")
    makedirs(out_path)

    cj.job.update(progress=1, statusComment="Downloading images...")
    images = ImageInstanceCollection().fetch_with_filter("project", params.cytomine_id_project)

    for image in images:
        image.download(os.path.join(in_path, "{id}.tif"))

    for image in images:
        annotations = AnnotationCollection()
        annotations.image = image.id
        annotations.fetch()
        for annotation in annotations:
            annotation.delete()       

    cj.job.update(progress=25, statusComment="Launching workflow...")

    command = "/icy/run.sh {} {}".format(in_path, params.scale3sens)
    call(command, shell=True)

    cj.job.update(progress=60, statusComment="Extracting polygons...")

    for image in images:
        file = str(image.id) + "_results.txt"
        path = in_path + "/" + file
        if(os.path.isfile(path)):
            (X,Y) = readcoords(path)
            for i in range(len(X)):
                circle = Point(X[i],image.height-Y[i])
                new_annotation = Annotation(location=circle.wkt, id_image=image.id).save()
        else:
            print(path + " does not exist")

    cj.job.update(progress=99, statusComment="Cleaning...")
    for image in images:
    	file = str(image.id) + ".tif"
    	#path = outDir + "/" + file
    	#os.remove(path);
    	path = in_path + "/" + file
    	os.remove(path);
    	path = in_path + "/" + str(image.id) + "_results.txt"
    	os.remove(path)

    cj.job.update(status=Job.TERMINATED, progress=100, statusComment="Finished.")
