"""A Unique Store is the base class for all tree/index stores."""

from abc import ABCMeta
from abc import abstractmethod
from abc import abstractproperty

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
    def from_gitobject(self, record_type, git_object):
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


class Page(Store):
    """A page is a single file in the git repo, which may contain one or more
    rows."""
    record_type = Property(isa=type)

    def __init__(self, record_type, git_object=None, rows=None):
        self.record_type = record_type
        self.git_object = git_object
        self._rowdata = rows

    @classmethod
    def from_gitobject(self, record_type, git_object, prefix=None):
        return Page(record_type, git_object=git_object)

    def scan(self):
        if not self._rowdata:
            self._rowdata = self.encoding.decode_str(
                self.record_type, self.git_object.data_stream.read()
            )
        for v in self._rowdata:
            yield record_id(v), v
