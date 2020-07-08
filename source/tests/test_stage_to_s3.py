from manifest.stage_to_s3 import StageFile
from utils.logger import Logger
from os import environ
logger = Logger('info')


def test_convert_url():
    bucket_name = 'my-bucket-name'
    key_name = 'my-key-name'
    relative_path = "s3://" + bucket_name + "/" + key_name
    sf = StageFile(logger, relative_path)
    s3_url = sf.get_staged_file()
    logger.info(s3_url)
    assert s3_url.startswith("{}{}{}{}{}{}".format('https://',
                                                   bucket_name,
                                                   '.s3.',
                                                   environ.get('AWS_REGION'),
                                                   '.amazonaws.com/',
                                                   key_name))