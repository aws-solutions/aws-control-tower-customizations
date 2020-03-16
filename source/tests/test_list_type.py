import pytest
from state_machine_handler import CloudFormation
from utils.logger import Logger
logger = Logger('info')

string1 = 'xx'
string2 = 'yy'
list1 = ['aa', 'bb']
list2 = ['bb', 'dd']
event = {}
cf = CloudFormation(event, logger)


def test_add_list_type():
    assert isinstance(cf._add_list(list1, list2), list)


def test_delete_list_type():
    assert isinstance(cf._delete_list(list1, list2), list)


def test_add_list_string_fail():
    with pytest.raises(ValueError, match=r"Both variables must be list.*"):
        cf._add_list(list1, string1)


def test_add_string_list_fail():
    with pytest.raises(ValueError, match=r"Both variables must be list.*"):
        cf._add_list(string1, list1)


def test_add_strings_fail():
    with pytest.raises(ValueError, match=r"Both variables must be list.*"):
        cf._add_list(string1, string2)


def test_del_list_string_fail():
    with pytest.raises(ValueError, match=r"Both variables must be list.*"):
        cf._delete_list(list1, string1)


def test_del_string_list_fail():
    with pytest.raises(ValueError, match=r"Both variables must be list.*"):
        cf._delete_list(string1, list1)


def test_del_strings_fail():
    with pytest.raises(ValueError, match=r"Both variables must be list.*"):
        cf._delete_list(string1, string2)