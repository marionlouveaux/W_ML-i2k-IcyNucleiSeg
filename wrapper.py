import sys
import os
from cytomine import CytomineJob
from cytomine.models import *
from subprocess import call
from shapely.geometry import Point


def makedirs(path):
    if not os.path.exists(path):
        os.makedirs(path)


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
    base_path = "{}".format(os.getenv("HOME")) # Mandatory for Singularity

    with CytomineJob.from_cli(sys.argv[1:]) as cj:
        scale3sens = cj.parameters.icy_scale3sensitivity

        working_path = os.path.join(base_path, "data", str(cj.job.id))
        in_dir = os.path.join(working_path, "in")
        makedirs(in_dir)
        out_dir = os.path.join(working_path, "out")
        makedirs(out_dir)

        cj.job.update(progress=1, statusComment="Downloading images (to {})...".format(in_dir))
        image_instances = ImageInstanceCollection().fetch_with_filter("project", cj.project.id)

        for image in image_instances:
            image.download(os.path.join(in_dir, "{id}.tif"))

        cj.job.update(progress=25, statusComment="Launching workflow...")
        call("java -cp /icy/lib/ -jar /icy/icy.jar -hl", shell=True)
        call("cd /icy && java -cp /icy/lib/ -jar /icy/icy.jar -hl -x plugins.adufour.protocols.Protocols "
             "protocol=\"/icy/protocols/protocol.protocol\" inputFolder=\"{}\" extension=tif csvFileSuffix=_results "
             "scale3enable=true scale3sensitivity={}".format(in_dir, scale3sens), shell=True)

        # # remove existing annotations if any
        # for image in cj.monitor(image_instances, start=60, end=75, period=0.1, prefix="Delete previous annotations"):
        #     annotations = AnnotationCollection.fetch_with_filter({"image": image.id})
        #     for annotation in annotations:
        #         annotation.delete()

        cj.job.update(progress=75, status_comment="Extracting polygons...")
        annotations = AnnotationCollection()
        for image in cj.monitor(image_instances, start=75, end=95, period=0.1, prefix="Upload annotations"):
            file = str(image.id) + "_results.txt"
            path = os.path.join(in_dir, file)
            if os.path.isfile(path):
                (X, Y) = readcoords(path)
                for i in range(len(X)):
                    center = Point(X[i], image.height - Y[i])
                    annotations.append(Annotation(location=center.wkt, id_image=image.id,
                                                  id_project=cj.parameters.cytomine_id_project))

                    if len(annotations) % 100 == 0:
                        annotations.save()
                        annotations = AnnotationCollection()
            else:
                print("No output file at '{}' for image with id:{}.".format(path, image.id), file=sys.stderr)
        # Save last annotations
        annotations.save()

        # Launch the metrics computation here
        # TODO

        cj.job.update(progress=100, status=Job.TERMINATED, status_comment="Finished.")


if __name__ == "__main__":
    main()
