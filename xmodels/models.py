import logging
from six import with_metaclass

from .fields import BaseField, WrappedObjectField, ValidationException, \
    RequiredAttribute, AttributeField
from .constraints import Stores
from .utils import CommonEqualityMixin, MessageRecord


logger = logging.getLogger(__name__)


def error(logger_inst, message, **kwargs):
    kwargs['errors'].append(message)
    logger_inst.error(message)


class SequenceElement(CommonEqualityMixin):
    """
    Container to store xml tag, min_occurs and max_occurs. The property
    required is True when min_occurs > 0.
    """
    def __repr__(self):
        return '%s: %s (%d, %d)' % (self.__class__.__name__, self.tag,
                                    self.min_occurs, self.max_occurs)

    def __init__(self, tag, min_occurs=0, max_occurs=0):
        self.tag = tag
        self._min_occurs = min_occurs
        self._max_occurs = max_occurs
        if 0 < max_occurs < min_occurs:
            raise ValueError

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
    The Choice class describes the options of the xsd:choice element.
    The options attributes is a list of choices. Each option may either
    be a single SequenceElement or a list of SequenceElement (xsd:sequence).
    If required is True, the default, the set of value keys (value_key_set)
    in self.match_choice_keys must match at least one set of required keys
    listed in any option. If required is False, the set of value keys may
    be empty.
    """

    def __init__(self, options, required=True, **kwargs):
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
        return dict((option.tag, option) for option in flattened)

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


class Options(object):
    """
    Container for meta properties.
    """
    def __init__(self, meta):
        self.key_to_source = None
        self.source_to_key = None
        self.allow_extra_element_fields = False
        self.allow_extra_attribute_fields = False
        if meta:
            for key, value in meta.items():
                self.__dict__[key] = value


class ModelType(type):
    """Creates the metaclass for Model. The main function of this metaclass
    is to move all of fields into the _clsfields variable on the class and to
    combine/update the class variables of the inner class Meta into an Options
    instance which is stored under _meta.
    """

    def __new__(cls, name, bases, attrs):
        super_new = super(ModelType, cls).__new__

        if not any(b for b in bases if isinstance(b, ModelType)):
            return super_new(cls, name, bases, attrs)

        module = attrs.pop('__module__')
        new_class = super_new(cls, name, bases, {'__module__': module})
        new_class._clsfields = {}
        new_class._extra = None
        new_class._data = None
        new_class._non_empty_fields = None
        new_class._defaults = {}
        for key, value in attrs.items():
            if isinstance(value, BaseField):
                new_class._clsfields[key] = value
        for key in new_class._clsfields.keys():
            attrs.pop(key, None)
        for key, field in new_class._clsfields.items():
            if field.default is not None:
                new_class._defaults[key] = field.default
        base_meta = getattr(new_class, 'Meta')
        attr_meta = attrs.pop('Meta', None)
        options = Options(base_meta.__dict__)
        if attr_meta:
            for key, value in attr_meta.__dict__.items():
                if not key.startswith('__'):
                    setattr(options, key, value)
        new_class._meta = options
        # Add all attributes to the class.
        for obj_name, obj in attrs.items():
            setattr(new_class, obj_name, obj)
        return new_class


class Model(with_metaclass(ModelType)):
    """The Model is the main component of xmodels.model. It is the base class
    for AttributeModel and SequenceModel implementing common logic.

    Usually one defines a number of fields as class variables. Fields may have
    default values. All fields can be assigned and read. A read to a field which
    has not been set previously return the default value if one exists or None. The
    validate method validates all fields defined as class variables.

    Instance variables may be created in addition to the fields specified as class
     variables if Meta.allow_extra_element_fields is True. Otherwise the model
     validation fails. The validation results are stored in a logger instance.
    """
    class Meta:
        allow_extra_element_fields = False
        allow_extra_attribute_fields = False
        value_key = 'value'
        required_attributes = None
        initial = None
        sequence = None


    def __init__(self):
        self._extra = {}
        self._data = {}
        self._path = ''
        self._non_empty_fields = set([])

    def __str__(self): return '%s(%s): %s' % (self.__class__.__name__,
                                              self.__class__.__base__.__name__,
                                              ', '.join(["'%s': %s" % (k, v)
                                                         for k, v in sorted(self._fields.items())]))

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
        elif key[0] == '@' and self._meta.allow_extra_attribute_fields:
            self._extra[key] = value
        elif key[0] != '@' and self._meta.allow_extra_element_fields:
            self._extra[key] = value
        else:
            raise AttributeError

    @classmethod
    def from_dict(cls, raw_data, **kwargs):
        """
        This factory for :class:`Model` creates a Model from a dict object.
        """
        instance = cls()
        instance.populate(raw_data, **kwargs)
        instance.validate(**kwargs)
        return instance

    def _gen_key_to_from_source(self, name_spaces):
        self._meta.source_to_key = {}
        default_prefix = ''
        if name_spaces and self._meta.name_space in name_spaces:
            default_prefix = ''.join([name_spaces[self._meta.name_space], ':'])
        for key, field in self._clsfields.items():
            source = field.get_source(key, name_spaces, default_prefix)
            self._meta.source_to_key[source] = key
        self._meta.key_to_source = dict(
            [(value, key) for key, value in self._meta.source_to_key.items()])

    def _find_field(self, name):
        if name in self._meta.source_to_key:
            key = self._meta.source_to_key[name]
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
        self._gen_key_to_from_source(name_spaces)
        for name, value in data.items():
            key = self._find_field(name)
            if key:
                field = self._clsfields[key]
                if value is not None or field.accept_none:
                    if key is not None:
                        self._non_empty_fields.add(key)
                if isinstance(field, WrappedObjectField):
                    self._data[key] = field.populate(value, **kwargs)
                else:
                    self._data[key] = value
            else:
                self._extra[name] = value

    def validate(self, **kwargs):
        self._path = self._build_path(**kwargs)
        for key, field in self._clsfields.items():
            data = self._data.get(key)
            if data is not None:
                try:
                    kwargs['path'] = self._path
                    self._data[key] = field.validate(data, **kwargs)
                except ValidationException as e:
                    msg_rec = MessageRecord(path=self._path, field=key,
                                            msg=e.msg)
                    error(logger, msg_rec, **kwargs)
        if self._extra:
            extra_attributes = [key for key in self._extra.keys() if key.startswith('@')]
            extra_elements = [key for key in self._extra.keys() if key not in extra_attributes]
            if extra_attributes and not self._meta.allow_extra_attribute_fields:
                msg = 'Found extra attribute fields: %s' % ','.join(extra_attributes)
                msg_rec = MessageRecord(path=self._path, field='_extra', msg=msg)
                error(logger, msg_rec, **kwargs)
            if extra_elements and not self._meta.allow_extra_element_fields:
                msg = 'Found extra element fields: %s' % ','.join(extra_elements)
                msg_rec = MessageRecord(path=self._path, field='_extra', msg=msg)
                error(logger, msg_rec, **kwargs)
        return self

    def deserialize(self, **kwargs):
        for key, field in self._fields.items():
            data = self._data.get(key)
            if data is not None:
                try:
                    kwargs['path'] = self._path
                    self._data[key] = field.deserialize(data, **kwargs)
                except ValidationException as e:
                    msg_rec = MessageRecord(path=self._path, field=key,
                                            msg=e.msg)
                    error(logger, msg_rec, **kwargs)
        return self

    def serialize(self, **kwargs):
        name_spaces = kwargs.get('name_spaces')
        dict_constructor = kwargs.get('dict_constructor', dict)
        self._gen_key_to_from_source(name_spaces)
        result = dict_constructor()
        for key, value in self._get_fields_items():
            field = self._fields[key]
            if value is not None:
                try:
                    kwargs['path'] = self._path
                    serialized_key = self._meta.key_to_source[key]
                    serialized_data = field.serialize(value, **kwargs)
                    if serialized_data =={}:
                        result[serialized_key] = None
                    else:
                        result[serialized_key] = serialized_data
                except ValidationException as e:
                    msg_rec = MessageRecord(path=self._path, field=key,
                                            msg=e.msg)
                    error(logger, msg_rec, **kwargs)
        result.update(self._extra)
        return result

    @property
    def _fields(self):
        if self._extra:
            return dict(self._clsfields, **self._extra)
        return dict(self._clsfields)

    def _get_fields_items(self):
        return list(self._data.items())


class AttributeModel(Model):
    """Used to describe elements with attributes, an optional
    text value and no children. The key value  used
    for the xml text #text is controlled by Meta.value_key.
    """
    class Meta:
        value_key = 'value'
        required_attributes = None

    def __init__(self):
        super(AttributeModel, self).__init__()
        if self._meta.required_attributes is None:
            self._meta.required_attributes = []
        cls_fields = {}
        for name, field in self._clsfields.items():
            if name == self._meta.value_key:
                cls_fields[name] = self._clsfields[name]
                if not cls_fields[name].source:
                    cls_fields[name].source = '#text'
            else:
                if name in self._meta.required_attributes:
                    cls_fields[name] = RequiredAttribute(field)
                else:
                    cls_fields[name] = AttributeField(field)
        self._clsfields = cls_fields


class SequenceModel(Model):
    """
    The SequenceModel is used to describe xml elements using xsd:sequence.
    The sequence is described with a list of SequenceElement in Meta.sequence.
    The validation method checks if all required attributes and min_occurs > 0
    elements are not None.

    The initial class variable is used for context initialization for identity
    constraints checking.
    """
    class Meta:
        initial = None
        sequence = None

    def __init__(self):
        super(SequenceModel, self).__init__()
        self._data_sequence = None

    def validate(self, **kwargs):
        self._path = self._build_path(**kwargs)
        if self._meta.initial is not None:
            if kwargs.get('stores') is None:
                kwargs['stores'] = Stores()
            self._meta.initial.add_keys(path=self._path, stores=kwargs['stores'])
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
        for field in self._meta.sequence:
            if isinstance(field, SequenceElement):
                if field.tag in value_tags:
                    result_sequence.append(field.tag)
                elif field.required:
                    msg = "Missing required key: %s %s" % (field.tag, path)
                    msg_rec = MessageRecord(path=self._path, field=field.tag,
                                            msg=msg)
                    error(logger, msg_rec, **kwargs)
            elif isinstance(field, Choice):
                choice_keys_sey = set(value_tags) & field.all_keys_set
                cs = field.match_choice_keys(choice_keys_sey, **kwargs)
                if cs:
                    result_sequence.extend(cs)
        extra_tags = [tag for tag in value_tags if tag not in result_sequence]
        if extra_tags:
            msg = "Could not match tag(s): %s" % ', '.join(extra_tags)
            msg_rec = MessageRecord(path=self._path, field='_extra', msg=msg)
            error(logger, msg_rec, **kwargs)
        return result_sequence

    def _get_fields_items(self):
        attribute_keys = set(self._data.keys()) - set(self._data_sequence)
        attributes = [(key, self._data[key]) for key in attribute_keys]
        elements = [(key, self._data[key]) for key in self._data_sequence]
        return attributes + elements

    def from_xml(self, raw_data, **kwargs):
        name_spaces = kwargs.get('name_spaces', {})
        keys_to_delete = []
        root_data = next(iter(raw_data.values()))
        for key, value in root_data.items():
            if key.startswith('@xmlns'):
                name_spaces[value] = key.split(':')[1]
                keys_to_delete.append(key)
        if 'http://www.w3.org/2001/XMLSchema-instance' in name_spaces:
            xsi = name_spaces['http://www.w3.org/2001/XMLSchema-instance']
            schema_location_attr = '@%s:schemaLocation' % xsi
            if schema_location_attr in root_data:
                keys_to_delete.append(schema_location_attr)
        for key in keys_to_delete:
            del root_data[key]
        kwargs['errors'] = []
        kwargs['name_spaces'] = name_spaces
        return self.populate(root_data, **kwargs)

    def serialize(self, **kwargs):
        # FIXME generate sequence
        return super(SequenceModel, self).serialize(**kwargs)
