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

# !/bin/python
import inspect

from botocore.exceptions import ClientError
from cfct.aws.utils.boto3_session import Boto3Session


class CodePipeline(Boto3Session):
    """This class make code pipeline API calls such as starts code pipeline
    execution, etc.
    """

    def __init__(self, logger, **kwargs):
        self.logger = logger
        __service_name = "codepipeline"
        super().__init__(logger, __service_name, **kwargs)
        self.code_pipeline = super().get_client()

    def start_pipeline_execution(self, code_pipeline_name):
        try:
            response = self.code_pipeline.start_pipeline_execution(
                name=code_pipeline_name
            )
            return response
        except ClientError as e:
            self.logger.log_unhandled_exception(e)
            raise
