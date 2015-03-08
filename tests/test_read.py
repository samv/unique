
from collections import OrderedDict
import os
import shutil
import tempfile
import unittest2

import git
from normalize import Property
from normalize import Record
from normalize.identity import record_id

from unique.store import Commit
from unique.store import Page
from unique.store import Tree

from testclasses import MultiLevelKeyValue


class BasicUntyped(Record):
    key = Property()
    value = Property()
    primary_key = [key]


class TestRead(unittest2.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.mkdtemp()
        cls.repo = git.repo.Repo.init(cls.tempdir)
        fixtures = os.path.join(
            os.path.split(__file__)[0],
            "fixtures",
        )
        cls.files = {}
        to_add = []
        for root, dirs, files in os.walk(fixtures, topdown=True):
            reldir = os.path.relpath(root, fixtures)
            for fn in dirs:
                os.mkdir(os.path.join(cls.tempdir, reldir, fn))
            for fn in files:
                if fn.endswith(".json"):
                    shutil.copy(
                        os.path.join(fixtures, root, fn),
                        os.path.join(cls.tempdir, reldir, fn),
                    )
                    to_add.append(fn if reldir == os.path.curdir else
                                  os.path.join(reldir, fn))
        for entry in cls.repo.index.add(to_add):
            cls.files[entry.path] = git.objects.Object(
                cls.repo, entry.binsha,
            )
        cls.repo.index.commit("test_read initial fixtures")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tempdir)

    def assertScan(self, store, expected):
        seen = OrderedDict()
        last_key = None
        for key, row in store.scan():
            self.assertIsInstance(key, tuple)
            self.assertIsInstance(row, MultiLevelKeyValue)
            self.assertNotIn(key, seen)
            if last_key is not None:
                self.assertGreater(key, last_key)
            seen[key] = row
        self.assertEqual(len(seen), expected)
        self.last_scanned = seen
        self.last_key = key
        self.last_row = row

    def test_simple_page_read(self):
        page = Page.from_gitobject(
            MultiLevelKeyValue, self.files['Gumdrop.json'],
        )
        self.assertScan(page, 1)
        self.assertEqual(page.get(self.last_key), self.last_row)

    def test_multi_page_read(self):
        page = Page.from_gitobject(
            MultiLevelKeyValue, self.files['Scout-Start.json'],
        )
        self.assertScan(page, 4)
        self.assertEqual(page.range['lte'], self.last_key)
        self.assertEqual(page.get(self.last_key), self.last_row)

    def test_tree_read(self):
        tree = Tree.from_gitobject(
            MultiLevelKeyValue, self.repo.tree().trees[0],
        )
        self.assertScan(tree, 7)
        self.assertEqual(tree.range['lte'], self.last_key)
        self.assertEqual(tree.get(self.last_key), self.last_row)

    def test_commit_read(self):
        commit = Commit.from_gitobject(
            MultiLevelKeyValue, self.repo.commit(),
        )
        self.assertScan(commit, 21)
        self.assertEqual(commit.range['lte'], self.last_key)
        self.assertEqual(commit.get(self.last_key), self.last_row)
