import sys
import os
from cytomine import CytomineJob
from cytomine.models import *
from subprocess import call
from shapely.geometry import Point


def readcoords(fname):
    X = []
    Y = []
    F = open(fname, 'r')
    i = 1
    for index, l in enumerate(F.readlines()):
        if index < 2: continue
        t = l.split('\t')
        print()
        if len(t) > 1:
            X.append(float(t[5]))
            Y.append(float(t[6]))
        i = i + 1
    F.close()
    return X, Y


def main():
    base_output_folder = "/dockershare/"

    with CytomineJob.from_cli(sys.argv[1:]) as cj:
        scale3sens = cj.parameters.icy_scale3sensitivity

        cj.job.update(progress=1, statusComment="Loading images from Cytomine...")

        # create the folder structure for the folders shared with docker
        job_folder = os.path.join(base_output_folder, str(cj.job.id))
        in_dir = os.path.join(job_folder, "in")
        out_dir = os.path.join(job_folder, "out")

        if not os.path.exists(in_dir):
            os.makedirs(in_dir)

        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        # Get the list of images in the project
        cj.job.update(progress=1, statusComment="Downloading images (to {})...".format(in_dir))
        image_instances = ImageInstanceCollection().fetch_with_filter("project", cj.project.id)

        for image in cj.monitor(image_instances, start=1, end=25, period=0.1, prefix="Download input images"):
            image.download(os.path.join(in_dir, "{id}.tif"))

        # call the image analysis workflow in the docker image
        cj.job.update(progress=25, statusComment="Launching workflow...")
        call("sh run.sh data/in {}".format(scale3sens), shell=True)  # waits for the subprocess to return

        # # remove existing annotations if any
        # for image in cj.monitor(image_instances, start=60, end=75, period=0.1, prefix="Delete previous annotations"):
        #     annotations = AnnotationCollection.fetch_with_filter({"image": image.id})
        #     for annotation in annotations:
        #         conn.delete_annotation(annotation.id)
        cj.job.update(progress=75, status_comment="Extracting polygons...")

        for image in cj.monitor(image_instances, start=75, end=95, period=0.1, prefix="Upload annotations"):
            file = str(image.id) + "_results.txt"
            path = os.path.join(in_dir, file)
            if os.path.isfile(path):
                (X, Y) = readcoords(path)
                for i in range(len(X)):
                    center = Point(X[i], image.height - Y[i])
                    annotation.location = center.wkt
                    Annotation(location=center.wkt, id_image=image.id).save()
            else:
                print("No output file at '{}' for image with id:{}.".format(path, image.id), file=sys.stderr)

        # should launch the metrics computation here
        # TODO

        # cleanup - remove the downloaded images and the images created by the workflow
        cj.job.update(progress=99, prefix="Cleaning up...")
        os.remove(job_folder)

        cj.job.update(progress=100, status=Job.TERMINATED, status_comment="Finished Job..")


if __name__ == "__main__":
    main()