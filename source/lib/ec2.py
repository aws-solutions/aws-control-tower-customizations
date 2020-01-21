######################################################################################################################
#  Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.                                           #
#                                                                                                                    #
#  Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance        #
#  with the License. A copy of the License is located at                                                             #
#                                                                                                                    #
#      http://www.apache.org/licenses/LICENSE-2.0                                                                                    #
#                                                                                                                    #
#  or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES #
#  OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions    #
#  and limitations under the License.                                                                                #
######################################################################################################################

#!/bin/python
from botocore.exceptions import ClientError
import boto3
import inspect


class EC2(object):
    def __init__(self, logger, region, **kwargs):
        self.logger = logger
        if kwargs is not None:
            if kwargs.get('credentials') is None:
                logger.debug("Setting up EC2 BOTO3 Client with default credentials")
                self.ec2_client = boto3.client('ec2', region_name=region)
            else:
                logger.debug("Setting up EC2 BOTO3 Client with ASSUMED ROLE credentials")
                cred = kwargs.get('credentials')
                self.ec2_client = boto3.client('ec2', region_name=region,
                                               aws_access_key_id=cred.get('AccessKeyId'),
                                               aws_secret_access_key=cred.get('SecretAccessKey'),
                                               aws_session_token=cred.get('SessionToken')
                                               )
        else:
            logger.info("There were no keyworded variables passed.")
            self.ec2_client = boto3.client('ec2', region_name=region)

    def describe_regions(self):
        try:
            response = self.ec2_client.describe_regions()
            return response.get('Regions')
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def describe_vpcs(self):
        try:
            response = self.ec2_client.describe_vpcs()
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'OptInRequired':
                self.logger.info("Caught exception 'OptInRequired', handling the exception...")
                return {"Error": "OptInRequired"}
            elif e.response['Error']['Code'] == 'AuthFailure':
                self.logger.info("Ignoring AuthFailure for the new region(s)")
                return {"Error": "OptInRequired"}
            else:
                message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                           'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
                self.logger.exception(message)
                raise

    def describe_subnets(self, vpc_id):
        try:
            response = self.ec2_client.describe_subnets(
                Filters=[
                    {
                        'Name': 'vpc-id',
                        'Values': [
                            vpc_id,
                        ],
                    },
                ]
            )
            return response
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise

    def describe_availability_zones(self):
        try:
            response = self.ec2_client.describe_availability_zones(Filters=[{'Name': 'state', 'Values': ['available']}])
            return [r['ZoneName'] for r in response['AvailabilityZones']]
        except Exception as e:
            message = {'FILE': __file__.split('/')[-1], 'CLASS': self.__class__.__name__,
                       'METHOD': inspect.stack()[0][3], 'EXCEPTION': str(e)}
            self.logger.exception(message)
            raise
