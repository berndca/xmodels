import pytest
from regxact.xmodels.fields import Attribute

from tests.definitions import HierarchicalSequenceModel, Size, \
    VendorExtensions, name_spaces
from regxact.xmodels import CharField, Model, IntegerField, ModelField
from regxact.xmodels.models import SequenceElement, Choice


class TestElementNoAttributes(object):

    @classmethod
    def setup_class(cls):
        """ setup any state specific to the execution of the given class (which
        usually contains tests).
        """
        class Register(Model):
            id = Attribute(CharField(source='@id'))
            name = CharField()
            addressOffset = IntegerField()
            size = ModelField(Size)

        register_dict = {
            'name': 'TestRegister',
            'addressOffset': '0',
            'size': '32'
        }
        cls.instance = Register()
        cls.instance.populate(register_dict)
        cls.instance.to_python()

    def test_address_offset(self):
        assert self.instance.addressOffset == 0

    def test_size(self):
        assert self.instance.size.size_int == 32

    def test_size_format(self):
        assert self.instance.size.format is None

    def test_size_resolve(self):
        assert self.instance.size.resolve == 'resolve'

    def test_extra_element_fail(self):
        with pytest.raises(AttributeError):
            self.instance.extra = 'element'

    def test_extra_attribute_fail(self):
        with pytest.raises(AttributeError):
            setattr(self.instance, '@extra', 'attribute')


class TestElementWithAttributes(object):

    @classmethod
    def setup_class(cls):
        """ setup any state specific to the execution of the given class (which
        usually contains tests).
        """
        class Register(Model):
            id = Attribute(CharField())
            name = CharField()
            addressOffset = IntegerField()
            size = ModelField(Size)

        register_dict = {
            'name': 'TestRegister',
            'addressOffset': '0',
            'size': {
                '#text': '32',
                '@format': 'long',
                }
        }
        cls.instance = Register()
        cls.instance.populate(register_dict)
        cls.instance.to_python()

    def test_size_property(self):
        assert self.instance.size.size_int == 32

    def test_size_format(self):
        assert self.instance.size.format == 'long'

    def test_size_resolve(self):
        assert self.instance.size.resolve == 'resolve'


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
        self.instance.to_python()
        assert self.instance.child.name == 'little one'
        assert self.instance.child.age == 4
        assert self.instance.type == 'my_type'


class TestModelExtra(object):

    @classmethod
    def setup_class(cls):
        class Extras(Model):
            _allow_extra_elements = True
            _allow_extra_attributes = True
            id = Attribute(CharField())
            name = CharField()
            addressOffset = IntegerField()
            size = ModelField(Size)
        cls.cls = Extras
        cls.instance = Extras()

    def test_extra_element_pass(self):
        self.instance.extra = 'element'
        assert self.instance.extra == 'element'

    def test_extra_attribute_pass(self):
        setattr(self.instance, '@extra', 'attribute')
        assert getattr(self.instance, '@extra') == 'attribute'

    def test_extra_to_dict(self):
        d = {'@id': 'ID42', 'name': 'Name', 'addressOffset': 2,
             'extra': 'element', '@extra': 'attribute'}
        inst = self.cls.from_dict(d)
        result = inst.to_dict()
        assert result == d


def test_sequence_element_defaults():
    se = SequenceElement('component')
    assert se.tag == 'component' and se.min_occurs == 0


def test_sequence_element_min_occurs():
    se = SequenceElement('component', min_occurs=1)
    assert se.min_occurs == 1 and se.max_occurs == 0


def test_sequence_element_max_occurs():
    se = SequenceElement('component', min_occurs=2, max_occurs=2)
    assert se.min_occurs == 2 and se.max_occurs == 2


def test_sequence_element_max_assert_fail():
    with pytest.raises(AssertionError):
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
        sequence = self.choice.match_choice_keys({'either_first'})
        assert sequence == ['either_first']

    def test_match_second(self):
        sequence = self.choice.match_choice_keys({'or_second'})
        assert sequence == ['or_second']

    def test_match_third(self):
        sequence = self.choice.match_choice_keys({'or_perhaps_third'})
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
        sequence = self.choice.match_choice_keys({'either_first', 'optional1'})
        assert sequence == ['either_first', 'optional1']

    def test_match_first_error(self):
        errors = []
        self.choice.match_choice_keys({'either_first', 'no_match'},
                                      errors=errors)
        assert len(errors) == 1

    def test_match_second(self):
        sequence = self.choice.match_choice_keys({'optional2', 'or_second'})
        assert sequence == ['optional2', 'or_second']

    def test_match_third(self):
        sequence = self.choice.match_choice_keys({'or_perhaps_third'})
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
        sequence = self.choice.match_choice_keys({'either_first', 'optional1'})
        assert sequence == ['either_first', 'optional1']

    def test_match_first_error(self):
        errors = []
        self.choice.match_choice_keys({'either_first', 'no_match'},
                                      errors=errors)
        assert len(errors) == 1

    def test_match_second(self):
        sequence = self.choice.match_choice_keys({'optional2', 'or_second'})
        assert sequence == ['optional2', 'or_second']

    def test_match_third(self):
        sequence = self.choice.match_choice_keys({'or_perhaps_third'})
        assert sequence == ['or_perhaps_third']


def test_optional_choice():
    choice = Choice(options=[
        SequenceElement('optional1'),
        SequenceElement('optional2'),
    ], required=False)
    assert choice.match_choice_keys(set([])) == []


class TestSequenceModel():

    @classmethod
    def setup_class(cls):
        cls.instance = HierarchicalSequenceModel()

    def test_match_sequence_basic(self):
        sequence = self.instance.match_sequence(['busRef', 'name',
                                                 'driveConstraint',
                                                 'marketShare'])
        assert sequence == ['name', 'busRef', 'driveConstraint',
                            'marketShare'] and not self.instance.fail

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
        d = {u'accellera:wire':
                 {u'accellera-power:wirePowerDefs':
                      {u'accellera-power:wirePowerDef': [
                          {u'accellera-power:domain': u'domain2',
                           u'accellera-power:isolation': u'L'},
                          {u'accellera-power:domain': u'domain3',
                           u'spirit:vector': {u'spirit:left': u'3',
                                              u'spirit:right': u'0'}}]}}}
        cls.inst = VendorExtensions.from_dict(d, name_spaces=name_spaces)
        cls.inst.to_python(name_spaces=name_spaces)

    def test_isolation(self):
        assert self.inst.wire.wirePowerDefs.wirePowerDef[0].isolation == 'L'

    def test_domain0(self):
        assert self.inst.wire.wirePowerDefs.wirePowerDef[0].domain == 'domain2'

    def test_domain1(self):
        assert self.inst.wire.wirePowerDefs.wirePowerDef[1].domain == 'domain3'

    def test_vector_left(self):
        assert self.inst.wire.wirePowerDefs.wirePowerDef[1].vector.left == 3

    def test_vector_right(self):
        assert self.inst.wire.wirePowerDefs.wirePowerDef[1].vector.right == 0

    def test_root_path(self):
        assert self.inst._path == 'VendorExtensions'

    def test_wire_path(self):
        assert self.inst.wire._path == 'VendorExtensions.WireExtension'

    def test_wire_power_defs_path(self):
        assert self.inst.wire.wirePowerDefs._path == \
               'VendorExtensions.WireExtension.WirePowerDefs'

    def test_wire_power_def0_path(self):
        assert self.inst.wire.wirePowerDefs.wirePowerDef[0]._path == \
               'VendorExtensions.WireExtension.WirePowerDefs.WirePowerDef[0]'

    def test_wire_power_def1_path(self):
        assert self.inst.wire.wirePowerDefs.wirePowerDef[1]._path == \
               'VendorExtensions.WireExtension.WirePowerDefs.WirePowerDef[1]'

    def test_vector_path(self):
        assert self.inst.wire.wirePowerDefs.wirePowerDef[1].vector._path == \
               'VendorExtensions.WireExtension.WirePowerDefs.WirePowerDef[1].Vector'

    def test_do_dict(self):
        d = {u'accellera:wire':
                 {u'accellera-power:wirePowerDefs':
                      {u'accellera-power:wirePowerDef': [
                          {u'accellera-power:domain': u'domain2',
                           u'accellera-power:isolation': u'L'},
                          {u'accellera-power:domain': u'domain3',
                           u'spirit:vector': {u'spirit:left': 3,
                                              u'spirit:right': 0}}]}}}
        assert self.inst.to_dict(name_spaces=name_spaces) == d