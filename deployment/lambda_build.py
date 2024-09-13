##############################################################################
#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.   #
#                                                                            #
#  Licensed under the Apache License, Version 2.0 (the "License").           #
#  You may not use this file except in compliance                            #
#  with the License. A copy of the License is located at                     #
#                                                                            #
#      http://www.apache.org/licenses/LICENSE-2.0                            #
#                                                                            #
#  or in the "license" file accompanying this file. This file is             #
#  distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY  #
#  KIND, express or implied. See the License for the specific language       #
#  governing permissions  and limitations under the License.                 #
##############################################################################

# !/usr/bin/env python3
import glob
import os
import shutil
import subprocess
import sys
from pathlib import Path

LIB_PATH = "source/src"
DIST_PATH = "deployment/dist"
HANDLERS_PATH = "source/src/cfct/lambda_handlers"
S3_OUTPUT_PATH = "deployment/regional-s3-assets/"
CODEBUILD_SCRIPTS_PATH = "source/codebuild_scripts"

LAMBDA_BUILD_MAPPING = {
    "state_machine_lambda": "custom-control-tower-state-machine",
    "deployment_lambda": "custom-control-tower-config-deployer",
    "build_scripts": "custom-control-tower-scripts",
    "lifecycle_event_handler": "custom-control-tower-lifecycle-event-handler",
    "state_machine_trigger": "custom-control-tower-state-machine-trigger",
}


def install_dependencies(
    dist_folder: str,
    lib_path: str,
    handlers_path: str,
    codebuild_script_path: str,
    clean: bool = True,
) -> None:
    if os.path.exists(dist_folder) and clean:
        shutil.rmtree(dist_folder)
    subprocess.run(
        ["pip", "install", "--quiet", lib_path, "--target", dist_folder], check=True
    )

    # Capture all installed package versions into requirements.txt
    requirements_path = os.path.join(dist_folder, "requirements.txt")
    subprocess.run(
        ["pip", "freeze", "--path", dist_folder],
        check=True,
        stdout=open(requirements_path, "w")
    )

    # Include lambda handlers in distributables
    for file in glob.glob(f"{handlers_path}/*.py"):
        shutil.copy(src=file, dst=dist_folder)

    # Include Codebuild scripts in distributables
    shutil.copytree(src=codebuild_script_path, dst=f"{dist_folder}/codebuild_scripts")

    # Remove *.dist-info from distributables
    for file in glob.glob(f"{dist_folder}/*.dist-info"):
        shutil.rmtree(path=file)


def create_lambda_archive(zip_file_name: str, source: str, output_path: str) -> None:
    # Create archive for specific lambda
    print(
        f"Contents of {source} will be zipped in {zip_file_name}"
        f" and saved in the {S3_OUTPUT_PATH}"
    )
    archive_path = shutil.make_archive(
        base_name=zip_file_name, format="zip", root_dir=source
    )
    destination_archive_name = f"{output_path}/{Path(archive_path).name}"
    if os.path.exists(destination_archive_name):
        os.remove(destination_archive_name)

    shutil.move(src=archive_path, dst=output_path)


def main(argv):
    print(argv)
    if "help" in argv:
        print(
            "Help: Please provide either or all the arguments as shown in"
            " the example below."
        )
        print(
            "lambda_build.py avm_cr_lambda state_machine_lambda"
            " trigger_lambda deployment_lambda"
        )
        sys.exit(2)
    else:
        os.makedirs(S3_OUTPUT_PATH, exist_ok=True)
        print(" Installing dependencies...")
        install_dependencies(
            dist_folder=DIST_PATH,
            lib_path=LIB_PATH,
            handlers_path=HANDLERS_PATH,
            codebuild_script_path=CODEBUILD_SCRIPTS_PATH,
        )

        for arg in argv:
            if arg in LAMBDA_BUILD_MAPPING:
                print("\n Building {} \n ===========================\n".format(arg))
                zip_file_name = LAMBDA_BUILD_MAPPING[arg]
            else:
                print(
                    "Invalid argument... Please provide either or all the"
                    " arguments as shown in the example below."
                )
                print(
                    "lambda_build.py avm_cr_lambda state_machine_lambda"
                    " trigger_lambda deployment_lambda"
                    " add_on_deployment_lambda"
                )
                sys.exit(2)

            print(f" Creating archive for {zip_file_name}..")
            create_lambda_archive(
                zip_file_name=zip_file_name,
                source=DIST_PATH,
                output_path=S3_OUTPUT_PATH,
            )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1:])
    else:
        print(
            "No arguments provided. Please provide any combination of OR"
            " all 4 arguments as shown in the example below."
        )
        print(
            "lambda_build.py avm_cr_lambda state_machine_lambda"
            " trigger_lambda deployment_lambda add_on_deployment_lambda"
        )
        print("Example 2:")
        print("lambda_build.py avm_cr_lambda state_machine_lambda" " trigger_lambda")
        print("Example 3:")
        print("lambda_build.py avm_cr_lambda state_machine_lambda")
        print("Example 4:")
        print("lambda_build.py avm_cr_lambda")
        sys.exit(2)
