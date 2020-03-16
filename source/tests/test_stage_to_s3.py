from manifest.stage_to_s3 import StageFile
from utils.logger import Logger
logger = Logger('info')


def test_convert_url():
    relative_path = "s3://bucket-name/object"
    sf = StageFile(logger, relative_path)
    s3_url = sf.get_staged_file()
    logger.info(s3_url)
    assert s3_url.startswith("https://s3.amazonaws.com/")