import datetime

import pytest

from tests.definitions import HasAModelField, IsASubModel, Vector, \
    VLNVAttributes
from xmodels import Model, ModelField, ModelCollectionField, \
    FieldCollectionField
from xmodels.fields import IntegerField, BooleanField, \
    ValidationException, BaseField, CharField, RegexField, Token, Name, NCName, \
    Language, NMTOKEN, RangeField, FloatField, NonNegativeInteger, \
    PositiveInteger, NegativeInteger, EnumField, DateTimeField, DateField, \
    TimeField, Attribute


__author__ = 'bernd'


def test_validation_exception():
    e = ValidationException('This is a violation', 41)
    assert str(e) == 'ValidationException: This is a violation, value:41'


class TestBaseField():
    @classmethod
    def setup_class(cls):
        class TestBF(BaseField):
            required = True

        cls.cls = TestBF

    def test_base_field_str_no_data(self):
        test = self.cls()
        assert str(test) == 'TestBF'

    def test_base_field_required_fail(self):
        test = self.cls(required=True)
        with pytest.raises(ValidationException):
            test.deserialize(None)

    def test_deserialize(self):
        actual = self.cls().deserialize('expected')
        assert actual == 'expected'

    def test_eq(self):
        inst1 = self.cls()
        inst2 = self.cls()
        assert inst1 == inst2

    def test_ne(self):
        inst1 = self.cls()
        inst2 = self.cls(required=False)
        assert inst1 != inst2


class TestAttribute():
    @classmethod
    def setup_class(cls):
        cls.instance = Attribute(IntegerField())

    def test_source_from_key(self):
        source = self.instance.get_source('key')
        assert source == '@key'

    def test_source_from_instance_field(self):
        self.instance.field_instance.source = 'my-source'
        source = self.instance.get_source('key')
        assert source == '@my-source'

    def test_source_from_kwarg(self):
        self.instance.source = 'kw-source'
        source = self.instance.get_source('key')
        assert source == '@kw-source'

    def test_deserialize_pass(self):
        result = self.instance.deserialize('42')
        assert result == 42

    def test_deserialize_dail(self):
        with pytest.raises(ValidationException) as exc_info:
            self.instance.deserialize('NaN')
        assert exc_info.value.msg == self.instance.messages['invalid']

    def test_is_attribute(self):
        assert self.instance.is_attribute


class TestCharField():
    @classmethod
    def setup_class(cls):
        cls.instance = CharField(minLength=3, maxLength=8)

    def test_char_field_type_check(self):
        with pytest.raises(ValidationException) as exc_info:
            self.instance.deserialize(11)
        assert exc_info.value.msg == self.instance.messages['invalid']

    def test_char_field_too_short(self):
        with pytest.raises(ValidationException) as exc_info:
            self.instance.deserialize('as')
        assert exc_info.value.msg == self.instance.messages['tooShort'] % 3

    def test_char_field_too_long(self):
        with pytest.raises(ValidationException) as exc_info:
            self.instance.deserialize('123456789')
        assert exc_info.value.msg == self.instance.messages['tooLong'] % 8

    def test_deserialize_char_field_pass(self):
        actual = self.instance.deserialize('valid')
        assert actual == 'valid'

    def test_is_attribute(self):
        assert not self.instance.is_attribute


class TestToken():
    @classmethod
    def setup_class(cls):
        cls.instance = Token()

    def test_token_field_type_check(self):
        with pytest.raises(ValidationException) as exc_info:
            self.instance.deserialize(11)
        assert exc_info.value.msg == self.instance.messages['invalid']

    def test_token_field_too_short(self):
        with pytest.raises(ValidationException) as exc_info:
            self.instance.deserialize('bad because of double  spaces')
        assert exc_info.value.msg == self.instance.messages['whitespace']

    def test_token_field_too_long(self):
        with pytest.raises(ValidationException) as exc_info:
            self.instance.maxLength = 8
            self.instance.deserialize('1234567890')
        assert exc_info.value.msg == self.instance.messages['tooLong'] % 8

    def test_deserialize_token_field_pass(self):
        self.instance.maxLength = None
        actual = self.instance.deserialize('valid:OK single space')
        assert actual == 'valid:OK single space'


class TestRegexField():
    @classmethod
    def setup_class(cls):
        cls.instance = RegexField(regex=r'^[a-zA-Z:_][\w:_\-\.]*$',
                                  maxLength=8)

    def test_regex_field_type_check(self):
        with pytest.raises(ValidationException) as exc_info:
            self.instance.deserialize(11)
        assert exc_info.value.msg == self.instance.messages['invalid']

    def test_regex_field_too_short(self):
        with pytest.raises(ValidationException) as exc_info:
            self.instance.deserialize('bad/')
        assert exc_info.value.msg == self.instance.messages['no_match']

    def test_regex_field_too_long(self):
        with pytest.raises(ValidationException) as exc_info:
            self.instance.deserialize('123456789')
        assert exc_info.value.msg == self.instance.messages['tooLong'] % 8

    def test_deserialize_regex_field_pass(self):
        actual = self.instance.deserialize('valid:OK')
        assert actual == 'valid:OK'


class TestName():
    @classmethod
    def setup_class(cls):
        cls.instance = Name()

    def test_name_fail(self):
        with pytest.raises(ValidationException) as exc_info:
            self.instance.deserialize('has space')
        assert exc_info.value.msg == self.instance.messages['no_match']

    def test_name_two_colons(self):
        with pytest.raises(ValidationException) as exc_info:
            self.instance.deserialize('two:colons:error')
        assert exc_info.value.msg == self.instance.messages['colons']

    def test_name_field_too_long(self):
        with pytest.raises(ValidationException) as exc_info:
            test = Name(maxLength=8)
            test.deserialize('1234567890')
        assert exc_info.value.msg == self.instance.messages['tooLong'] % 8

    def test_deserialize_name_pass(self):
        actual = self.instance.deserialize('  valid:OK \n ')
        assert actual == 'valid:OK'


class TestNCName():
    @classmethod
    def setup_class(cls):
        cls.instance = NCName()

    def test_ncname_fail(self):
        with pytest.raises(ValidationException) as exc_info:
            self.instance.deserialize('has:colon')
        assert exc_info.value.msg == self.instance.messages['no_match']

    def test_ncname_field_too_long(self):
        with pytest.raises(ValidationException) as exc_info:
            test = NCName(maxLength=5)
            test.deserialize('1234567890')
        assert exc_info.value.msg == self.instance.messages['tooLong'] % 5

    def test_deserialize_ncname_pass(self):
        actual = self.instance.deserialize('  valid_OK \n ')
        assert actual == 'valid_OK'


class TestLanguage():
    @classmethod
    def setup_class(cls):
        cls.instance = Language()

    def test_language_fail(self):
        with pytest.raises(ValidationException) as exc_info:
            self.instance.deserialize('has:colon')
        assert exc_info.value.msg == self.instance.messages['no_match']

    def test_language_too_long_fail(self):
        with pytest.raises(ValidationException) as exc_info:
            self.instance.deserialize('Ukrainian-uc')
        assert exc_info.value.msg == self.instance.messages['no_match']

    def test_deserialize_language_field_pass(self):
        actual = self.instance.deserialize('  en-us \n ')
        assert actual == 'en-us'


class TestNmtoken():
    @classmethod
    def setup_class(cls):
        cls.instance = NMTOKEN()

    def test_nmtoken_fail(self):
        with pytest.raises(ValidationException) as exc_info:
            self.instance.deserialize('has space')
        assert exc_info.value.msg == self.instance.messages['no_match']

    def test_deserialize_nmtoken_field_pass(self):
        actual = self.instance.deserialize('  :all_sorts_of-chars. \n ')
        assert actual == ':all_sorts_of-chars.'


class TestRangeField():
    @classmethod
    def setup_class(cls):
        class TestRF(RangeField):
            min = -20
            max = 63

        cls.instance = TestRF()

    def test_range_field_pass(self):
        actual = self.instance.deserialize(42.0)
        assert actual == 42.0

    def test_range_min_fail(self):
        expected = self.instance.messages['tooSmall'] % self.instance.min
        with pytest.raises(ValidationException) as exc_info:
            self.instance.deserialize(-42)
        assert exc_info.value.msg == expected

    def test_range_max_fail(self):
        expected = self.instance.messages['tooLarge'] % self.instance.max
        with pytest.raises(ValidationException) as exc_info:
            self.instance.deserialize(84)
        assert exc_info.value.msg == expected


class TestIntegerField():
    @classmethod
    def setup_class(cls):
        class TestIF(IntegerField):
            min = -20
            max = 63

        cls.instance = TestIF()

    def test_integer_field_pass(self):
        actual = self.instance.deserialize(' 42\n')
        assert actual == 42

    def test_integer_min_fail(self):
        expected = self.instance.messages['tooSmall'] % self.instance.min
        with pytest.raises(ValidationException) as exc_info:
            self.instance.deserialize('-42')
        assert exc_info.value.msg == expected

    def test_integer_max_fail(self):
        expected = self.instance.messages['tooLarge'] % self.instance.max
        with pytest.raises(ValidationException) as exc_info:
            self.instance.deserialize('84')
        assert exc_info.value.msg == expected

    def test_integer_invalid_fail(self):
        with pytest.raises(ValidationException) as exc_info:
            self.instance.deserialize('invalid')
        assert exc_info.value.msg == self.instance.messages['invalid']


def test_non_negative_integer_pass():
    inst = NonNegativeInteger()
    actual = inst.deserialize(0)
    assert actual == 0


def test_non_negative_integer_fail():
    inst = NonNegativeInteger()
    with pytest.raises(ValidationException) as exc_info:
        inst.deserialize(-1)
    expected = inst.messages['tooSmall'] % inst.min
    assert exc_info.value.msg == expected


def test_positive_integer_pass():
    inst = PositiveInteger()
    actual = inst.deserialize(1)
    assert actual == 1


def test_positive_integer_fail():
    inst = PositiveInteger()
    with pytest.raises(ValidationException) as exc_info:
        inst.deserialize(0)
    expected = inst.messages['tooSmall'] % inst.min
    assert exc_info.value.msg == expected


def test_negative_integer_pass():
    inst = NegativeInteger()
    actual = inst.deserialize(-1)
    assert actual == -1


def test_negative_integer_fail():
    inst = NegativeInteger()
    with pytest.raises(ValidationException) as exc_info:
        inst.deserialize(0)
    expected = inst.messages['tooLarge'] % inst.max
    assert exc_info.value.msg == expected


class TestFloatField():
    @classmethod
    def setup_class(cls):
        class TestFF(FloatField):
            min = -20
            max = 63

        cls.instance = TestFF()

    def test_float_field_pass(self):
        actual = self.instance.deserialize(' 42.e-4\n')
        assert actual == 0.0042

    def test_float_min_fail(self):
        expected = self.instance.messages['tooSmall'] % self.instance.min
        with pytest.raises(ValidationException) as exc_info:
            self.instance.deserialize('-42')
        assert exc_info.value.msg == expected

    def test_float_max_fail(self):
        expected = self.instance.messages['tooLarge'] % self.instance.max
        with pytest.raises(ValidationException) as exc_info:
            self.instance.deserialize('84')
        assert exc_info.value.msg == expected

    def test_float_invalid_fail(self):
        with pytest.raises(ValidationException) as exc_info:
            self.instance.deserialize('invalid')
        assert exc_info.value.msg == self.instance.messages['invalid']


class TestBooleanField():
    @classmethod
    def setup_class(cls):
        class TestBF(BooleanField):
            _min = -20
            _max = 63

        cls.instance = TestBF()

    def test_boolean_field_int_true_pass(self):
        actual = self.instance.deserialize(2)
        assert actual is True

    def test_boolean_field_int_false_pass(self):
        actual = self.instance.deserialize(-2)
        assert actual is False

    def test_boolean_field_string_true_pass(self):
        actual = self.instance.deserialize('tRue')
        assert actual is True

    def test_boolean_field_string_false_pass(self):
        actual = self.instance.deserialize('anything else is false')
        assert actual is False

    def test_boolean_field_bool_true_pass(self):
        actual = self.instance.deserialize(True)
        assert actual is True

    def test_boolean_field_bool_false_pass(self):
        actual = self.instance.deserialize(False)
        assert actual is False


class TestEnumField():
    @classmethod
    def setup_class(cls):
        class TestEF(EnumField):
            options = ['One', 'Two', 'Three']

        cls.instance = TestEF()

    def test_enum_field_match_lower_pass(self):
        actual = self.instance.deserialize('one')
        assert actual == 'One'

    def test_enum_field_pass(self):
        actual = self.instance.deserialize('Two')
        assert actual == 'Two'

    def test_enum_field_match_mixed_pass(self):
        actual = self.instance.deserialize('tHRee')
        assert actual == 'Three'

    def test_enum_field_match_mixed_update_raw(self):
        self.instance.deserialize('tHRee')
        assert self.instance._raw == 'Three'

    def test_enum_field_fail(self):
        with pytest.raises(ValidationException) as exc_info:
            self.instance.deserialize('invalid')
        message = self.instance.messages['notIn'] % dict(
            items=self.instance._options_str, value='invalid')
        assert exc_info.value.msg == message


class TestDateTimeFieldTestCase():
    @classmethod
    def setup_class(cls):
        cls.serial_format = "%a %b %d %H:%M:%S +0000 %Y"
        cls.datetimestring = "Tue Mar 21 20:50:14 +0000 2006"
        cls.field = DateTimeField(serial_format=cls.serial_format)

    def test_format_conversion_to_python(self):
        import datetime

        self.field.deserialize(self.datetimestring)
        converted = self.field.deserialize(self.datetimestring)
        assert isinstance(converted, datetime.datetime)

    def test_format_conversion_deserialize(self):
        self.field.deserialize(self.datetimestring)
        converted = self.field.deserialize(self.datetimestring)
        assert converted.strftime(self.serial_format) == self.datetimestring

    def test_iso8601_conversion_z(self):
        import datetime
        from xmodels.PySO8601 import Timezone

        dt_field = DateTimeField()
        dt_field.deserialize("2010-07-13T14:01:00Z")
        expected = datetime.datetime(2010, 7, 13, 14, 1, 0,
                                     tzinfo=Timezone())
        assert expected == dt_field.deserialize("2010-07-13T14:01:00Z")

    def test_iso8601_conversion_0(self):
        import datetime
        from xmodels.PySO8601 import Timezone

        dt_field = DateTimeField()
        dt_field.deserialize("2010-07-13T14:02:00-05:00")
        expected = datetime.datetime(2010, 7, 13, 14, 2, 0,
                                     tzinfo=Timezone("-05:00"))
        assert expected == dt_field.deserialize("2010-07-13T14:02:00-05:00")

    def test_iso8601_conversion_1(self):
        import datetime
        from xmodels.PySO8601 import Timezone

        dt_field = DateTimeField()
        dt_field.deserialize("2010-07-13T14:03:00+05:30")
        expected = datetime.datetime(2010, 7, 13, 14, 3, 0,
                                     tzinfo=Timezone("05:30"))
        assert expected == dt_field.deserialize("2010-07-13T14:03:00+05:30")

    def test_datetime_input(self):
        import datetime
        from xmodels.PySO8601 import Timezone

        datetime_input = datetime.datetime(1989, 11, 9, 15,
                                           tzinfo=Timezone("+01:00"))
        result = DateTimeField().deserialize(datetime_input)
        assert result == datetime_input


class TestDateFieldTestCase():
    @classmethod
    def setup_class(cls):
        cls.serial_format = "%Y-%m-%d"
        cls.datestring = "2010-12-28"
        cls.field = DateField(serial_format=cls.serial_format)

    def test_datetime_input(self):
        import datetime
        from xmodels.PySO8601 import Timezone

        datetime_input = datetime.datetime(1989, 11, 9,
                                           tzinfo=Timezone("+01:00"))
        result = DateField().deserialize(datetime_input)
        assert result == datetime_input

    def test_format_conversion(self):
        import datetime

        dt = self.field.deserialize(self.datestring)
        assert isinstance(dt, datetime.date)
        assert dt.strftime(self.serial_format) == self.datestring


class TestTimeField():
    @classmethod
    def setup_class(cls):
        cls.format = "%H:%M:%S"
        cls.timestring = "09:33:30"
        cls.field = TimeField(format=cls.format)

    def test_format_conversion(self):
        import datetime

        t = self.field.deserialize(self.timestring)
        assert isinstance(t, datetime.time)
        assert t.strftime(self.format) == self.timestring

    def test_iso8601_conversion(self):
        import datetime

        tf = TimeField()
        t = tf.deserialize("09:33:30")
        expected = datetime.time(9, 33, 30)
        assert expected == t

    def test_datetime_time(self):
        import datetime

        tf = TimeField()
        t = tf.deserialize(datetime.time(9, 33, 30))
        expected = datetime.time(9, 33, 30)
        assert expected == t

    def test_datetime(self):
        import datetime

        tf = TimeField()
        dt = datetime.datetime(1989, 11, 9, 9, 33, 30)
        t = tf.deserialize(dt)
        expected = datetime.time(9, 33, 30)
        assert expected == t


class TestModelFieldBasic():
    @classmethod
    def setup_class(cls):
        data = dict(first='42')
        instance = ModelField(IsASubModel)
        cls.deserialized = instance.deserialize(data)

    def test_model_field_deserialize_instance(self):
        assert isinstance(self.deserialized, IsASubModel)

    def test_model_field_deserialize_data(self):
        assert self.deserialized.first == 42

    def test_model_field_default(self):
        field = ModelField(IsASubModel)
        instance = field.deserialize({})
        assert instance.first == 0

    def test_model_field_converted(self):
        import datetime
        from xmodels.PySO8601 import Timezone

        field = ModelField(IsASubModel)
        instance = field.deserialize(dict(dt="2010-07-13T14:03:00+05:30"))
        assert instance.dt == datetime.datetime(
            2010, 7, 13, 14, 3, 0, tzinfo=Timezone("05:30"))

    def test_model_field_str(self):
        assert str(ModelField(IsASubModel)) == 'ModelField: IsASubModel'

    def test_model_field_model_str(self):
        assert str(self.deserialized) == "IsASubModel: 'dt': DateTimeField, " \
                                         "'first': IntegerField"

    def test_get_name_space(self):
        inst = ModelField(Vector)
        ns = inst.name_space
        assert ns == "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"

    def test_get_name_space_none(self):
        inst = ModelField(VLNVAttributes)
        assert inst.name_space is None


class TestHierarchicalModelFieldCreation():
    @classmethod
    def setup_class(cls):
        cls.data = {'first': {'first': '42'}}
        cls.instance = HasAModelField.from_dict(cls.data)

    def test_model_field_sub_model_type(self):
        assert isinstance(self.instance.first, IsASubModel)

    def test_model_field_deserialized_sub_model_data(self):
        assert self.instance.first.first == int(self.data['first']['first'])

    def test_model_field_from_model_instance(self):
        sub_model_instance = IsASubModel.from_dict(dict(first='13'))
        inst = HasAModelField.from_dict(dict(first=sub_model_instance))
        assert inst.first.first == 13

    def test_model_field_second_instance(self):
        first_instance = self.instance
        new_data = dict(first=dict(first=9999), tag='second')
        second_instance = HasAModelField()
        second_instance.populate(new_data)
        assert first_instance.first.first == 42


class TestModelCollectionField():
    def test_model_collection_deserialize(self):
        mc = ModelCollectionField(IsASubModel)
        data = [dict(first='42'), dict(first='1989')]
        result = mc.deserialize(data)
        assert isinstance(result, list)
        assert isinstance(result[0], IsASubModel)
        assert isinstance(result[1], IsASubModel)
        assert len(result) == 2
        assert result[0].first == 42
        assert result[1].first == 1989

    def test_model_collection_deserialize_single(self):
        mc = ModelCollectionField(IsASubModel)
        data = dict(first='1011')
        result = mc.deserialize(data)
        assert isinstance(result, list)
        assert isinstance(result[0], IsASubModel)
        assert len(result) == 1
        assert result[0].first == 1011

    def test_model_collection_field_creation(self):
        class HasAModelCollectionField(Model):
            first = ModelCollectionField(IsASubModel)

        data = {'first': [{'first': '42'}, {'first': '1989'}]}
        instance = HasAModelCollectionField.from_dict(data)
        assert isinstance(instance.first, list)
        # for item in instance.first:
        # self.assertTrue(isinstance(item, IsASubModel))
        # self.assertEqual(instance.first[0].first, data['first'][0]['first'])
        # self.assertEqual(instance.first[1].first, data['first'][1]['first'])

    def test_model_collection_field_with_no_elements(self):
        class IsASubModel(Model):
            first = CharField()

        class HasAModelCollectionField(Model):
            first = ModelCollectionField(IsASubModel)

        data = {'first': []}
        instance = HasAModelCollectionField.from_dict(data)
        assert instance.first == []

    def test_model_collection_to_dict(self):
        class Post(Model):
            title = CharField()
            created = DateTimeField()


        class User(Model):
            name = CharField()
            posts = ModelCollectionField(Post)

        data = {
            'name': 'Eric Martin',
            'posts': [
                {'title': 'Post #1',
                 'created': '2014-08-24T16:57:00'},
                {'title': 'Post #2',
                 'created': "2010-07-13T14:03:00"}
            ]
        }

        eric = User.from_dict(data)
        assert len(eric.posts) == 2
        assert eric.posts[1].title == 'Post #2'
        assert eric.posts[0].title == 'Post #1'
        expected = datetime.datetime(2010, 7, 13, 14, 3)
        assert eric.posts[1].created == expected

class TestFieldCollectionFieldBasic():

    def test_str(self):
        cf = FieldCollectionField(IntegerField())
        assert str(cf) == 'FieldCollectionField(IntegerField)'

    def test_int_list(self):
        data = ['1', '2', '3']
        cf = FieldCollectionField(IntegerField())
        actual = cf.deserialize(data)
        assert actual == [1, 2, 3]

    def test_date_time_single(self):
        dt_list = FieldCollectionField(DateTimeField())
        data = '2012-02-28'
        actual = dt_list.deserialize(data)
        assert actual == [datetime.datetime(2012, 2, 28)]

    def test_date_time_list(self):
        dt_list = FieldCollectionField(DateTimeField())
        data = ['2012-12-25', '2013-07-04T08:55:00']
        actual = dt_list.deserialize(data)
        assert actual == [datetime.datetime(2012, 12, 25),
                          datetime.datetime(2013, 7, 4,8,55)]

    def test_date_time_error(self):
        dt_list = FieldCollectionField(DateTimeField())
        data = ['2012-12-25', 'invalid', '2013-07-04T08:55:00']
        with pytest.raises(ValidationException):
            dt_list.deserialize(data)

    def test_get_name_space(self):
        inst = ModelCollectionField(Vector)
        ns = inst.name_space
        assert ns == "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"

    def test_get_name_space_none(self):
        inst = ModelCollectionField(VLNVAttributes)
        assert inst.name_space is None

