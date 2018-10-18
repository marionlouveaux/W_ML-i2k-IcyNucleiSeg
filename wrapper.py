import os
import sys
import cv2
import numpy as np
import tifffile
from cytomine import CytomineJob
from cytomine.models import *
from subprocess import call

from shapely.affinity import affine_transform
from shapely.geometry import Point
from annotation_exporter import csv_to_points, slices_to_mask, AnnotationSlice

from neubiaswg5.metrics import computemetrics_batch


def makedirs(path):
    if not os.path.exists(path):
        os.makedirs(path)


def clean_icy_result_file(filepath, n=1):
    lines = None
    with open(filepath, "r") as file:
        lines = file.readlines()
    with open(filepath, "w") as file:
        file.writelines([l for l in lines[n:] if len(l.strip()) > 0])


def main():
    with CytomineJob.from_cli(sys.argv[1:]) as cj:
        scale3sens = cj.parameters.icy_scale3sensitivity

        cj.job.update(status=Job.RUNNING, progress=0, statusComment="Initialisation...")

        # 1. Create working directories on the machine:
        # - WORKING_PATH/in: input images
        # - WORKING_PATH/out: output images
        # - WORKING_PATH/ground_truth: ground truth images
        # - WORKING_PATH/tmp: temporary path
        base_path = "{}".format(os.getenv("HOME"))
        gt_suffix = "_lbl"
        working_path = os.path.join(base_path, str(cj.job.id))
        in_path = os.path.join(working_path, "in")
        out_path = os.path.join(working_path, "out")
        gt_path = os.path.join(working_path, "ground_truth")
        tmp_path = os.path.join(working_path, "tmp")

        if not os.path.exists(working_path):
            os.makedirs(working_path)
            os.makedirs(in_path)
            os.makedirs(out_path)
            os.makedirs(gt_path)
            os.makedirs(tmp_path)

        # 2. Download the images (first input, then ground truth image)
        cj.job.update(progress=1, statusComment="Downloading images (to {})...".format(in_path))
        image_instances = ImageInstanceCollection().fetch_with_filter("project", cj.parameters.cytomine_id_project)
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
        call("java -cp /icy/lib/ -jar /icy/icy.jar -hl", shell=True, cwd="/icy")
        call("java -cp /icy/lib/ -jar /icy/icy.jar -hl -x plugins.adufour.protocols.Protocols "
             "protocol=\"/icy/protocols/protocol.protocol\" inputFolder=\"{}\" extension=tif csvFileSuffix=_results "
             "scale3enable=true scale3sensitivity={}".format(in_path, scale3sens), shell=True, cwd="/icy")

        cj.job.update(progress=75, status_comment="Extracting polygons...")

        for image in cj.monitor(input_images, start=75, end=90, period=0.1, prefix="Upload annotations and generate masks"):
            file = str(image.id) + "_results.txt"
            path = os.path.join(in_path, file)
            if not os.path.isfile(path):
                print("No output file at '{}' for image with id:{}.".format(path, image.id), file=sys.stderr)

                mask = np.zeros((image.height, image.width), dtype=np.uint8)
                cv2.imwrite(os.path.join(out_path, "{}.png".format(image.id)), mask)
                continue

            # export points to AnnotationSlice
            clean_icy_result_file(path, n=1)  # among others, remove invalid header '== ROI Statistics ==' in result file
            points = csv_to_points(
                path, has_headers=True,
                parse_fn=lambda l, sep: [float(coord) for coord in l.split(sep)[5:7]]
            )

            annotations = AnnotationCollection()
            for _slice in points:
                annotations.append(Annotation(
                    location=affine_transform(_slice.polygon, [1, 0, 0, -1, 0, image.height]).wkt,
                    id_image=image.id,
                    id_project=cj.parameters.cytomine_id_project
                ))
            annotations.save()

            # create masks for metric computations
            mask = slices_to_mask(points, (image.height, image.width))
            tifffile.imsave(os.path.join(out_path, "{}.tif".format(image.id)), mask)

        # Launch the metrics computation here
        cj.job.update(progress=95, statusComment="Computing and uploading metrics...")
        outfiles, reffiles = zip(*[
            (os.path.join(out_path, "{}.tif".format(image.id)),
             os.path.join(gt_path, "{}.tif".format(image.id)))
            for image in input_images
        ])

        results = computemetrics_batch(outfiles, reffiles, "SptCnt", tmp_path)

        for key, value in results.items():
            Property(cj.job, key=key, value=str(value)).save()
        Property(cj.job, key="IMAGE_INSTANCES", value=str([im.id for im in input_images])).save()

        cj.job.update(progress=100, status=Job.TERMINATED, status_comment="Finished.")


if __name__ == "__main__":
    main()
