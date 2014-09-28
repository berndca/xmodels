from xmodels import CharField, FieldCollectionField, IntegerField, ModelField, \
    FloatField, Model, DateTimeField, ModelCollectionField, AttributeModel
from xmodels.fields import EnumField, RequiredAttribute
from xmodels.models import SequenceModel, SequenceElement, Choice

__author__ = 'bernd'


class IsASubModel(Model):
    first = IntegerField(default=0)
    dt = DateTimeField()

class HasAModelField(Model):
    first = ModelField(IsASubModel)
    tag = CharField()


class ChildModel(SequenceModel):
    name = CharField()
    id = CharField(source='@id')
    alignment = RequiredAttribute(EnumField(options=['serial', 'parallel']))
    tags = FieldCollectionField(CharField())

    _sequence = [
        SequenceElement('name', min_occurs=1),
        SequenceElement('tags'),
    ]


class VLNVAttributes(AttributeModel):
    vendor = CharField()
    library = CharField()
    name = CharField()
    version = CharField()
    required_attributes = ['vendor', 'library', 'name', 'version']


class LoadConstraint(AttributeModel):
    value = CharField()
    count = IntegerField(min=0, default=3)


class Size(AttributeModel):
    _value_key = 'size_int'
    size_int = IntegerField()
    format = CharField()
    resolve = CharField(default='resolve')


class HierarchicalSequenceModel(SequenceModel):

    name = CharField()
    id = CharField(source='@id')
    busRef = ModelField(VLNVAttributes)
    count = IntegerField(min=0, default=0)
    child = ModelField(ChildModel)
    timingConstraint = FloatField(min=0, max=100)
    driveConstraint = CharField()
    loadConstraint = ModelField(LoadConstraint)
    marketShare = FloatField(min=0, max=100)

    _sequence = [
        SequenceElement('name', min_occurs=1),
        SequenceElement('busRef', min_occurs=1),
        SequenceElement('count'),
        SequenceElement('child'),
        Choice(options=[
            [
                SequenceElement('timingConstraint', min_occurs=1),
                SequenceElement('driveConstraint'),
                SequenceElement('loadConstraint'),
            ],
            [
                SequenceElement('driveConstraint', min_occurs=1),
                SequenceElement('loadConstraint'),
            ],
            SequenceElement('loadConstraint', min_occurs=1),
        ]),
        SequenceElement('marketShare'),
    ]

    @staticmethod
    def gen_parent_min_dict():
        return dict(name='test',
                    busRef={'@vendor':'vendor.com',
                            '@library':'testLibrary',
                            '@name':'BusName',
                            '@version':'v1.0'},
                    loadConstraint='medium')

    @staticmethod
    def gen_child_min_dict():
        return {'name':'child', '@alignment':'serial'}


name_spaces = {
    "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009": "spirit",
    "http://www.w3.org/2001/XMLSchema-instance": "xsi",
    "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE": "accellera",
    "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/POWER-1.0":
        "accellera-power",
}
schema_locations = [
    "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009,"
    "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009/index.xsd",
    "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE",
    "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE-1.0/index.xsd"
    ]


class Vector(SequenceModel):
    left = IntegerField(min=0)
    right = IntegerField(min=0)
    _sequence = [
        SequenceElement('left', min_occurs=1),
        SequenceElement('right', min_occurs=1),
    ]
    _name_space = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


class WirePowerDef(SequenceModel):
    domain = CharField()
    isolation = CharField()
    vector = ModelField(Vector)
    _sequence = [
        Choice(options=[
            SequenceElement('isolation'),
            SequenceElement('vector')
        ]),
        SequenceElement('domain'),
    ]
    _name_space = "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/POWER-1.0"


class WirePowerDefs(SequenceModel):
    wirePowerDef = ModelCollectionField(WirePowerDef)
    _sequence = [
        SequenceElement('wirePowerDef'),
    ]
    _name_space = "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/POWER-1.0"


class WireExtension(SequenceModel):
    wirePowerDefs = ModelField(WirePowerDefs)
    _sequence = [
        SequenceElement('wirePowerDefs'),
    ]
    _name_space = "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE"


class VendorExtensions(SequenceModel):
    wire = ModelField(WireExtension)
    _sequence = [
        SequenceElement('wire'),
    ]
    _name_space = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"

