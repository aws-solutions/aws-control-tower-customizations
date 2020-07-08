from aws.utils.get_partition import get_partition
from utils.logger import Logger
from os import environ
logger = Logger('info')

aws_regions_partition = 'aws'
aws_china_regions_partition = 'aws-cn'
aws_us_gov_cloud_regions_partition = 'aws-us-gov'


def test_get_partition_for_us_region():
    environ['AWS_REGION'] = 'us-east-1'
    assert aws_regions_partition == get_partition()


def test_get_partition_for_eu_region():
    environ['AWS_REGION'] = 'eu-west-1'
    assert  aws_regions_partition == get_partition()


def test_get_partition_for_cn_region():
    environ['AWS_REGION'] = 'cn-north-1'
    assert aws_china_regions_partition == get_partition()


def test_get_partition_for_us_gov_cloud_region():
    environ['AWS_REGION'] = 'us-gov-west-1'
    assert aws_us_gov_cloud_regions_partition == get_partition()

