import sys
import os
from cytomine import Cytomine
from cytomine.models import *
from subprocess import call
from skimage import io
import numpy as np
from sldc import locator
from shapely.geometry import Point
from array import *
from argparse import ArgumentParser

def readcoords(fname):
	X = []
	Y = []
	F = open(fname,'r')
	i = 1
	for l in F.readlines():
		t = l.split(',')
		X.append(float(t[1]))
		Y.append(float(t[2]))
		i=i+1
	F.close()
	return X,Y

baseOutputFolder = "/dockershare/";

parser = ArgumentParser(prog="Icy-SpotDetection.py", description="Icy workflow to detect spots in 2D images")
parser.add_argument('--cytomine_host', dest="cytomine_host", default='http://localhost-core')
parser.add_argument('--cytomine_public_key', dest="cytomine_public_key", default="77af7d84-b737-4489-8864-d5ad93f4700b")
parser.add_argument('--cytomine_private_key', dest="cytomine_private_key", default="3ef1f34e-2a9e-4ff8-96ec-df8e57c7dfcd")
parser.add_argument("--cytomine_id_project", dest="cytomine_id_project", default="5378")
parser.add_argument("--icy_scale3sensitivity", dest="scale3sens", default="40")

arguments, others = parser.parse_known_args(sys.argv)
scale3sens = arguments.scale3sens


#Cytomine connection parameters
cytomine_host=arguments.cytomine_host

id_project=arguments.cytomine_id_project

conn = Cytomine(arguments.cytomine_host, arguments.cytomine_public_key, arguments.cytomine_private_key, base_path = '/api/', working_path = '/tmp/', verbose= True)

current_user = conn.get_current_user()
user_job = current_user

job = conn.get_job(user_job.job)

job = conn.update_job_status(job, status = job.RUNNING, progress = 0, status_comment = "Loading images...")

# Get the list of images in the project
image_instances = ImageInstanceCollection()
image_instances.project  =  id_project
image_instances  =  conn.fetch(image_instances)
images = image_instances.data()

# create the folder structure for the folders shared with docker 
jobFolder = baseOutputFolder + str(job.id) + "/"
inDir = jobFolder + "in"
outDir = jobFolder + "out"

if not os.path.exists(inDir):
    os.makedirs(inDir)

if not os.path.exists(outDir):
    os.makedirs(outDir)

# download the images
for image in images:
	# url format: CYTOMINEURL/api/imageinstance/$idOfMyImageInstance/download
	url = cytomine_host+"/api/imageinstance/" + str(image.id) + "/download"
	filename = str(image.id) + ".tif"
	conn.fetch_url_into_file(url, inDir+"/"+filename, True, True) 

# call the image analysis workflow in the docker image
shArgs = "data/in "+scale3sens
job = conn.update_job_status(job, status = job.RUNNING, progress = 25, status_comment = "Launching workflow...")
command = "docker run --rm -v "+jobFolder+":/icy/data neubiaswg5/spotdetection-icy " + shArgs
call(command,shell=True)	# waits for the subprocess to return

# remove existing annotations if any
for image in images:
	annotations = conn.get_annotations(id_image=image.id)
        for annotation in annotations:
            conn.delete_annotation(annotation.id)

files = os.listdir(outDir)


job = conn.update_job_status(job, status = job.RUNNING, progress = 50, status_comment = "Extracting polygons...")

for image in images:
	file = str(image.id) + ".tif.csv"
	path = outDir + "/" + file
	if(os.path.isfile(path)):
		imageData = io.imread(path)
		(X,Y) = readcoords(fname)
	  	for i in range(len(terms)):
			circle = Point(X[i],image.height-Y[i])
			annotation.location=circle.wkt
			new_annotation = conn.add_annotation(annotation.location, image.id)
			conn.add_user_annotation_term(new_annotation.id, term=terms[i])
	else:
		print path + " does not exist"

# cleanup - remove the downloaded images and the images created by the workflow
job = conn.update_job_status(job, status = job.TERMINATED, progress = 90, status_comment =  "Cleaning up..")

for image in images:
	file = str(image.id) + ".tif"
	path = outDir + "/" + file
	os.remove(path);
	path = inDir + "/" + file
	os.remove(path);
        path = inDir + "/" + file + ".csv"
        os.remove(path)

job = conn.update_job_status(job, status = job.TERMINATED, progress = 100, status_comment =  "Finished Job..")
