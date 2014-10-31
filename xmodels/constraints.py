from __future__ import unicode_literals
from collections import namedtuple
import logging

from six import string_types

from .fields import RegexField, ValidationException, NCName, Name


logger = logging.getLogger(__name__)

KeyRef = namedtuple('KeyRef', 'key_name key_value ref_path')


class KeyStore(object):
    """
    Base class for all key and unique stores. It contains two dictionaries:
    * index: {key_name: list_of_target_paths}
    * keys: {'%s:%s % (key_name, target_path): {key_value: key_path}}
    """
    def __init__(self):
        self.index = {}
        self.keys = {}

    def add_key(self, key_names, target_path):
        if isinstance(key_names, list):
            key_names_list = key_names
        else:
            key_names_list = [key_names]
        for key_name in key_names_list:
            key = '%s:%s' % (key_name, target_path)
            if key in self.keys:
                raise ValidationException('Key %s does already exist.' % key,
                                          target_path)
            if key_name not in self.index:
                self.index[key_name] = [target_path]
            else:
                self.index[key_name].append(target_path)
            self.keys[key] = {}

    def in_keys(self, key_name, target_path):
        return '%s:%s' % (key_name, target_path) in self.keys

    def add_value(self, key_names, target_path, key_value, key_path):
        if isinstance(key_names, string_types):
            key_names_list = [key_names]
        else:
            key_names_list = key_names
        for key_name in key_names_list:
            key = '%s:%s' % (key_name, target_path)
            if self.in_keys(key_name, target_path):
                if key_value in self.keys[key]:
                    msg = 'Duplicate key value %s for %s at %s' % (key_value,
                                                                   key_name,
                                                                   key_path)
                    raise ValidationException(msg, key_value)
                self.keys[key][key_value] = key_path
                return True
        msg = 'Could not find target path %s for key name(s) %s' % \
              (target_path, ', '.join(key_names_list))
        raise ValidationException(msg, key_value)

    def match_ref(self, key_name, ref_key_value):
        if key_name not in self.index:
            raise ValidationException('No key for %s exists' % key_name,
                                      key_name)
        for key_path in self.index[key_name]:
            key = '%s:%s' % (key_name, key_path)
            for key_value, instance_path in self.keys[key].items():
                if key_value == ref_key_value:
                    return instance_path
        raise ValidationException('Could not match ref %s for %s' % (
            ref_key_value, key_name), ref_key_value)

    def key_value_count(self, key_name, target_path):
        key = '%s:%s' % (key_name, target_path)
        if key in self.keys:
            return len(self.keys[key])
        return 0


class IDStore(KeyStore):
    """
    ID's are a special case of key since all of them share the same path '/'
    and of course they all share the same name 'ID'.
    """
    key_name = 'ID'
    path = '/'

    def __init__(self):
        super(IDStore, self).__init__()
        super(IDStore, self).add_key(self.key_name, self.path)

    def add_id(self, key_value, key_path):
        super(IDStore, self).add_value(self.key_name, self.path,
                                       key_value, key_path)

    def match_id(self, ref_key_value):
        return super(IDStore, self).match_ref(self.key_name, ref_key_value)

    def id_count(self):
        return super(IDStore, self).key_value_count(self.key_name, self.path)


class RefStore(object):
    """
    Store for keyref identity constraints.
    * refs: list of namedtuple KeyRef(key_name, key_value, ref_path)
    * targets: dict {ref_path: target_path}
    """
    def __init__(self):
        self.refs = []
        self.targets = {}

    def add_key_ref(self, key_name, key_value, ref_path):
        if not key_value:
            raise ValidationException('key value is required', key_value)
        self.refs.append(KeyRef(key_name, key_value, ref_path))

    def set_target(self, ref_path, target_path):
        if ref_path in self.targets:
            raise ValidationException('Target for ref_path already exists.',
                                      ref_path)
        self.targets[ref_path] = target_path


class IDREFStore(RefStore):
    """
    Store for IDREF. All IDREF refer to the same key: 'ID'.
    """

    def add_idref(self, key_value, ref_path):
        super(IDREFStore, self).add_key_ref('ID', key_value, ref_path)


class Stores(object):
    """
    Combination of all identity constraint related stores in a single object.
    """
    def __init__(self):
        self.keyStore = KeyStore()
        self.uniquesStore = KeyStore()
        self.idStore = IDStore()
        self.refStore = RefStore()
        self.idrefStore = IDREFStore()


def get_value_path_stores(**kwargs):
    messages = dict(
        path='No path supplied.',
        store='Parameter store of type Stores expected.',
    )

    stores = kwargs.get('stores')
    path = kwargs.get('path')
    if stores is not None:
        if not isinstance(stores, Stores):
            raise TypeError(messages['store'])
    return path, stores


class InitStores(object):
    """
    Initializes stores.keyStore uf key_names or stores.uniquesStore
    if unique_names by adding keys/path.
    """
    key_names = None
    unique_names = None
    messages = dict(
        name='key names (string or list of strings) is required and can not '
             'be empty.',
        store='Parameter store of type Stores expected.',
    )

    def add_keys(self, path='', stores=None):
        if self.key_names:
            stores.keyStore.add_key(self.key_names, path)
        if self.unique_names:
            stores.uniquesStore.add_key(self.unique_names, path)

    def check_key_name(self, key_name):
        if not key_name or not isinstance(key_name, string_types):
            raise ValueError(self.messages['name'])


class InitKeyStore(InitStores):
    """
    Creates an empty dict under
    stores.keyStore[keyName:keyTargetInstancePath]
    """
    messages = dict(
        name='keyName (string) is required and can not be empty.',
        store='Parameter store of type Stores expected.',
    )

    def __init__(self, key_name):
        self.check_key_name(key_name)
        self.key_names = [key_name]


class InitUniqueStore(InitStores):
    """
    Creates an empty dict under
    stores.uniquesStore[keyName:keyTargetInstancePath]
    """
    def __init__(self, key_name):
        self.check_key_name(key_name)
        self.unique_names = [key_name]


class SetupKeyRefsStore(object):
    """
    """
    string_validator_instance = None
    refer_key_name = None
    messages = dict(
        names='%(keyNames (type list of strings or string) is is required.',
        emptyValue='Value may not be empty.',
    )

    def __init__(self, refer_key_name, **kwargs):
        self.string_validator_instance = kwargs.get(
            'string_validator_instance', self.string_validator_instance)
        self.refer_key_name = refer_key_name

    def validate(self, key_value, **kwargs):
        path, stores = get_value_path_stores(**kwargs)
        if self.string_validator_instance:
            string_value = self.string_validator_instance.validate(key_value)
        else:
            string_value = key_value
        if stores:
            stores.refStore.add_key_ref(self.refer_key_name,
                                        string_value, path)
        return string_value


class CheckKeys(object):
    """
    Determines the targetPath by removing <level>s from path.

    Looks up store[keyName:keyTargetInstancePath] for all

    keyNames and checks the dict if keyValue (element.value) is already
    present (duplicate error). If not it adds the element.value as key
    and element.path as value.
    """
    not_empty = True
    string_validator_instance = None
    key_names = None
    refer_key_name = None
    level = None
    messages = dict(
        names='%(keyNames (type list of strings or string) is is required.',
        stores='%(stores (type dict) is is required.',
        missing='%(param)s is required for CheckKeys.',
        type='%(param)s should be of type %(type)s.',
        duplicate='%(value)s is a duplicate entry for key %(key)s.',
        noMatch='Could not find match for path %(path)s.',
        stateMissing='Parameter state is required.',
        emptyValue='Value may not be empty.',
    )

    def __init__(self, **kwargs):
        self.key_names = kwargs.get('key_names', self.key_names)
        self.level = kwargs.get('level', self.level)
        assert self.key_names, self.messages['names']
        if isinstance(self.key_names, list):
            assert self.key_names
            for name in self.key_names:
                assert isinstance(name, string_types)
        else:
            assert isinstance(self.key_names, string_types)
            self.key_names = [self.key_names]
        assert isinstance(self.level, int)

    def validate(self, key_value, **kwargs):
        path, stores = get_value_path_stores(**kwargs)
        if not key_value:
            if not self.not_empty:
                return key_value
                # self.not_empty
            raise ValidationException(self.messages['emptyValue'], key_value)
        if self.string_validator_instance:
            string_value = self.string_validator_instance.validate(key_value)
        else:
            string_value = key_value
        if stores is None:
            return string_value
        target_path = '.'.join(path.split('.')[:-self.level])
        if self.refer_key_name:
            stores.refStore.add_key_ref(self.refer_key_name, key_value, path)
        self.add_value(stores, target_path, string_value, path)
        return string_value

    def add_value(self, stores, target_path, value, path):
        if self.key_names:
            stores.keyStore.add_value(self.key_names, target_path, value, path)


class CheckUniques(CheckKeys):
    not_empty = False
    key_names = None

    def add_value(self, stores, target_path, value, path):
        if self.key_names:
            stores.uniquesStore.add_value(self.key_names, target_path,
                                          value, path)


class KeyName(CheckKeys):
    """

    """
    not_empty = True
    store_name = 'keyStore'
    string_validator_instance = Name()


class UniqueName(CheckUniques):
    """
    A UniqueName is of type Name and may be empty.
    """
    not_empty = False
    string_validator_instance = Name()


class ID(NCName):
    """
    The type ID is used for an attribute that uniquely identifies an element
    in an XML document. An ID value must conform to the rules for an NCName.
    This means that it must start with a letter or underscore, and can only
    contain letters, digits, underscores, hyphens, and periods. ID values
    must be unique within an XML instance, regardless of the attribute's name
    or its element name.
    """
    not_empty = True

    def validate(self, key_value, **kwargs):
        path, stores = get_value_path_stores(**kwargs)
        string_value = super(ID, self).validate(key_value, **kwargs)
        if stores:
            stores.idStore.add_id(string_value, path)
        return key_value


class IDREF(NCName):
    """
    The type ID is used for an attribute that uniquely identifies an element
    in an XML document. An ID value must conform to the rules for an NCName.
    This means that it must start with a letter or underscore, and can only
    contain letters, digits, underscores, hyphens, and periods. ID values
    must be unique within an XML instance, regardless of the attribute's name
    or its element name.
    """
    default_build_value = 'testId0'
    not_empty = True

    def validate(self, key_value, **kwargs):
        path, stores = get_value_path_stores(**kwargs)
        string_value = super(IDREF, self).validate(key_value, **kwargs)
        if stores:
            stores.idrefStore.add_idref(string_value, path)
        return key_value


def match_refs(stores):
    def match_store_refs(key_store, ref_store):
        for ref in ref_store.refs:
            instance_path = key_store.match_ref(ref.key_name, ref.key_value)
            ref_store.set_target(ref.ref_path, instance_path)
            logger.debug('Successfully matched "%s/%s", got: %r'
                         % (ref.key_name, ref.key_value, instance_path))

    match_store_refs(stores.keyStore, stores.refStore)
    match_store_refs(stores.idStore, stores.idrefStore)
