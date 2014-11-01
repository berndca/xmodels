import json
import os

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
import datetime

import pytest

from xmodels.constraints import ID, InitStores
from xmodels.fields import AttributeField, DateTimeField, FloatField, Name, \
    RequiredAttribute
from tests.definitions import HierarchicalSequenceModel, Size, \
    VendorExtensions, name_spaces, Port, AbstractDefinition, LibraryRef
from xmodels import CharField, Model, IntegerField, ModelField, SequenceModel
from xmodels.models import SequenceElement, Choice
from xmodels.utils import MsgRecord


class TestElementNoAttributes(object):
    @classmethod
    def setup_class(cls):
        """ setup any state specific to the execution of the given class (which
        usually contains tests).
        """
        class Register(SequenceModel):
            id = AttributeField(ID())
            name = CharField()
            addressOffset = IntegerField()
            size = ModelField(Size)

            class Meta:
                sequence = [
                    SequenceElement('name', min_occurs=1),
                    SequenceElement('addressOffset', min_occurs=1),
                    SequenceElement('size', min_occurs=1),
                ]

        cls.register_dict = {
            'name': 'TestRegister',
            '@id': 'ID42',
            'addressOffset': '0',
            'size': '32'
        }
        cls.cls = Register
        cls.instance = Register.from_dict(cls.register_dict)

    def test_address_offset(self):
        assert self.instance.addressOffset == 0

    def test_size(self):
        assert self.instance.size.size_int == 32

    def test_size_format(self):
        assert self.instance.size.format is None

    def test_size_resolve(self):
        assert self.instance.size.resolve == 'resolve'

    def test_size_resolve_fail(self):
        self.instance.size.resolve = True
        errors = []
        self.instance.validate(errors=errors)
        assert errors == [MsgRecord(path='Register.Size', field='resolve',
                                        msg='Expecting a string')]

    def test_extra_element_fail(self):
        with pytest.raises(AttributeError):
            self.instance.extra = 'element'

    def test_extra_attribute_fail(self):
        with pytest.raises(AttributeError):
            setattr(self.instance, '@extra', 'attribute')

    def test_extra_element_from_dict_fail(self):
        reg_dict = dict((key, value)
                        for (key, value) in self.register_dict.items())
        reg_dict['extra_element'] = 'causing an error'
        errors = []
        self.cls.from_dict(reg_dict, errors=errors)
        assert errors == [MsgRecord(
            path='Register', field='_extra',
            msg='Found extra element fields: extra_element')]


class TestElementWithAttributes(object):
    @classmethod
    def setup_class(cls):
        """ setup any state specific to the execution of the given class (which
        usually contains tests).
        """
        class Register(Model):
            id = AttributeField(ID())
            name = CharField()
            addressOffset = IntegerField()
            size = ModelField(Size)

        register_dict = {
            'name': 'TestRegister',
            'addressOffset': '0',
            'size': {
                '#text': '32',
                '@id': 'ID33',
                '@format': 'long',
            }
        }
        cls.instance = Register()
        cls.instance.populate(register_dict)
        cls.instance.validate()

    def test_size_property(self):
        assert self.instance.size.size_int == 32

    def test_size_format(self):
        assert self.instance.size.format == 'long'

    def test_size_resolve(self):
        assert self.instance.size.resolve == 'resolve'

    def test_str(self):
        expected = "Register(Model): 'addressOffset': IntegerField, " \
                   "'id': AttributeField, 'name': CharField, " \
                   "'size': ModelField: Size"
        assert str(self.instance) == expected
        assert str(self.instance) == repr(self.instance)


class TestHierarchicalClass(object):
    @classmethod
    def setup_class(cls):
        class ChildModel(Model):
            name = CharField()
            age = IntegerField()

        class ParentModel(Model):
            type = CharField()
            child = ModelField(ChildModel)

        cls.instance = ParentModel()

    def test_from_dict(self):
        d = dict(type='my_type', child=dict(name='little one', age='4'))
        self.instance.populate(d)
        self.instance.validate()
        assert self.instance.child.name == 'little one'
        assert self.instance.child.age == 4
        assert self.instance.type == 'my_type'


class TestModelExtra(object):
    @classmethod
    def setup_class(cls):
        class Extras(Model):
            id = AttributeField(CharField())
            name = CharField()
            addressOffset = IntegerField()
            size = ModelField(Size)

            class Meta:
                allow_extra_elements = True
                allow_extra_attributes = True

        cls.cls = Extras
        cls.instance = Extras()

    def test_extra_element_pass(self):
        self.instance.extra = 'element'
        assert self.instance.extra == 'element'

    def test_extra_attribute_pass(self):
        setattr(self.instance, '@extra', 'attribute')
        assert getattr(self.instance, '@extra') == 'attribute'

    def test_extra_serialize(self):
        d = {'@id': 'ID42', 'name': 'Name', 'addressOffset': 2,
             'extra': 'element', '@extra': 'attribute'}
        inst = self.cls.from_dict(d)
        result = inst.serialize()
        assert result == d


def test_sequence_element_defaults():
    se = SequenceElement('component')
    assert se.tag == 'component' and se.min_occurs == 0


def test_sequence_element_str():
    se = SequenceElement('component')
    assert str(se) == 'SequenceElement: component (0, 0)'


def test_sequence_element_min_occurs():
    se = SequenceElement('component', min_occurs=1)
    assert se.min_occurs == 1 and se.max_occurs == 0


def test_sequence_element_max_occurs():
    se = SequenceElement('component', min_occurs=2, max_occurs=2)
    assert se.min_occurs == 2 and se.max_occurs == 2


def test_sequence_element_max_assert_fail():
    with pytest.raises(ValueError):
        SequenceElement('component', min_occurs=12, max_occurs=2)


class TestChoiceScalarOptions():
    @classmethod
    def setup_class(cls):
        cls.choice = Choice(options=[
            SequenceElement('either_first', min_occurs=1),
            SequenceElement('or_second', min_occurs=1),
            SequenceElement('or_perhaps_third', min_occurs=1),
        ])

    def test_match_first(self):
        sequence = self.choice.match_choice_keys(set(['either_first']))
        assert sequence == ['either_first']

    def test_match_second(self):
        sequence = self.choice.match_choice_keys(set(['or_second']))
        assert sequence == ['or_second']

    def test_match_third(self):
        sequence = self.choice.match_choice_keys(set(['or_perhaps_third']))
        assert sequence == ['or_perhaps_third']


class TestChoiceListOptions():
    @classmethod
    def setup_class(cls):
        option1 = [
            SequenceElement('either_first', min_occurs=1),
            SequenceElement('optional0'),
            SequenceElement('optional1'),
        ]
        option2 = [
            SequenceElement('optional2'),
            SequenceElement('or_second', min_occurs=1),
        ]
        option3 = [
            SequenceElement('or_perhaps_third', min_occurs=1),
            SequenceElement('optional3'),
        ]
        cls.choice = Choice(options=[
            option1,
            option2,
            option3,
        ])

    def test_match_first(self):
        sequence = self.choice.match_choice_keys(set(['either_first',
                                                      'optional1']))
        assert sequence == ['either_first', 'optional1']

    def test_match_first_error(self):
        errors = []
        self.choice.match_choice_keys(set(['either_first', 'no_match']),
                                      errors=errors)
        assert len(errors) == 1

    def test_match_second(self):
        sequence = self.choice.match_choice_keys(set(['optional2',
                                                      'or_second']))
        assert sequence == ['optional2', 'or_second']

    def test_match_third(self):
        sequence = self.choice.match_choice_keys(set(['or_perhaps_third']))
        assert sequence == ['or_perhaps_third']

    def test_str(self):
        expected = 'Choice: ((either_first, optional0, optional1) | ' \
                   '(optional2, or_second) | (or_perhaps_third, optional3))'
        assert str(self.choice) == expected


class TestChoiceMixedOptions():
    @classmethod
    def setup_class(cls):
        option1 = [
            SequenceElement('either_first', min_occurs=1),
            SequenceElement('optional0'),
            SequenceElement('optional1'),
        ]
        option2 = [
            SequenceElement('optional2'),
            SequenceElement('or_second', min_occurs=1),
        ]
        cls.choice = Choice(options=[
            option1,
            option2,
            SequenceElement('or_perhaps_third', min_occurs=1),
        ])

    def test_match_first(self):
        sequence = self.choice.match_choice_keys(
            set(['either_first', 'optional1'])
        )
        assert sequence == ['either_first', 'optional1']

    def test_match_first_error(self):
        errors = []
        self.choice.match_choice_keys(set(['either_first', 'no_match']),
                                      errors=errors)
        assert len(errors) == 1

    def test_match_second(self):
        sequence = self.choice.match_choice_keys(set(['optional2',
                                                      'or_second']))
        assert sequence == ['optional2', 'or_second']

    def test_match_third(self):
        sequence = self.choice.match_choice_keys(set(['or_perhaps_third']))
        assert sequence == ['or_perhaps_third']


def test_optional_choice():
    choice = Choice(options=[
        SequenceElement('optional1', min_occurs=1),
        SequenceElement('optional2', min_occurs=1),
    ], required=False)
    assert choice.match_choice_keys(set([])) == []
    assert True


class TestSequenceModel():
    @classmethod
    def setup_class(cls):
        cls.instance = HierarchicalSequenceModel()

    def test_match_sequence_basic(self):
        sequence = self.instance.match_sequence(['busRef', 'name',
                                                 'driveConstraint',
                                                 'marketShare'])
        assert sequence == ['name', 'busRef', 'driveConstraint',
                            'marketShare'] and not self.instance._errors

    def test_match_sequence_fail(self):
        errors = []
        self.instance.match_sequence(['busRef', 'name', 'marketShare'],
                                     errors=errors)
        assert len(errors) == 1

    def test_match_sequence_extra_fail(self):
        errors = []
        self.instance.match_sequence(['busRef', 'name', 'extra_field'],
                                     errors=errors)
        assert len(errors) == 2


class TestToDictMin():
    @classmethod
    def setup_class(cls):
        child = HierarchicalSequenceModel.gen_child_min_dict()
        parent = HierarchicalSequenceModel.gen_parent_min_dict()
        parent['child'] = child
        cls.instance = HierarchicalSequenceModel.from_dict(parent)

    def test_pass(self):
        assert not self.instance.fail

    def test_field_load_constraints_value(self):
        assert self.instance.loadConstraint.value == 'medium'

    def test_field_load_constraints_count(self):
        assert self.instance.loadConstraint.count == 3


class TestNameSpacePrefix():
    @classmethod
    def setup_class(cls):
        d = {'accellera:logicalWire': {
            '@spirit:id': 'ID42',
            'accellera-power:logicalWirePowerDefs':
                {'accellera-power:logicalWirePowerDef': [
                    {'accellera-power:domain': 'domain2',
                     'accellera-power:isolation': 'L'},
                    {'accellera-power:domain': 'domain3',
                     'spirit:vector':
                         {'spirit:left': '3',
                          'spirit:right': '0'}}]}}}
        cls.raw_data = d
        cls.inst = VendorExtensions.from_dict(d, name_spaces=name_spaces)
        lwpd = cls.inst.logicalWire.logicalWirePowerDefs.logicalWirePowerDef
        cls.lwpDefs = [lwpDef for lwpDef in lwpd]
        cls.LD = 'VendorExtensions.AccelleraLogicalWire.LogicalWirePowerDefs'

    def test_isolation(self):
        assert self.lwpDefs[0].isolation == 'L'

    def test_domain0(self):
        assert self.lwpDefs[0].domain == 'domain2'

    def test_domain1(self):
        assert self.lwpDefs[1].domain == 'domain3'

    def test_vector_left(self):
        assert self.lwpDefs[1].vector.left == 3

    def test_vector_right(self):
        assert self.lwpDefs[1].vector.right == 0

    def test_root_path(self):
        assert self.inst._path == 'VendorExtensions'

    def test_wire_path(self):
        expected = 'VendorExtensions.AccelleraLogicalWire'
        assert self.inst.logicalWire._path == expected

    def test_wire_power_defs_path(self):
        assert self.inst.logicalWire.logicalWirePowerDefs._path == self.LD

    def test_wire_power_def0_path(self):
        assert self.lwpDefs[0]._path == self.LD + '.LogicalWirePowerDef[0]'

    def test_wire_power_def1_path(self):
        assert self.lwpDefs[1]._path == self.LD + '.LogicalWirePowerDef[1]'

    def test_vector_path(self):
        expected = self.LD + '.LogicalWirePowerDef[1].Vector'
        assert self.lwpDefs[1].vector._path == expected

    def test_do_dict(self):
        d = {'accellera:logicalWire': {
            '@spirit:id': 'ID42',
            'accellera-power:logicalWirePowerDefs':
                {'accellera-power:logicalWirePowerDef': [
                    {'accellera-power:domain': 'domain2',
                     'accellera-power:isolation': 'L'},
                    {'accellera-power:domain': 'domain3',
                     'spirit:vector':
                         {'spirit:left': 3,
                          'spirit:right': 0}}]}}}
        assert self.inst.serialize(name_spaces=name_spaces) == d


class TestSerialization(object):
    @classmethod
    def setup_class(cls):
        class Basic(Model):
            created = DateTimeField()
            probability = RequiredAttribute(FloatField())

        cls.basic_dict = {
            'created': '2014-08-24T16:57:00',
            '@probability': '0.21',
        }
        cls.cls = Basic
        cls.instance = Basic.from_dict(cls.basic_dict)
        cls.instance.deserialize()

    def test_float_pass(self):
        assert self.instance.probability == 0.21

    def test_date_pass(self):
        assert self.instance.created == datetime.datetime(2014, 8, 24, 16, 57)

    def test_deserialize_fail(self):
        errors = []
        inst = self.cls.from_dict(self.basic_dict)
        inst.probability = 'not a number'
        inst.deserialize(errors=errors)
        assert errors == [MsgRecord(path='Basic', field='probability',
                                        msg='Could not convert to float:')]

    def test_serialize_pass(self):
        result = self.instance.serialize()
        assert result == self.basic_dict

    def test_serialize_multiple_pass(self):
        self.instance.serialize()
        result = self.instance.serialize()
        assert result == self.basic_dict

    def test_serialize_fail(self):
        inst = self.cls.from_dict(self.basic_dict)
        inst.deserialize()
        inst._fields['probability'].serial_format = '{'
        errors = []
        inst.serialize(errors=errors)
        assert errors == [MsgRecord(
            path='Basic', field='probability',
            msg='Could not convert float to string with format {.')]


class TestSequenceModels():
    @classmethod
    def setup_class(cls):
        class InitSystemGroupKey(InitStores):
            key_names = ['systemGroupNameKey']

        class Sequence0(SequenceModel):
            id = AttributeField(ID())
            name = Name()
            size = IntegerField(min=1)

            class Meta:
                initial = InitSystemGroupKey()
                sequence = [
                    SequenceElement('name', min_occurs=1),
                    SequenceElement('size', min_occurs=1),
                ]

        cls.cls = Sequence0

    def test_sequence_pass(self):
        seq_data = dict(name='test', size='10')
        inst = self.cls.from_dict(seq_data)
        assert inst.size == 10

    def test_match_sequence_fail(self):
        seq_data = dict(name='test')
        errors = []
        self.cls.from_dict(seq_data, errors=errors)
        assert errors == [MsgRecord(path='Sequence0', field='size',
                                        msg='Missing required key: size ')]


def test_empty_modelfield():
    d = dict(logicalName='lname', wire=None)
    inst = Port.from_dict(d)
    serialized = inst.serialize()
    assert serialized == d


class TestAttributeModel():
    @classmethod
    def setup_class(cls):
        cls.d = {
            '@spirit:library': 'test',
            '@spirit:name': 'busdef',
            '@spirit:vendor': 'Mds',
            '@spirit:version': '1.0'
        }

    def test_from_xml(self):
        inst = LibraryRef()
        inst.populate(self.d, name_spaces=name_spaces)
        errors = []
        inst.validate(errors=errors)
        assert inst.serialize() == {
            '@library': 'test',
            '@name': 'busdef',
            '@vendor': 'Mds',
            '@version': '1.0'}


class TestSerialize():
    @classmethod
    def setup_class(cls):
        class Basic(SequenceModel):
            zzz = IntegerField()
            a = IntegerField()

            class Meta:
                sequence = [
                    SequenceElement('zzz'),
                    SequenceElement('a'),
                ]

        cls.inst = Basic.from_dict(dict(zzz=22, a=999))

    def test_serialize_to_dict(self):
        result = self.inst.serialize().items()
        assert not isinstance(result, OrderedDict)

    def test_serialize_to_ordered_dict(self):
        kwargs = {'dict_constructor': OrderedDict}
        serialized_items = list(self.inst.serialize(**kwargs).items())
        assert serialized_items == [('zzz', 22), ('a', 999)]


class TestXMLDict():
    @classmethod
    def setup_class(cls):
        tests_path = os.path.split(os.path.abspath(__file__))[0]
        fn = os.path.join(tests_path, 'abstractDefinition.json')
        with open(fn) as ad_jfile:
            d = json.load(ad_jfile)
        cls.in_dict = d

    def test_from_xml(self):
        inst = AbstractDefinition()
        inst.from_xml(self.in_dict, name_spaces=name_spaces)
        errors = []
        inst.validate(errors=errors)
        lwp = OrderedDict([('domain', 'domain4'),
                           ('isolation', 'Z'),
                           ('idle', '1'),
                           ('reset', '0')])
        ve_data = OrderedDict([('logicalWire', OrderedDict([
            ('logicalWirePowerDefs',
             OrderedDict([('logicalWirePowerDef', [lwp])]))]))])
        expected = OrderedDict([
            ('vendor', 'Mds'),
            ('library', 'test'),
            ('name', 'absdef'),
            ('version', '1.0'),
            ('busType',
             OrderedDict([
                 ('@vendor', 'Mds'),
                 ('@library', 'test'),
                 ('@name', 'busdef'),
                 ('@version', '1.0')])),
            ('ports', OrderedDict([
                ('port', [OrderedDict([('logicalName', 'lo1'),
                                       ('wire', None), ]),
                          OrderedDict([('logicalName', 'lo2'), ('wire', None),
                                       ('vendorExtensions', ve_data)])])
            ]))
        ])
        assert inst.serialize() == expected
