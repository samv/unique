"""A Unique Store is the base class for all tree/index stores."""

from abc import ABCMeta
from abc import abstractmethod
from abc import abstractproperty
from collections import OrderedDict

from normalize import Property
from normalize.identity import record_id

from unique.encoding import JSONRecordIO


class abstractclassmethod(classmethod):

    __isabstractmethod__ = True

    def __init__(self, callable):
        callable.__isabstractmethod__ = True
        super(abstractclassmethod, self).__init__(callable)


class Store(object):
    """The base class for Stores.  Stores know the type of objects within.
    Subclasses can override a data visitor for marshaling.
    """
    __meta__ = ABCMeta
    encoding = JSONRecordIO

    @abstractproperty
    def oid(self):
        """The object ID for this immutable store"""
        pass

    @abstractproperty
    def record_type(self):
        """The type of items stored within.  Must have a primary key
        defined."""
        pass

    @abstractclassmethod
    def from_gitobject(cls, record_type, git_object):
        """Construct a store from an existing git object."""
        pass
                       
    @abstractmethod
    def get(self, key):
        """Return a single row by its key, or throw ``KeyError``
        """
        pass

    @abstractproperty
    def range(self):
        """Return a range object specifying the range of keys in this store.
        """
        pass

    @abstractmethod
    def scan(self, range):
        """Iterator that yields all keys and objects in the range in order.
        Throws ``KeyError`` if out of bounds.
        """
        pass


class MutableStore(Store):
    """A MutableStore is returned by connecting to a Store for update.
    """

    @abstractmethod
    def put(self, key, value):
        """Inserts a value into the store.  Throws ``KeyError`` if the value
        does not already exist."""
        pass

    @abstractmethod
    def post(self, key, value):
        """Inserts a value into the store.  Throws ``KeyError`` if the value
        already exists."""
        pass

    @abstractmethod
    def delete(self, key):
        """Deletes a value from the store.  Throws ``KeyError`` if the value
        does not exist."""
        pass

    def patch(self, key, value, filter):
        """Updates an object with selected fields from the passed value.
        Filter should be a MultiFieldSelector.
        """
        obj = self.get(key)
        filter.patch(obj, value)
        self.put(key, obj)

    @abstractmethod
    def commit(self):
        """Returns an immutable version of the store."""
        pass


class GitStore(Store):
    record_type = Property(isa=type)

    def __init__(self, record_type, git_object=None, prefix=()):
        self.record_type = record_type
        self.git_object = git_object
        self.prefix = ()


class Page(GitStore):
    """A page is a single file in the git repo, which may contain one or more
    rows."""
    def __init__(self, *a, **kw):
        super(Page, self).__init__(*a, **kw)
        self._rowdata = None
        self._range = None

    @classmethod
    def from_gitobject(cls, record_type, git_object, prefix=()):
        return cls(record_type, git_object=git_object, prefix=())

    def scan(self):
        if not self._rowdata:
            self._rowdata = OrderedDict(
                (record_id(v), v) for v in
                self.encoding.decode_str(
                    self.record_type, self.git_object.data_stream.read()
                )
            )
        return self._rowdata.items()

    def get(self, k):
        if not self._rowdata:
            self.scan()
        return self._rowdata[k]

    @property
    def range(self):
        if not self._range:
            lowest = None
            greatest = None
            for k, v in self.scan():
                if greatest is None or k > greatest:
                    greatest = k
                if lowest is None or k < lowest:
                    lowest = k
            self._range = dict(gte=lowest, lte=greatest)
        return self._range


class Tree(GitStore):
    def __init__(self, *a, **kw):
        super(Tree, self).__init__(*a, **kw)
        self._tree = None
        self._range = None

    @classmethod
    def from_gitobject(cls, record_type, git_object, prefix=()):
        return cls(record_type, git_object=git_object, prefix=())

    @property
    def _sub(self):
        if not self._tree:
            self._tree = sorted(
                list(Tree.from_gitobject(self.record_type, x) for
                     x in self.git_object.trees) +
                list(Page.from_gitobject(self.record_type, x) for
                     x in self.git_object.blobs),
                key=lambda x: x.git_object.path,  # XX - not sufficient
            )
        return self._tree

    @property
    def range(self):
        if not self._range:
            lowest = self._sub[0].range
            greatest = self._sub[-1].range
            self._range = dict(gte=lowest['gte'], lte=greatest['lte'])
        return self._range

    def scan(self):
        for sub in self._sub:
            for k, v in sub.scan():
                yield k, v

    def get(self, k):
        if k > self._range['lte'] or k < self._range['gte']:
            raise KeyError(k)
        sub = self._sub
        top = len(sub) - 1
        bottom = 0
        while top > bottom:
            x = (top + bottom) / 2
            item = sub[x]
            too_big = item.range['lte'] > k
            too_small = item.range['gte'] < k
            if not too_big and not too_small:
                top = bottom = x
            elif too_big:
                top = x - 1
            elif too_small:
                bottom = x + 1
        return sub[bottom].get(k)


class Commit(Tree):
    def __init__(self, *a, **kw):
        super(Commit, self).__init__(*a, **kw)
        self._tree = None
        self._range = None

    @property
    def _sub(self):
        if not self._tree:
            self._tree = [Tree(self.record_type, self.git_object.tree)]
        return self._tree
