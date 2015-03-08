
from normalize import Property
from normalize import Record


class SimpleKeyValue(Record):
    key = Property()
    value = Property()
    primary_key = [key]


class MultiLevelKeyValue(Record):
    key = Property()
    primary_key = [key]
    items = Property(list_of=SimpleKeyValue)
    custom_val = Property(json_name="custval")


