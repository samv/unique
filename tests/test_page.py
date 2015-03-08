
import os
import shutil
import tempfile
import unittest2

import git
from normalize import Property
from normalize import Record
from normalize.identity import record_id

from unique.store import Page

from testclasses import MultiLevelKeyValue


class BasicUntyped(Record):
    key = Property()
    value = Property()
    primary_key = [key]


class TestPage(unittest2.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.mkdtemp()
        cls.repo = git.repo.Repo.init(cls.tempdir)
        fixtures = os.path.join(
            os.path.split(__file__)[0],
            "fixtures",
        )
        cls.files = {}
        for root, dirs, files in os.walk(fixtures):
            to_add = []
            for fn in files:
                if fn.endswith(".json"):
                    shutil.copy(
                        os.path.join(fixtures, root, fn),
                        os.path.join(cls.tempdir, fn),
                    )
                    to_add.append(fn)
            for entry in cls.repo.index.add(to_add):
                cls.files[entry.path] = git.objects.Object(
                    cls.repo, entry.binsha,
                )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tempdir)

    def test_from_gitobject(self):
        page = Page.from_gitobject(
            MultiLevelKeyValue, self.files['page.json'],
        )
        seen = dict()
        for key, row in page.scan():
            self.assertIsInstance(key, tuple)
            self.assertIsInstance(row, MultiLevelKeyValue)
            self.assertNotIn(key, seen)
            seen[key] = row

        self.assertEqual(len(seen), 1)
        self.assertEqual(page.get(key), row)

    def test_multi_page_read(self):
        page = Page.from_gitobject(
            MultiLevelKeyValue, self.files['Scout-Start.json'],
        )
        seen = dict()
        last_key = None
        for key, row in page.scan():
            self.assertIsInstance(key, tuple)
            if last_key is not None:
                self.assertGreater(key, last_key)
            last_key = key
            self.assertIsInstance(row, MultiLevelKeyValue)
            self.assertNotIn(key, seen)
            seen[key] = row

        self.assertEqual(len(seen), 4)
