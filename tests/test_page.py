
import unittest2

from normalize import Property
from normalize import Record

from unique.store import Page


class BasicUntyped(Record):
    key = Property()
    value = Property()
    primary_key = [key]


class TestPage(unittest2.TestCase):
    def test_from_gitobject(self):
        
        
