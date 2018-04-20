import logging
import os
import sys
from argparse import ArgumentParser
from subprocess import call

import numpy as np
from cytomine import CytomineJob
from cytomine.models import Annotation, AnnotationTerm, Job, ImageInstanceCollection, Property
from shapely.ops import cascaded_union
from shapely.affinity import affine_transform
from skimage import io
from sldc import locator

def add_annotation(img_inst, polygon, label=None, proba=1.0):
    image_id = img_inst.id
    # Transform in cartesian coordinates
    polygon = affine_transform(polygon, [1, 0, 0, -1, 0, img_inst.height])

    annotation = Annotation(polygon.wkt, image_id).save()
    if label is not None and annotation is not None:
        annotation_term = AnnotationTerm()
        annotation_term.annotation = annotation.id
        annotation_term.annotationIdent = annotation.id
        annotation_term.userannotation = annotation.id
        annotation_term.term = label
        annotation_term.expectedTerm = label
        annotation_term.rate = proba
        annotation_term.save()
    return annotation

def makedirs(path):
    if not os.path.exists(path):
        os.makedirs(path)


parser = ArgumentParser(prog="Icy-SpotDetection.py", description="Icy workflow to detect spots in 2D images")
parser.add_argument('--cytomine_host', dest="cytomine_host", default='http://localhost-core')
parser.add_argument('--cytomine_public_key', dest="cytomine_public_key", default="")
parser.add_argument('--cytomine_private_key', dest="cytomine_private_key", default="")
parser.add_argument("--cytomine_id_project", dest="cytomine_id_project", default="5378")
parser.add_argument("--cytomine_id_software", dest="cytomine_id_software", default="")
parser.add_argument("--icy_scale3sensitivity", dest="scale3sens", default="40")
params, others = parser.parse_known_args(sys.argv)

gt_suffix = "_lbl"
base_path = "/icy/data"

with CytomineJob(params.cytomine_host, params.cytomine_public_key, params.cytomine_private_key, params.cytomine_id_software, params.cytomine_id_project, verbose=logging.INFO) as cj:
    cj.job.update(status=Job.RUNNING, progress=0, statusComment="Initialisation...")

    working_path = os.path.join(base_path, str(cj.job.id))
    in_path = os.path.join(working_path, "in")
    makedirs(in_path)
    out_path = os.path.join(working_path, "out")
    makedirs(out_path)
    gt_path = os.path.join(working_path, "ground_truth")
    makedirs(gt_path)

    cj.job.update(progress=1, statusComment="Downloading images...")
    image_instances = ImageInstanceCollection().fetch_with_filter("project", params.cytomine_id_project)
    input_images = [i for i in image_instances if gt_suffix not in i.originalFilename]
    gt_images = [i for i in image_instances if gt_suffix in i.originalFilename]

    for input_image in input_images:
        input_image.download(os.path.join(in_path, "{id}.tif"))

    for gt_image in gt_images:
        related_name = gt_image.originalFilename.replace(gt_suffix, '')
        related_image = [i for i in input_images if related_name == i.originalFilename]
        if len(related_image) == 1:
            gt_image.download(os.path.join(gt_path, "{}.tif".format(related_image[0].id)))

    cj.job.update(progress=25, statusComment="Launching workflow...")

    command = "/icy/run.sh {} {}".format(in_path, params.scale3sens)
    call(command, shell=True)

    cj.job.update(progress=60, statusComment="Extracting polygons...")

    for image in images:
    file = str(image.id) + "_results.txt"
    path = inDir + "/" + file
    if(os.path.isfile(path)):
        (X,Y) = readcoords(path)
        for i in range(len(X)):
            circle = Point(X[i],image.height-Y[i])
            annotation.location=circle.wkt
            new_annotation = conn.add_annotation(annotation.location, image.id)
    else:
        print(path + " does not exist")

    cj.job.update(progress=99, statusComment="Cleaning...")
    for image in images:
    	file = str(image.id) + ".tif"
    	#path = outDir + "/" + file
    	#os.remove(path);
    	path = inDir + "/" + file
    	os.remove(path);
    	path = inDir + "/" + str(image.id) + "_results.txt"
    	os.remove(path)

    cj.job.update(status=Job.TERMINATED, progress=100, statusComment="Finished.")
