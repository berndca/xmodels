"""
The fields module defines various field classes all of which are derived from
BaseField.

Field Methods
~~~~~~~~~~~~~

.. automethod:: BaseField.validate(raw_data, **kwargs)

.. automethod:: BaseField.deserialize(raw_data, **kwargs)

.. automethod:: BaseField.serialize(py_data, **kwargs)

"""

from collections import OrderedDict
import datetime
import logging
import re

from six import string_types

from .utils import CommonEqualityMixin
from .PySO8601 import ParseError, parse, parse_time, parse_date


logger = logging.getLogger(__name__)


class ValidationException(Exception):
    def __init__(self, msg, value):
        super(ValidationException, self).__init__(self, msg, repr(value))
        self._msg = msg
        self._value = value

    def __str__(self):
        return '%s: %s, value:%r' % (self.__class__.__name__, self._msg,
                                     self._value)

    @property
    def msg(self):
        return self._msg


class BaseField(CommonEqualityMixin):
    """Base class for all field types.

    The ``source`` parameter sets the key that will be retrieved from the
    source data. If ``source`` is not specified, the field instance will use
    its own name as the key to retrieve the value from the source data.

    """
    serial_format = None

    def __init__(self, **kwargs):
        self.source = kwargs.get('source')
        self.default = kwargs.get('default')
        self.serial_format = kwargs.get('serial_format', self.serial_format)
        self.isAttribute = False

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.__str__()

    def get_source(self, key):
        """Generates the dictionary key for the serialized representation
        based on the instance variable source and a provided key.

        :param str key: name of the field in model
        :returns: self.source or key
        """
        return self.source or key

    def validate(self, raw_data, **kwargs):
        """The validate method validates raw_data against the field .

        :param raw_data: raw data for field
        :type raw_data: str or other valid formats
        :param bool kwargs['required']: indicates required field
        :param str kwargs['default']: default value, used when raw_data is None
        :param str kwargs['serial_format']: format string for serialization and
        deserialization
        :param str kwargs['source']: field name for serialized version
        :returns: validated_data
        :raises ValidationException: if self.required and raw_data is None
        """
        return raw_data

    def deserialize(self, raw_data, **kwargs):
        return self.validate(raw_data, **kwargs)

    def serialize(self, py_data, **kwargs):
        return self.validate(py_data, **kwargs)


class RequiredAttribute(BaseField):
    """Describes a required XML attribute."""
    required = True

    def __init__(self, field_instance, **kwargs):
        super(RequiredAttribute, self).__init__(**kwargs)
        self.field_instance = field_instance
        self.default = self.field_instance.default
        self.messages = self.field_instance.messages
        self.isAttribute = True

    def get_source(self, key):
        source = self.source or self.field_instance.source or key
        if source.startswith('@'):
            return source
        return '@' + source

    def validate(self, raw_data, **kwargs):
        if raw_data is None:
            if self.required:
                raise ValidationException('Required field has no data.',
                                          self.__str__())
        else:
            return self.field_instance.validate(raw_data, **kwargs)


class OptionalAttribute(RequiredAttribute):
    """Describes an optional XML attribute."""
    required = False


class CharField(BaseField):
    """Field to represent a simple Unicode string value.

    .. doctest::

        >>> from xmodels import CharField
        >>> char_field = CharField()
        >>> char_field.validate(' valid unicode string!\\n')
        'valid unicode string!'
        >>> CharField().validate(42)
        Traceback (most recent call last):
        ...
        xmodels.fields.ValidationException: ValidationException: Expecting a string, value:42
        >>> CharField(minLength=8).validate('0123')
        Traceback (most recent call last):
        ...
        xmodels.fields.ValidationException: ValidationException: Expecting string longer than 8 characters, value:'0123'
        >>> CharField(maxLength=8).validate('0123456789')
        Traceback (most recent call last):
        ...
        xmodels.fields.ValidationException: ValidationException: Expecting string shorter than 8 characters, value:'0123456789'
    """
    strip = True
    minLength = None
    maxLength = None
    messages = dict(
        invalid='Expecting a string',
        tooShort='Expecting string longer than %d characters',
        tooLong='Expecting string shorter than %d characters',
    )

    def __init__(self, **kwargs):
        super(CharField, self).__init__(**kwargs)
        self.strip = kwargs.get('strip', self.strip)
        self.minLength = kwargs.get('minLength', self.minLength)
        self.maxLength = kwargs.get('maxLength', self.maxLength)

    def validate(self, raw_data, **kwargs):
        super(CharField, self).validate(raw_data, **kwargs)
        if not isinstance(raw_data, string_types):
            raise ValidationException(self.messages['invalid'], raw_data)
        stripped = raw_data.strip() if self.strip else raw_data
        if self.minLength is not None:
            if len(stripped) < self.minLength:
                raise ValidationException(self.messages['tooShort']
                                          % self.minLength, stripped)
        if self.maxLength is not None:
            if len(stripped) > self.maxLength:
                raise ValidationException(self.messages['tooLong']
                                          % self.maxLength, stripped)
        return stripped


class RegexField(CharField):
    """

    """
    regex = r''
    messages = dict(
        no_match='The input does not match the regex')

    def __init__(self, **kwargs):
        super(RegexField, self).__init__(**kwargs)
        self.regex = kwargs.get('regex', self.regex)
        self.messages.update(CharField.messages)

    def validate(self, raw_data, **kwargs):
        validated_string = super(RegexField, self).validate(raw_data, **kwargs)
        regex = re.compile(self.regex)
        if not regex.search(validated_string):
            raise ValidationException(self.messages['no_match'], raw_data)
        return validated_string


class Token(CharField):
    """
    Tokens are strings without leading and trailing whitespaces. All other
    whitespaces are collapsed.
    """
    messages = dict(
        whitespace="""Whitespaces should be collapsed in a token."""
    )

    def __init__(self, **kwargs):
        super(Token, self).__init__(**kwargs)
        self.messages.update(CharField.messages)

    def validate(self, raw_data, **kwargs):
        string_value = super(Token, self).validate(raw_data, **kwargs)
        if ' '.join(string_value.split()) != string_value.strip():
            raise ValidationException(self.messages['whitespace'], raw_data)
        return string_value


class Name(RegexField):
    """
    Values of this type must start with a letter, underscore (_), or colon (:),
    and may contain only letters, digits, underscores (_), colons (:), hyphens
    (-), and periods (.). Colons should only be used to separate namespace
    prefixes from local names.

    .. doctest::

        >>> from xmodels import Name
        >>> name_field = Name()
        >>> name_field.validate('valid_name')
        'valid_name'
        >>> name_field.validate('illegal!')
        Traceback (most recent call last):
        ...
        xmodels.fields.ValidationException: ValidationException: A name needs to begin with a letter, colon (:), or
        underscore (_) and shall only contain letters, numbers, and the colon (:),
        underscore (_), dash (-), and dot (.) characters. Only one colon (:) total., value:'illegal!'
    """
    regex = r'^[a-zA-Z:_][\w:_\-\.]*$'
    messages = dict(
        no_match="""A name needs to begin with a letter, colon (:), or
underscore (_) and shall only contain letters, numbers, and the colon (:),
underscore (_), dash (-), and dot (.) characters. Only one colon (:) total.""",
        colons="There should only be ONE colon."
    )

    def validate(self, raw_data, **kwargs):
        validated_string = super(Name, self).validate(raw_data, **kwargs)
        if validated_string.count(':') > 1:
            raise ValidationException(self.messages['colons'], raw_data)
        return validated_string


class NCName(RegexField):
    """
    The type NCName represents an XML non-colonized name, which is simply a
    name that does not contain colons. An NCName must start with either a
    letter or underscore (_) and may contain only letters, digits, underscores
    (_), hyphens (-), and periods (.). This is identical to the Name type,
    except that colons are not permitted.
    """
    regex = r'^[a-zA-Z_][\w_\-\.]*$'
    messages = dict(
        no_match="""A name needs to begin with a letter, or underscore (_) and
shall only contain letters, numbers, and the underscore (_), dash (-), and dot
(.) characters."""
    )


class Language(RegexField):
    """
    The type language represents a natural language identifier, generally used
    to indicate the language of a document or a part of a document. Before
    creating a new attribute of type language, consider using the xml:lang
    attribute that is intended to indicate the natural language of the element
    and its content.  Values of the language type conform to RFC 3066, Tags
    for the Identification of Languages, in version 1.0 and to RFC 4646, Tags
    for Identifying Languages, and RFC 4647, Matching of Language Tags, in
    version 1.1. The three most common formats are:  For ISO-recognized
    languages, the format is a two- or three-letter (usually lowercase)
    language code that conforms to ISO 639, optionally followed by a hyphen
    and a two-letter, usually uppercase, country code that conforms to
    ISO 3166. For example, en or en-US. For languages registered by the
    Internet Assigned Numbers Authority (IANA), the format is i-langname,
    where langname is the registered name. For example, i-navajo.
    For unofficial languages, the format is x-langname, where langname is a
    name of up to eight characters agreed upon by the two parties sharing the
    document. For example, x-Newspeak.  Any of these three formats may have
    additional parts, each preceded by a hyphen, which identify more countries
    or dialects. Schema processors will not verify that values of the language
    type conform to the above rules. They will simply deserialize them based on
    the pattern specified for this type, which says that it must consist of
    one or more parts of up to eight characters each, separated by hyphens.
    """
    regex = r'^([a-zA-Z]{1,8})(-[a-zA-Z]{1,8})*$'
    messages = dict(
        no_match="""A language identifier consists of parts of one to eight
letters separated by a dash (-)."""
    )


class NMTOKEN(RegexField):
    """
    The type NMTOKEN represents a single string token. NMTOKEN values may
    consist of letters, digits, periods (.), hyphens (-), underscores (_), and
    colons (:). They may start with any of these characters. NMTOKEN has a
    whitespace facet value of collapse, so any leading or trailing whitespace
    will be removed. However, no whitespace may appear within the value itself.
    """
    regex = r'^[\w:_\-\.]+$'
    messages = dict(
        no_match='A nmtoken shall only contain letters, numbers,\
 and the colon (:), underscore (_), dash (-), and dot (.) characters.')


class RangeField(BaseField):
    min = None
    max = None
    messages = dict(
        tooSmall='Expecting value greater than %d',
        tooLarge='Expecting value less than %d',
    )

    def __init__(self, **kwargs):
        super(RangeField, self).__init__(**kwargs)
        self.max = kwargs.get('max', self.max)
        self.min = kwargs.get('min', self.min)

    def validate(self, raw_data, **kwargs):
        super(RangeField, self).validate(raw_data, **kwargs)
        if self.min is not None:
            if raw_data < self.min:
                raise ValidationException(self.messages['tooSmall']
                                          % self.min, raw_data)
        if self.max is not None:
            if raw_data > self.max:
                raise ValidationException(self.messages['tooLarge']
                                          % self.max, raw_data)
        return raw_data


class IntegerField(RangeField):
    """Field to represent an integer value"""
    messages = dict(
        invalid="Could not convert to int:"
    )

    def __init__(self, **kwargs):
        super(IntegerField, self).__init__(**kwargs)
        self.messages.update(RangeField.messages)

    def validate(self, raw_data, **kwargs):
        """Convert the raw_data to an integer.

        """
        try:
            converted_data = int(raw_data)
            return super(IntegerField, self).validate(converted_data)
        except ValueError:
            raise ValidationException(self.messages['invalid'], repr(raw_data))


class NonNegativeInteger(IntegerField):
    min = 0


class PositiveInteger(IntegerField):
    min = 1


class NegativeInteger(IntegerField):
    max = -1


class FloatField(RangeField):
    """Field to represent a floating point value. The serial_format uses the
    standard string format notation with the surrounding curly brackets."""

    messages = dict(
        invalid="Could not convert to float:",
        format="Could not convert float to string with format %(format)s.",
    )

    def __init__(self, **kwargs):
        super(FloatField, self).__init__(**kwargs)
        self.messages.update(RangeField.messages)

    def validate(self, raw_data, **kwargs):
        """Convert the raw_data to a float.

        """
        try:
            converted_data = float(raw_data)
            super(FloatField, self).validate(converted_data, **kwargs)
            return raw_data
        except ValueError:
            raise ValidationException(self.messages['invalid'], repr(raw_data))

    def deserialize(self, raw_data, **kwargs):
        valid_data = super(FloatField, self).deserialize(raw_data, **kwargs)
        return float(valid_data)

    def serialize(self, py_data, **kwargs):
        super(FloatField, self).serialize(py_data, **kwargs)
        if self.serial_format:
            try:
                return self.serial_format.format(py_data)
            except (KeyError, ValueError):
                msg = self.messages['format'] % dict(format=self.serial_format)
                raise ValidationException(msg, py_data)
        return str(py_data)


class NonNegativeFloat(FloatField):
    min = 0


class BooleanField(BaseField):
    """Field to represent a boolean. The string ``'True'`` (case insensitive)
    will be converted to ``True``, as will any positive integers and the
    boolean value ``True``.

    .. doctest::

        >>> from xmodels import BooleanField
        >>> BooleanField().validate('TRUE')
        True
        >>> BooleanField().validate('not true!')
        False
        >>> BooleanField().validate(42)
        True
        >>> BooleanField().validate(-3)
        False
        >>> BooleanField().validate(True)
        True

    """

    def validate(self, raw_data, **kwargs):
        """The string ``'True'`` (case insensitive) will be converted
        to ``True``, as will any positive integers.

        """
        super(BooleanField, self).validate(raw_data, **kwargs)
        if isinstance(raw_data, string_types):
            valid_data = raw_data.strip().lower() == 'true'
        elif isinstance(raw_data, bool):
            valid_data = raw_data
        else:
            valid_data = raw_data > 0
        return valid_data

    def serialize(self, py_data, **kwargs):
        super(BooleanField, self).serialize(py_data, **kwargs)
        if py_data:
            return 'true'
        return 'false'


class EnumField(CharField):
    """
    Tests that the value is one of the members of a given list (options). There
    can be no empty strings in options. value has to be a string.

    If matchLower is True it will also compare value.lower() with the lower
    case version of all strings in options.
    """

    options = []
    matchLower = True

    messages = dict(
        invalid='Invalid value',
        notIn='Value must be one of: %(items)s (not %(value)r)')

    def __init__(self, **kwargs):
        super(EnumField, self).__init__(**kwargs)
        self.options = kwargs.get('options', self.options)
        self.messages.update(CharField.messages)
        assert isinstance(self.options, list), \
            'options need to be a list of strings.'
        all_members_strings = True
        for item in self.options:
            all_members_strings = (all_members_strings and
                                   isinstance(item, string_types))
        assert all_members_strings, 'options need to be a list of strings.'
        self.lookup = None
        self.lookup_lower = None

    def validate(self, raw_data, **kwargs):
        string_value = super(EnumField, self).validate(raw_data, **kwargs)
        if not self.lookup:
            self.lookup = {item for item in self.options}
        if not self.lookup_lower:
            self.lookup_lower = {item.lower(): item for item in self.options}
        if string_value in self.lookup:
            return string_value
        lower_case_value = string_value.lower()
        if lower_case_value in self.lookup_lower:
            correct_value = self.lookup_lower[lower_case_value]
            self._raw = correct_value
            return correct_value
        raise ValidationException(self.messages['notIn'] % dict(
            items=self._options_str, value=raw_data), raw_data)

    @property
    def _options_str(self):
        return '; '.join(map(str, self.options))


class DateTimeField(BaseField):
    """Field to represent a datetime

    The ``format`` parameter dictates the format of the input strings, and is
    used in the construction of the :class:`datetime.datetime` object.

    The ``serial_format`` parameter is a strftime formatted string for
    serialization. If ``serial_format`` isn't specified, an ISO formatted
    string will be returned by :meth:`~micromodels.DateTimeField.to_serial`.

    """
    messages = dict(
        parse='%(cls)s Error Parsing %(data)s with format %(format)s'
    )

    def __init__(self, **kwargs):
        super(DateTimeField, self).__init__(**kwargs)
        self.converted = None

    def validate(self, raw_data, **kwargs):
        """The raw_data is returned unchanged."""

        super(DateTimeField, self).validate(raw_data, **kwargs)
        try:
            if isinstance(raw_data, datetime.datetime):
                self.converted = raw_data
            elif self.serial_format is None:
                # parse as iso8601
                self.converted = parse(raw_data)
            else:
                self.converted = datetime.datetime.strptime(raw_data,
                                                            self.serial_format)
            return raw_data
        except (ParseError, ValueError) as e:
            msg = self.messages['parse'] % dict(cls=self.__class__.__name__,
                                                data=raw_data,
                                                format=self.serial_format)
            raise ValidationException(msg, raw_data)

    def deserialize(self, raw_data, **kwargs):
        """A :class:`datetime.datetime` object is returned."""
        super(DateTimeField, self).deserialize(raw_data, **kwargs)
        return self.converted

    def serialize(self, py_data, **kwargs):
        time_obj = self.deserialize(py_data, **kwargs)
        if not self.serial_format:
            return time_obj.isoformat()
        return time_obj.strftime(self.serial_format)


class DateField(DateTimeField):
    """Field to represent a :mod:`datetime.date`"""

    def validate(self, raw_data, **kwargs):
        try:
            if isinstance(raw_data, datetime.datetime):
                valid_data = raw_data.date()
            elif isinstance(raw_data, datetime.date):
                valid_data = raw_data
            elif self.serial_format is None:
                # parse as iso8601
                valid_data = parse_date(raw_data).date()
            else:
                valid_data = datetime.datetime.strptime(
                    raw_data, self.serial_format).date()
            self.converted = valid_data
            return raw_data
        except (ParseError, ValueError) as e:
            msg = self.messages['parse'] % dict(cls=self.__class__.__name__,
                                                data=raw_data,
                                                format=self.serial_format)
            raise ValidationException(msg, raw_data)


class TimeField(DateTimeField):
    """Field to represent a :mod:`datetime.time`"""

    def validate(self, raw_data, **kwargs):
        try:
            if isinstance(raw_data, datetime.datetime):
                valid_data = raw_data.time()
            elif isinstance(raw_data, datetime.time):
                valid_data = raw_data
            elif self.serial_format is None:
                # parse as iso8601
                valid_data = parse_time(raw_data).time()
            else:
                valid_data = datetime.datetime.strptime(
                    raw_data, self.serial_format).time()
            self.converted = valid_data
            return raw_data
        except (ParseError, ValueError) as e:
            msg = self.messages['parse'] % dict(cls=self.__class__.__name__,
                                                data=raw_data,
                                                format=self.serial_format)
            raise ValidationException(msg, raw_data)


class WrappedObjectField(BaseField):
    """Superclass for any fields that wrap an object"""

    def __init__(self, wrapped_class, **kwargs):
        self._wrapped_class = wrapped_class
        super(WrappedObjectField, self).__init__(**kwargs)

    def __str__(self):
        return ''.join([self.__class__.__name__, ': ',
                        self._wrapped_class.__name__])

    def populate(self, raw_data, **kwargs):
        if isinstance(raw_data, self._wrapped_class):
            obj = raw_data
        else:
            obj = self._wrapped_class()
            if isinstance(raw_data, (dict, OrderedDict)):
                obj.populate(raw_data, **kwargs)
            else:
                obj.populate({'#text': raw_data}, **kwargs)
        return obj

    def validate(self, raw_data, **kwargs):
        super(WrappedObjectField, self).validate(raw_data, **kwargs)
        obj = self.populate(raw_data, **kwargs)
        obj.validate(**kwargs)
        return obj

    def deserialize(self, raw_data, **kwargs):
        obj = super(WrappedObjectField, self).deserialize(raw_data, **kwargs)
        return obj.deserialize(**kwargs)

    def serialize(self, py_data, **kwargs):
        return py_data.serialize(**kwargs)

    @property
    def name_space(self):
        return getattr(self._wrapped_class, '_name_space', None)


class ModelField(WrappedObjectField):
    """Field containing a model instance

    Use this field when you wish to nest one object inside another.
    It takes a single required argument, which is the nested class.
    For example, given the following dictionary::

        some_data = {
            'first_item': 'Some value',
            'second_item': {
                'nested_item': 'Some nested value',
            },
        }

    You could build the following classes
    (note that you have to define the inner nested models first)::

        class MyNestedModel(micromodels.Model):
            nested_item = micromodels.CharField()

        class MyMainModel(micromodels.Model):
            first_item = micromodels.CharField()
            second_item = micromodels.ModelField(MyNestedModel)

    Then you can access the data as follows::

        >>> m = MyMainModel(some_data)
        >>> m.first_item
        u'Some value'
        >>> m.second_item.__class__.__name__
        'MyNestedModel'
        >>> m.second_item.nested_item
        u'Some nested value'

    """

    def __init__(self, wrapped_class, **kwargs):
        super(ModelField, self).__init__(wrapped_class, **kwargs)
        self._model_instance = None

    def validate(self, raw_data, **kwargs):
        kwargs.update(instance_index=None)
        return super(ModelField, self).validate(raw_data, **kwargs)


class ModelCollectionField(WrappedObjectField):
    """Field containing a list of model instances.

    Use this field when your source data dictionary contains a list of
    dictionaries. It takes a single required argument, which is the name of the
    nested class that each item in the list should be converted to.
    For example::

        some_data = {
            'list': [
                {'value': 'First value'},
                {'value': 'Second value'},
                {'value': 'Third value'},
            ]
        }

        class MyNestedModel(micromodels.Model):
            value = micromodels.CharField()

        class MyMainModel(micromodels.Model):
            list = micromodels.ModelCollectionField(MyNestedModel)

        >>> m = MyMainModel(some_data)
        >>> len(m.list)
        3
        >>> m.list[0].__class__.__name__
        'MyNestedModel'
        >>> m.list[0].value
        u'First value'
        >>> [item.value for item in m.list]
        [u'First value', u'Second value', u'Third value']

    """

    def __init__(self, wrapped_class, **kwargs):
        super(ModelCollectionField, self).__init__(wrapped_class, **kwargs)

    def populate(self, raw_data, **kwargs):
        if not isinstance(raw_data, list):
            raw_data = [raw_data]
        result = []
        for index, item in enumerate(raw_data):
            path = kwargs.get('path', '<inst>') + '[%d]' % index
            kwargs_copy = {key: value for key, value in kwargs.items()}
            kwargs_copy.update(path=path)
            obj = super(ModelCollectionField, self).populate(item,
                                                             **kwargs_copy)
            result.append(obj)
        return result

    def validate(self, raw_data, **kwargs):
        objects = self.populate(raw_data, **kwargs)
        result = []
        for index, item in enumerate(objects):
            kwargs.update(instance_index=index)
            item.validate(**kwargs)
            result.append(item)
        return result

    def deserialize(self, raw_data, **kwargs):
        objects = self.validate(raw_data, **kwargs)
        return [obj.deserialize(**kwargs) for obj in objects]

    def serialize(self, py_data, **kwargs):
        objects = self.validate(py_data, **kwargs)
        return [obj.serialize(**kwargs) for obj in objects]


class FieldCollectionField(BaseField):
    """Field containing a list of the same type of fields.

    The constructor takes an instance of the field.

    Here are some examples::

        data = {
                    'legal_name': 'John Smith',
                    'aliases': ['Larry', 'Mo', 'Curly']
        }

        class Person(Model):
            legal_name = CharField()
            aliases = FieldCollectionField(CharField())

        p = Person(data)

    And now a quick REPL session::

        >>> p.legal_name
        u'John Smith'
        >>> p.aliases
        [u'Larry', u'Mo', u'Curly']
        >>> p.to_dict()
        {'legal_name': u'John Smith', 'aliases': [u'Larry', u'Mo', u'Curly']}
        >>> p.to_dict() == p.to_dict(serial=True)
        True

    Here is a bit more complicated example involving args and kwargs::

        data = {
                    'name': 'San Andreas',
                    'dates': ['1906-05-11', '1948-11-02', '1970-01-01']
        }

        class FaultLine(Model):
            name = CharField()
            earthquake_dates = FieldCollectionField(DateField('%Y-%m-%d',
                                                    serial_format='%m-%d-%Y'),
                                                    source='dates')

        f = FaultLine(data)

    Notice that source is passed to to the
    :class:`~micromodels.FieldCollectionField`, not the
    :class:`~micromodels.DateField`.

    Let's check out the resulting :class:`~micromodels.Model` instance with the
    REPL::

        >>> f.name
        u'San Andreas'
        >>> f.earthquake_dates
        [datetime.date(1906, 5, 11), datetime.date(1948, 11, 2),
        datetime.date(1970, 1, 1)]
        >>> f.to_dict()
        {'earthquake_dates': [datetime.date(1906, 5, 11),
        datetime.date(1948, 11, 2), datetime.date(1970, 1, 1)],
         'name': u'San Andreas'}
        >>> f.to_dict(serial=True)
        {'earthquake_dates': ['05-11-1906', '11-02-1948', '01-01-1970'],
        'name': u'San Andreas'}
        >>> f.to_json()
        '{"earthquake_dates": ["05-11-1906", "11-02-1948", "01-01-1970"],
        "name": "San Andreas"}'

    """
    def __init__(self, field_instance, **kwargs):
        super(FieldCollectionField, self).__init__(**kwargs)
        if not isinstance(field_instance, BaseField):
            raise TypeError('Field instance of type BaseField expected.')
        self._instance = field_instance

    def __str__(self):
        return '%s(%s)' % (self.__class__.__name__,
                           self._instance.__class__.__name__)

    def validate(self, raw_data, **kwargs):
        if not isinstance(raw_data, list):
            raw_data = [raw_data]
        result = []
        for item in raw_data:
            result.append(self._instance.validate(item))
        return result

    def deserialize(self, raw_data, **kwargs):
        items = self.validate(raw_data, **kwargs)
        result = []
        for item in items:
            result.append(self._instance.deserialize(item))
        return result

    def serialize(self, py_data, **kwargs):
        if not isinstance(py_data, list):
            py_data = [py_data]
        result = []
        for item in py_data:
            result.append(self._instance.serialize(item))
        return result
