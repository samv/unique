
import json

from normalize.visitor import VisitorPattern


class JSONRecordIO(VisitorPattern):
    @classmethod
    def apply(cls, value, prop, visitor):
        json_data = None
        if getattr(prop, "json_name", False) is None:
            json_data = None
        elif getattr(prop, "json_out", False):
            json_data = prop.json_out(value)
        elif hasattr(value, "json_data"):
            json_data = value.json_data()
        else:
            json_data = value
        return json_data

    @classmethod
    def reduce(cls, mapped_props, aggregated, value_type, visitor):
        rv = {}
        for prop, v in mapped_props:
            json_name = getattr(prop, "json_name", prop.name)
            if json_name is not None:
                rv[json_name] = v
        if rv:
            if aggregated:
                rv['values'] = aggregated
            return rv
        else:
            return aggregated

    @classmethod
    def grok(cls, value, value_type, visitor):
        kwargs = value
        if hasattr(value_type, "json_to_initkwargs"):
            kwargs = value_type.json_to_initkwargs(value, {})

        return super(JSONRecordIO, cls).grok(
            kwargs, value_type, visitor
        )

    @classmethod
    def encode_str(cls, item):
        return json.dumps(
            cls.visit(item),
            indent=4,
            separators=(',', ': '),
            sort_keys=True,
        )

    @classmethod
    def encode_many_str(cls, items):
        return json.dumps(
            [cls.visit(item) for item in items],
            indent=4,
            separators=(',', ': '),
            sort_keys=True,
        )

    @classmethod
    def decode_str(cls, record_type, data):
        json_data = json.loads(data)
        return cls.cast(record_type, json_data)

    @classmethod
    def decode_many_str(cls, record_type, data):
        json_data = json.loads(data)
        return [
            cls.cast(record_type, x) for x in json_data
        ]
