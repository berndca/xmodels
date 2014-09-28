from collections import OrderedDict
import logging

from six import with_metaclass
from .fields import BaseField, WrappedObjectField, ValidationException, \
    OptionalAttribute, RequiredAttribute
from .constraints import Stores

from .utils import CommonEqualityMixin, MessageRecord


logger = logging.getLogger(__name__)


def error(logger_inst, message, **kwargs):
    kwargs['errors'].append(message)
    logger_inst.error(message)


class ModelType(type):
    """Creates the metaclass for Model. The main function of this metaclass
    is to move all of fields into the _fields variable on the class.

    """
    def __init__(cls, name, bases, attrs):
        cls._clsfields = {}
        for key, value in attrs.items():
            if isinstance(value, BaseField):
                cls._clsfields[key] = value
                delattr(cls, key)


class SequenceElement(CommonEqualityMixin):

    def __repr__(self):
        return '%s: %s (%d, %d)' % (self.__class__.__name__, self.tag,
                                    self.min_occurs, self.max_occurs)

    def __init__(self, tag, min_occurs=0, max_occurs=0):
        self.tag = tag
        self._min_occurs = min_occurs
        self._max_occurs = max_occurs
        if max_occurs > 0:
            assert min_occurs <= max_occurs

    @property
    def min_occurs(self):
        return self._min_occurs

    @property
    def max_occurs(self):
        return self._max_occurs

    @property
    def required(self):
        return self.min_occurs > 0


class Choice(CommonEqualityMixin):
    """

    """

    def __init__(self, options, required=True, **kwargs):
        super(Choice, self).__init__(**kwargs)
        assert isinstance(options, list)
        self.options = [option for option in options]
        self.required = required
        self._flat_options = self._flat_options_dict()
        self.all_keys_set = set(self._flat_options.keys())
        self.required_keys_sets = self.choice_to_key_sets(True)
        self.optional_keys_sets = self.choice_to_key_sets(False)

    def __str__(self):
        return 'Choice: %s' % self.choice_keys_str()

    def choice_keys_str(self):
        result = ''
        for option in self.options:
            if isinstance(option, list):
                result += ' (%s) ' % ','.join(item.tag for item in option)
            else:
                result += ' %s ' % option.tag
        return '(%s)' % ' | '.join(result.strip().split()).replace(',', ', ')

    def _flat_options_dict(self):
        flattened = []
        assert_msg = "Choice options may only be of type BaseField or " \
                     "list of BaseField"
        for option in self.options:
            if isinstance(option, list):
                for item in option:
                    assert isinstance(item, SequenceElement), assert_msg
                flattened.extend(option)
            else:
                assert isinstance(option, SequenceElement), assert_msg
                flattened.append(option)
        return {option.tag: option for option in flattened}

    def choice_to_key_sets(self, required):
        key_sets = [set([]) for option in self.options]
        for index, option in enumerate(self.options):
            if isinstance(option, SequenceElement):
                if option.required == required:
                    key_sets[index].add(option.tag)
            elif isinstance(option, list):
                [key_sets[index].add(field.tag) for field in option
                 if field.required == required]
        return key_sets

    def match_choice_keys(self, value_key_set, **kwargs):
        no_match_msg = "Could not match keys: %s with: choices: %s" % (
            ', '.join(value_key_set), self.choice_keys_str())
        if value_key_set == set([]) and not self.required:
            return []
        max_key_sets = [self.required_keys_sets[i] | self.optional_keys_sets[i]
                        for i in range(len(self.options))]
        min_key_matches = [value_key_set >= min_keys
                           for min_keys in self.required_keys_sets]
        max_key_matches = [value_key_set <= max_keys
                           for max_keys in max_key_sets]
        if not any(min_key_matches):
            error(logger, no_match_msg, **kwargs)
        if not any(max_key_matches):
            error(logger, no_match_msg, **kwargs)
        if any(min_key_matches) and any(max_key_matches):
            matches = [i for i in range(len(self.options))
                       if min_key_matches[i] and max_key_matches[i]]
            if isinstance(self.options[matches[0]], SequenceElement):
                matched_fields = [self.options[matches[0]].tag]
            else:
                matched_fields = [field.tag
                                  for field in self.options[matches[0]]
                                  if field.tag in value_key_set]
            msg = "Matched keys: %s with option: %d" % \
                  (', '.join(value_key_set), matches[0])
            logger.debug(msg)
            return matched_fields
        return [self._flat_options[tag] for tag in value_key_set
                if tag in self._flat_options]


class Model(with_metaclass(ModelType, CommonEqualityMixin)):
    """The Model is the main component of micromodels. Model makes it trivial
    to parse data from many sources, including JSON APIs.

    You will probably want to initialize this class using the class methods
    :meth:`from_dict` or :meth:`from_kwargs`. If you want to initialize an
    instance without any data, just call :class:`Model` with no parameters.

    :class:`Model` instances have a unique behavior when an attribute is set
    on them. This is needed to properly format data as the fields specify.
    The variable name is referred to as the key, and the value will be called
    the value. For example, in::

        instance = Model()
        instance.age = 18

    ``age`` is the key and ``18`` is the value.

    First, the model checks if it has a field with a name matching the key.

    If there is a matching field, then :meth:`validate` is called on the field
    with the value.
        If :meth:`validate` does not raise an exception, then the result of
        :meth:`validate` is set on the instance, and the method is completed.
        Essentially, this means that the first thing setting an attribute tries
        to do is process the data as if it was a "primitive" data type.

        If :meth:`validate` does raise an exception, this means that the data
        might already be an appropriate Python type. The :class:`Model` then
        attempts to *serialize* the data into a "primitive" type using the
        field's :meth:`to_serial` method.

            If this fails, a ``TypeError`` is raised.

            If it does not fail, the value is set on the instance, and the
            method is complete.

    If the instance doesn't have a field matching the key, then the key and
    value are just set on the instance like any other assignment in Python.

    """

    _allow_extra_elements = False
    _allow_extra_attributes = False

    def __init__(self):
        self._extra = {}
        self._errors = []
        self._data = {}
        self._path = ''
        self._source_to_key = None
        self._defaults = {key: field.default for key, field in
                          self._fields.items() if field.default is not None}
        self._non_empty_fields = set([])

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__,
                           ', '.join(["'%s': %s" % (k, v) for k, v in
                                      sorted(self._fields.items())]))

    def __repr__(self):
        return self.__str__()

    def __getattr__(self, key):
        data = self._data.get(key)
        if data is None:
            data = self._extra.get(key)
        if data is None:
            data = self._defaults.get(key)
        return data

    def __setattr__(self, key, value):
        if key in self._clsfields.keys():
            self._data[key] = value
            if value is not None:
                self._non_empty_fields.add(key)
        elif key.startswith('_'):
            self.__dict__[key] = value
        elif key[0] == '@' and self._allow_extra_attributes:
            self._extra[key] = value
        elif key[0] != '@' and self._allow_extra_elements:
            self._extra[key] = value
        else:
            raise AttributeError

    @classmethod
    def _extract_name_spaces(cls, kwargs, raw_data):
        name_spaces = kwargs.get('name_spaces', {})
        keys_to_delete = []
        for key, value in raw_data.items():
            if key.startswith('@xmlns'):
                name_spaces[value] = key.split(':')[1]
                keys_to_delete.append(key)
        if 'http://www.w3.org/2001/XMLSchema-instance' in name_spaces:
            xsi = name_spaces['http://www.w3.org/2001/XMLSchema-instance']
            schema_location_attr = '@%s:schemaLocation' % xsi
            if schema_location_attr in raw_data:
                keys_to_delete.append(schema_location_attr)
        for key in keys_to_delete:
            del raw_data[key]
        kwargs['errors'] = []
        kwargs['name_spaces'] = name_spaces

    @classmethod
    def from_dict(cls, raw_data, **kwargs):
        """
        This factory for :class:`Model`
        takes either a native Python dictionary or a JSON dictionary/object
        if ``is_json`` is ``True``. The dictionary passed does not need to
        contain all of the values that the Model declares.

        """
        instance = cls()
        # cls._extract_name_spaces(kwargs, raw_data)
        instance.populate(raw_data, **kwargs)
        instance.validate(**kwargs)
        return instance

    def _gen_key_to_from_source(self, name_spaces):
        self._source_to_key = {}
        for key, field in self._clsfields.items():
            source = field.get_source(key)
            if isinstance(field, WrappedObjectField):
                field_name_space = field.name_space
            else:
                field_name_space = self._name_space
            if name_spaces and field_name_space in name_spaces:
                prefix = name_spaces[field_name_space] + ':'
            else:
                prefix = ''
            if source[0] == '@':
                data_key = '@' + prefix + source[1:]
            elif source == '#text':
                data_key = '#text'
            else:
                data_key = prefix + source
            self._source_to_key[data_key] = key
            self._key_to_source = {value: key for key, value in
                                   self._source_to_key.items()}

    def _find_field(self, name):
        if name in self._source_to_key:
            key = self._source_to_key[name]
            if key in self._fields:
                return key

    def _build_path(self, **kwargs):
        path = kwargs.get('path', '')
        index = kwargs.get('instance_index')
        if path:
            base_path = ''.join([path, '.', self.__class__.__name__])
        else:
            base_path = self.__class__.__name__
        if index is not None:
            base_path = ''.join([base_path, '[', str(index), ']'])
            kwargs['instance_index'] = None
        return base_path

    def populate(self, data, **kwargs):
        name_spaces = kwargs.get('name_spaces')
        self._non_empty_fields = set([])
        self._gen_key_to_from_source(name_spaces)
        for name, value in data.items():
            key = self._find_field(name)
            if data is not None:
                if key is not None:
                    self._non_empty_fields.add(key)
            if key:
                field = self._fields[key]
                if isinstance(field, WrappedObjectField):
                    self._data[key] = field.populate(value, **kwargs)
                else:
                    self._data[key] = value
            else:
                self._extra[name] = value

    def validate(self, **kwargs):
        self._path = self._build_path(**kwargs)
        for key, field in self._fields.items():
            data = self._data.get(key)
            if data is not None:
                try:
                    kwargs['path'] = self._path
                    self._data[key] = field.validate(data, **kwargs)
                except ValidationException as e:
                    self._errors.append(MessageRecord(field=key, msg=e.msg))
                    error(logger, e.msg, **kwargs)
        if self._extra and not \
                (self._allow_extra_elements or self._allow_extra_attributes):
            msg = 'Found extra fields: %s' % ','.join(self._extra.keys())
            self._errors.append(MessageRecord(field='_extra', msg=msg))
            error(logger, msg, **kwargs)
        return self

    def deserialize(self, **kwargs):
        for key, field in self._fields.items():
            data = self._data.get(key)
            if data is not None:
                try:
                    kwargs['path'] = self._path
                    self._data[key] = field.deserialize(data, **kwargs)
                except ValidationException as e:
                    self._errors.append(MessageRecord(field=key, msg=e.msg))
                    error(logger, e.msg, **kwargs)
        return self

    def serialize(self, **kwargs):
        for key, field in self._fields.items():
            data = self._data.get(key)
            if data is not None:
                try:
                    kwargs['path'] = self._path
                    self._data[key] = field.serialize(data, **kwargs)
                except ValidationException as e:
                    self._errors.append(MessageRecord(field=key, msg=e.msg))
                    error(logger, e.msg, **kwargs)
        return self

    @property
    def _fields(self):
        return dict(self._clsfields, **self._extra)

    def _get_fields_items(self):
        return self._data.items()

    def to_dict(self, name_spaces=None, **kwargs):
        self.validate(**kwargs)
        result = OrderedDict()
        self._gen_key_to_from_source(name_spaces)
        for key, value in self._get_fields_items():
            if value is not None and key in self._key_to_source:
                name = self._key_to_source[key]
                if isinstance(value, Model):
                    result[name] = value.to_dict(name_spaces=name_spaces)
                elif (isinstance(value, list) and value and
                      isinstance(value[0], Model)):
                    result[name] = [item.to_dict(name_spaces=name_spaces)
                                    for item in value if value is not None]
                else:
                    result[name] = value
        if self._extra:
            for name, value in self._extra.items():
                if value is not None:
                    result[name] = value
        return result


class AttributeModel(Model):
    """Used to describe elements with attributes and no children.
    """
    _value_key = 'value'
    required_attributes = None

    def __init__(self):
        super(AttributeModel, self).__init__()
        if self.required_attributes is None:
            self.required_attributes = []
        for name, field in self._fields.items():
            if not field.source:
                if name == self._value_key:
                    field.source = '#text'
                else:
                    if name in self.required_attributes:
                        attribute_field = RequiredAttribute(field)
                    else:
                        attribute_field = OptionalAttribute(field)
                    field.source = attribute_field.get_source(name)

    def __setattr__(self, key, value):
        if key == 'required_attributes':
            self.__dict__[key] = value
        else:
            return super(AttributeModel, self).__setattr__(key, value)


class SequenceModel(Model):
    _initial = None
    _sequence = None

    def __init__(self):
        super(SequenceModel, self).__init__()
        self._data_sequence = None

    def validate(self, **kwargs):
        self._path = self._build_path(**kwargs)
        if self._initial is not None:
            stores = kwargs.get('stores', Stores())
            self._initial.add_keys(path=self._path, stores=stores)
        super(SequenceModel, self).validate(**kwargs)
        element_tags = []
        for tag in self._non_empty_fields:
            if tag in self._fields and self._data[tag] is not None:
                field = self._fields[tag]
                if not field.isAttribute:
                    element_tags.append(tag)
        self._data_sequence = self.match_sequence(element_tags, **kwargs)

    def match_sequence(self, value_tags, **kwargs):
        result_sequence = []
        path = kwargs.get('path', '')
        for field in self._sequence:
            if isinstance(field, SequenceElement):
                if field.tag in value_tags:
                    result_sequence.append(field.tag)
                elif field.required:
                    msg = "Missing required key: %s %s" % (field.tag, path)
                    self._errors.append(MessageRecord(field=field.tag, msg=msg))
                    error(logger, msg, **kwargs)
            elif isinstance(field, Choice):
                choice_keys_sey = set(value_tags) & field.all_keys_set
                cs = field.match_choice_keys(choice_keys_sey, **kwargs)
                if cs:
                    result_sequence.extend(cs)
        extra_tags = [tag for tag in value_tags if tag not in result_sequence]
        if extra_tags:
            msg = "Could not match tag(s): %s" % ', '.join(extra_tags)
            self._errors.append(MessageRecord(field='_extra', msg=msg))
            error(logger, msg, **kwargs)
        return result_sequence

    def _get_fields_items(self):
        attributes = []
        elements = []
        attribute_keys = set(self._data.keys()) - set(self._data_sequence)
        for key in attribute_keys:
            attributes.append((key, self._data[key]))
        for key in self._data_sequence:
            elements.append((key, self._data[key]))
        return attributes + elements
