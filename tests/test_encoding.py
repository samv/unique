
import json
import unittest2

from normalize import from_json
from normalize import JsonProperty
from normalize import JsonRecord
from normalize import Property
from normalize import Record
from normalize import to_json

from unique.encoding import JSONRecordIO

from testclasses import MultiLevelKeyValue
from testclasses import SimpleKeyValue


def jdump(obj):
    return json.dumps(
        obj,
        indent=4,
        separators=(',', ': '),
        sort_keys=True,
    )


class CustomMarshalled(JsonRecord):
    key = Property(json_name="id")
    value = Property()

    def json_data(self, **args):
        jd = super(CustomMarshalled, self).json_data(**args)
        jd['oid'] = "1234567"
        return jd

    @classmethod
    def json_to_initkwargs(cls, json_data, kwargs):
        return super(CustomMarshalled, cls).json_to_initkwargs(
            dict((k, v) for k, v in json_data.items() if k != 'oid'),
            kwargs,
        )


class SanityTest(unittest2.TestCase):
    def test_simple_key(self):
        sk = SimpleKeyValue(key="Bob", value="bill")

        encoded = JSONRecordIO.encode_str(sk)
        self.assertEqual(
            encoded, '{\n    "key": "Bob",\n    "value": "bill"\n}',
        )

        decoded = JSONRecordIO.decode_str(SimpleKeyValue, encoded)[0]
        self.assertEqual(sk, decoded)

    def test_multi_level_key(self):
        mlkv = MultiLevelKeyValue(
            key="Casper",
            items=[{"key": "toast", "value": "Charlie_Brown"},
                   {"key": "ham", "value": "Lucy"},
                   {"key": "spam", "value": "Franklin"}],
            custom_val="Minotaur",
        )

        # IO using regular normalize
        default_json = jdump(to_json(mlkv))
        default_decoded = from_json(MultiLevelKeyValue, json.loads(default_json))
        self.assertEqual(mlkv, default_decoded)

        encoded = JSONRecordIO.encode_str(mlkv)
        decoded = JSONRecordIO.decode_str(MultiLevelKeyValue, encoded)[0]
        # FIXME: visitor should either respect all JsonRecord hints or none.
        decoded.custom_val = 'Minotaur'
        self.assertEqual(mlkv, decoded)

