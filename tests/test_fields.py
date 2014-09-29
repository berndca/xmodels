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
    TimeField, OptionalAttribute, RequiredAttribute
from xmodels.iso8601 import Timezone


def test_validation_exception():
    e = ValidationException('This is a violation', 41)
    assert str(e) == 'ValidationException: This is a violation, value:41'


class TestBaseField():
    @classmethod
    def setup_class(cls):
        class TestBF(RequiredAttribute):
            required = True

        cls.cls = TestBF

    def test_base_field_str_no_data(self):
        test = self.cls(CharField())
        assert str(test) == 'TestBF'

    def test_base_field_repr_no_data(self):
        test = self.cls(CharField())
        assert repr(test) == 'TestBF'

    def test_base_field_required_fail(self):
        test = self.cls(CharField())
        with pytest.raises(ValidationException):
            test.deserialize(None)

    def test_deserialize(self):
        actual = self.cls(CharField()).deserialize('expected')
        assert actual == 'expected'

    def test_eq(self):
        inst1 = self.cls(CharField())
        inst2 = self.cls(CharField())
        assert inst1 == inst2

    def test_ne(self):
        inst1 = RequiredAttribute(CharField())
        inst2 = OptionalAttribute(CharField())
        assert inst1 != inst2

    def test_name_space_kwarg(self):
        name_space="http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"
        id = OptionalAttribute(CharField(name_space=name_space))
        assert id.name_space == name_space


class TestAttribute():
    @classmethod
    def setup_class(cls):
        cls.instance = OptionalAttribute(IntegerField())

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
        assert self.instance.isAttribute

def test_required_attribute_full_source():
    attr = RequiredAttribute(CharField(source='@id'))
    assert attr.get_source('test') == '@id'

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
        assert not self.instance.isAttribute


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

    def test_serialize_no_format(self):
        self.instance.serial_format = None
        assert self.instance.serialize(3.14) == '3.14'

    def test_serialize_basic_format(self):
        self.instance.serial_format = '{:e}'
        assert self.instance.serialize(3.14) == '3.140000e+00'

    def test_serialize_basic_fail(self):
        self.instance.serial_format = '{invalid}'
        with pytest.raises(ValidationException) as exc_info:
            self.instance.serialize('3.14')
        assert exc_info.value.msg == self.instance.messages['format'] %dict(
            format=self.instance.serial_format)


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

    def test_boolean_field_bool_serialize_true(self):
        actual = self.instance.serialize(True)
        assert actual == 'true'

    def test_boolean_field_bool_serialize_false(self):
        actual = self.instance.serialize(0)
        assert actual == 'false'


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


class TestFormattedDateTimeField():
    @classmethod
    def setup_class(cls):
        cls.serial_format = "%a %b %d %H:%M:%S +0000 %Y"
        cls.datetimestring = "Tue Mar 21 20:50:14 +0000 2006"
        cls.field = DateTimeField(serial_format=cls.serial_format)

    def test_format_conversion_to_python(self):
        self.field.deserialize(self.datetimestring)
        converted = self.field.deserialize(self.datetimestring)
        assert isinstance(converted, datetime.datetime)

    def test_format_conversion_deserialize(self):
        self.field.deserialize(self.datetimestring)
        converted = self.field.deserialize(self.datetimestring)
        assert converted.strftime(self.serial_format) == self.datetimestring

    def test_datetime_serialize(self):
        datetime_input = datetime.datetime(1989, 11, 9, 15,
                                           tzinfo=Timezone("+01:00"))
        result = self.field.serialize(datetime_input)
        assert result == 'Thu Nov 09 15:00:00 +0000 1989'


class TestISO8601DateTimeField():

    def test_conversion_z(self):
        dt_field = DateTimeField()
        expected = datetime.datetime(2010, 7, 13, 14, 1, 0,
                                     tzinfo=Timezone())
        assert expected == dt_field.deserialize("2010-07-13T14:01:00Z")

    def test_conversion_0(self):
        dt_field = DateTimeField()
        expected = datetime.datetime(2010, 7, 13, 14, 2, 0,
                                     tzinfo=Timezone("-05:00"))
        assert expected == dt_field.deserialize("2010-07-13T14:02:00-05:00")

    def test_conversion_1(self):
        dt_field = DateTimeField()
        expected = datetime.datetime(2010, 7, 13, 14, 3, 0,
                                     tzinfo=Timezone("05:30"))
        assert expected == dt_field.deserialize("2010-07-13T14:03:00+05:30")

    def test_conversion_2(self):
        dt_field = DateTimeField()
        expected = datetime.datetime(2011, 1, 13, 16, 44, 00, tzinfo=Timezone())
        assert expected == dt_field.deserialize("20110113T164400Z")

    def test_conversion_3(self):
        dt_field = DateTimeField()
        expected = datetime.datetime(2011, 1, 13, 16, 44, 00, tzinfo=Timezone())
        assert expected == dt_field.deserialize("20110113T1644Z")

    def test_conversion_4(self):
        dt_field = DateTimeField()
        expected = datetime.datetime(2011, 1, 13, 16, 44, 00)
        assert expected == dt_field.deserialize("20110113T164400")

    def test_conversion_5(self):
        dt_field = DateTimeField()
        expected = datetime.datetime(2011, 1, 13, 16, 44, 00)
        assert expected == dt_field.deserialize("20110113T1644")

    def test_conversion_6(self):
        dt_field = DateTimeField()
        expected = datetime.datetime(2010, 2, 1)
        assert expected == dt_field.deserialize("2010W052")

    def test_conversion_7(self):
        dt_field = DateTimeField()
        expected = datetime.datetime(2010, 2, 1, 12, 1, 15, 2,
                                     tzinfo=Timezone())
        assert expected == dt_field.deserialize("2010W052T120115.002Z")

    def test_conversion_8(self):
        dt_field = DateTimeField()
        expected = datetime.datetime(2010, 8, 22)
        assert expected == dt_field.deserialize("2010234")

    def test_conversion_9(self):
        dt_field = DateTimeField()
        expected = datetime.datetime(2010, 8, 22, 15, 52, 42, 763)
        assert expected == dt_field.deserialize("2010234T155242.763")

    def test_conversion_a(self):
        dt_field = DateTimeField()
        expected = datetime.datetime(2007, 1, 2)
        assert expected == dt_field.deserialize("20070102")

    def test_conversion_b(self):
        dt_field = DateTimeField()
        expected = datetime.datetime(2007, 1, 2)
        assert expected == dt_field.deserialize("070102")

    def test_conversion_c(self):
        dt_field = DateTimeField()
        expected = datetime.datetime(2007, 1, 1)
        assert expected == dt_field.deserialize("2007")

    def test_conversion_d(self):
        dt_field = DateTimeField()
        today = datetime.date.today()
        expected = datetime.datetime(today.year, today.month, today.day,
                                     16, 47, 21)
        assert expected == dt_field.deserialize('16:47:21')

    def test_datetime_input(self):
        datetime_input = datetime.datetime(1989, 11, 9, 15,
                                           tzinfo=Timezone("+01:00"))
        result = DateTimeField().deserialize(datetime_input)
        assert result == datetime_input

    def test_datetime_serialize_isoformat(self):
        datetime_input = datetime.datetime(1989, 11, 9, 15,
                                           tzinfo=Timezone("+01:00"))
        result = DateTimeField().serialize(datetime_input)
        assert result == '1989-11-09T15:00:00+01:00'

    def test_timezone_repr(self):
        tz = Timezone('-07:00')
        assert repr(tz) == '<Timezone UTC-07:00>'

    def test_timezone_str(self):
        tz = Timezone('-07:00')
        assert str(tz) == 'UTC-07:00'


class TestDateFieldTestCase():
    @classmethod
    def setup_class(cls):
        cls.serial_format = "%Y-%b-%d"
        cls.datestring = "2010-12-28"
        cls.field = DateField(serial_format=cls.serial_format)

    def test_datetime_input(self):
        datetime_input = datetime.datetime(1989, 11, 9,
                                           tzinfo=Timezone("+01:00"))
        result = self.field.deserialize(datetime_input)
        assert result == datetime_input.date()

    def test_date_input(self):
        datetime_input = datetime.date(1989, 11, 9)
        result = self.field.deserialize(datetime_input)
        assert result == datetime_input

    def test_date_input_isoformat(self):
        result = DateField().deserialize('1989-11-09')
        assert result == datetime.date(1989, 11, 9)

    def test_date_input_fail_parse(self):
        with pytest.raises(ValidationException):
            DateField().deserialize('not a date')

    def test_date_input_fail_value(self):
        with pytest.raises(ValidationException):
            self.field.deserialize('not a date')

    def test_format_serialize_default(self):
        date_str = DateField().serialize(datetime.date(1989, 11, 9))
        assert date_str == '1989-11-09'

    def test_format_serialize_format(self):
        date_str = self.field.serialize(datetime.date(1989, 11, 9))
        assert date_str == '1989-Nov-09'


class TestTimeField():
    @classmethod
    def setup_class(cls):
        cls.format = "%H.%M.%S"
        cls.timestring = "09.33.30"
        cls.field = TimeField(serial_format=cls.format)

    def test_format_conversion(self):
        t = self.field.deserialize(self.timestring)
        assert isinstance(t, datetime.time)
        assert t.strftime(self.format) == self.timestring

    def test_iso8601_conversion(self):
        tf = TimeField()
        t = tf.deserialize("09:33:30")
        expected = datetime.time(9, 33, 30)
        assert expected == t

    def test_value_fail(self):
        with pytest.raises(ValidationException):
            self.field.deserialize("not a time")

    def test_parse_fail(self):
        with pytest.raises(ValidationException):
            TimeField().deserialize("not a time")

    def test_datetime_time(self):
        tf = TimeField()
        t = tf.deserialize(datetime.time(9, 33, 30))
        expected = datetime.time(9, 33, 30)
        assert expected == t

    def test_datetime(self):
        dt = datetime.datetime(1989, 11, 9, 9, 33, 30)
        assert self.field.deserialize(dt) == datetime.time(9, 33, 30)

    def test_serialize_default(self):
        assert TimeField().serialize(datetime.time(9, 33, 30)) == "09:33:30"

    def test_serialize_format(self):
        assert self.field.serialize(datetime.time(9, 33, 30)) == "09.33.30"



class TestTimeFieldISO8601():

    def test_time_colons(self):
        assert TimeField().deserialize('16:47:21') == datetime.time(16, 47, 21)

    def test_time_just_digits(self):
        assert TimeField().deserialize('164721') == datetime.time(16, 47, 21)

    def test_time_just_digits2(self):
        expected = datetime.time(16, 47, 21, 854)
        assert TimeField().deserialize('16:47:21.854Z') == expected


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
        from xmodels.iso8601 import Timezone

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

    def test_serialize(self):
        mc = ModelField(IsASubModel)
        sm = IsASubModel()
        sm.first = 1
        sm.dt = datetime.datetime(1973, 9, 11, 5)
        actual = mc.serialize(sm)
        assert actual == {'dt': '1973-09-11T05:00:00', 'first': 1}


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

    def test_model_collection_field_with_no_elements(self):
        class IsASubModel(Model):
            first = CharField()

        class HasAModelCollectionField(Model):
            first = ModelCollectionField(IsASubModel)

        data = {'first': []}
        instance = HasAModelCollectionField.from_dict(data)
        assert instance.first == []

    def test_serialize(self):
        mc = ModelCollectionField(IsASubModel)
        sm = [IsASubModel(), IsASubModel()]
        sm[0].first = 1
        sm[0].dt = datetime.datetime(1973, 9, 11, 5)
        sm[1].first= 42
        sm[1].dt = datetime.datetime(1945, 8, 9, 11, 2)
        actual = mc.serialize(sm)
        assert actual == [
            {'dt': '1973-09-11T05:00:00', 'first': 1},
            {'dt': '1945-08-09T11:02:00', 'first': 42}
        ]

class TestModelCollectionFieldFromDict():
    @classmethod
    def setup_class(cls):
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

        cls.eric = User.from_dict(data)
        cls.eric.deserialize()

    def test_str(self):
        assert str(self.eric) == "User: 'name': CharField, " \
                                 "'posts': ModelCollectionField: Post"

    def test_len_posts(self):
        assert len(self.eric.posts) == 2

    def test_title_1(self):
        assert self.eric.posts[1].title == 'Post #2'

    def test_title_0(self):
        assert self.eric.posts[0].title == 'Post #1'

    def test_created_1(self):
        expected = datetime.datetime(2010, 7, 13, 14, 3)
        assert self.eric.posts[1].created == expected

class TestFieldCollectionFieldBasic():

    def test_str(self):
        cf = FieldCollectionField(IntegerField())
        assert str(cf) == 'FieldCollectionField(IntegerField)'

    def test_int_list(self):
        data = ['1', '2', '3']
        cf = FieldCollectionField(IntegerField())
        actual = cf.deserialize(data)
        assert actual == [1, 2, 3]

    def test_constructor_fail(self):
        with pytest.raises(TypeError):
            FieldCollectionField('invalid')

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

    def test_serialize_floats(self):
        field = FieldCollectionField(FloatField(serial_format='{0:.3f}'))
        result = field.serialize([1, 2, 3])
        assert result == ['1.000', '2.000', '3.000']

    def test_serialize_single_float(self):
        field = FieldCollectionField(FloatField(serial_format='{0:.3f}'))
        result = field.serialize(4)
        assert result == ['4.000']
