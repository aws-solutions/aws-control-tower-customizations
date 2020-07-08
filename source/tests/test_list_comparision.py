from utils.list_comparision import compare_lists
from utils.logger import Logger
logger = Logger('info')

list1 = ['aa', 'bb', 'cc'] # add value to list 2
list2 = ['aa', 'bb']  # remove value from list 1
list3 = ['aa', 'cc', 'dd']  # remove and add values from list 1
list4 = ['ee'] # single item list to test replace single account
list5 = ['ff']

def test_add_list():
    assert compare_lists(list2, list1) is False


def test_delete_list():
    assert compare_lists(list1, list2) is False


def test_add_delete_list():
    assert compare_lists(list1, list3) is False


def test_single_item_replacement():
    assert compare_lists(list4, list5) is False


def test_no_change_list():
    assert compare_lists(list1, list1) is True

