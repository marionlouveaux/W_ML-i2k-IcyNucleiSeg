import os
import shutil
import sys
from cytomine.models import *
from subprocess import call

from neubiaswg5 import CLASS_SPTCNT
from neubiaswg5.helpers import prepare_data, NeubiasJob, upload_data, upload_metrics


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
    with NeubiasJob.from_cli(sys.argv[1:]) as nj:
        nj.job.update(status=Job.RUNNING, progress=0, statusComment="Initialisation...")

        # 1. Create working directories on the machine:
        # 2. Download (or read) data
        problem_cls = CLASS_SPTCNT
        in_images, gt_images, in_path, gt_path, out_path, tmp_path = prepare_data(problem_cls, nj, is_2d=True, **nj.flags)

        # 3. Execute workflow
        scale3sens = nj.parameters.icy_scale3sensitivity
        nj.job.update(progress=25, statusComment="Launching workflow...")
        call("java -cp /icy/lib/ -jar /icy/icy.jar -hl", shell=True, cwd="/icy")
        call("java -cp /icy/lib/ -jar /icy/icy.jar -hl -x plugins.adufour.protocols.Protocols "
             "protocol=\"/icy/protocols/protocol.protocol\" inputFolder=\"{}\" extension=tif csvFileSuffix=_results "
             "scale3enable=true scale3sensitivity={}".format(in_path, scale3sens), shell=True, cwd="/icy")

        # Generated csv files must be cleaned: remove invalid header '== ROI Statistics ==' in result file (i.e.
        # remove one line). Also, move CSV file to output folder.
        # If --nodownload is set, image is a filepath. Otherwise, it is an ImageInstance.
        csv_suffix = "_results.txt"
        for image in in_images:
            if isinstance(image, str):
                filename = os.path.join(in_path, os.path.basename(image).rsplit(".", 1)[0])
            else:
                filename = os.path.join(in_path, str(image.id))
            filename += csv_suffix
            clean_icy_result_file(filename, n=1)
            shutil.move(filename, os.path.join(out_path, os.path.basename(filename)))

        # 4. Upload the annotation and labels to Cytomine
        upload_data(
            problem_cls, nj, in_images, out_path,
            is_csv=True, result_file_suffix=csv_suffix,
            generate_mask=True, in_path=in_path,
            has_headers=True,
            parse_fn=lambda l, sep: [float(coord) for coord in l.split(sep)[5:7]],
            **nj.flags, monitor_params={
                "start": 75, "end": 90, "period": 0.1
            }
        )

        # Launch the metrics computation here
        nj.job.update(progress=95, statusComment="Computing and uploading metrics...")
        upload_metrics(problem_cls, nj, in_images, gt_path, out_path, tmp_path, **nj.flags)

        nj.job.update(progress=100, status=Job.TERMINATED, status_comment="Finished.")


if __name__ == "__main__":
    main()
