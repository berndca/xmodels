from xmodels import CharField, FieldCollectionField, IntegerField, ModelField, \
    FloatField, Model, DateTimeField, ModelCollectionField, AttributeModel
from xmodels.constraints import ID
from xmodels.fields import EnumField, RequiredAttribute, OptionalAttribute
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
    id = OptionalAttribute(ID())
    value = CharField()
    count = IntegerField(min=0, default=3)


class Size(AttributeModel):
    id = ID()
    size_int = IntegerField(min=1)
    format = CharField()
    resolve = CharField(default='resolve')

    class Meta(AttributeModel.Meta):
        value_key = 'size_int'


class HierarchicalSequenceModel(SequenceModel):

    name = CharField()
    id = OptionalAttribute(ID())
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


class LogicalWirePowerDef(SequenceModel):
    domain = CharField()
    isolation = CharField()
    idle = CharField()
    reset = CharField()
    vector = ModelField(Vector)
    _sequence = [
        SequenceElement('domain'),
        SequenceElement('isolation'),
        SequenceElement('idle'),
        SequenceElement('reset'),
        SequenceElement('vector'),
    ]
    _name_space = "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/POWER-1.0"


class LogicalWirePowerDefs(SequenceModel):
    logicalWirePowerDef = ModelCollectionField(LogicalWirePowerDef)
    _sequence = [
        SequenceElement('logicalWirePowerDef'),
    ]
    _name_space = "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/POWER-1.0"


class AccelleraLogicalWire(SequenceModel):
    id = OptionalAttribute(ID(name_space="http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"))
    logicalWirePowerDefs = ModelField(LogicalWirePowerDefs)
    _sequence = [
        SequenceElement('logicalWirePowerDefs'),
    ]
    _name_space = "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE"


class VendorExtensions(SequenceModel):
    logicalWire = ModelField(AccelleraLogicalWire)
    _sequence = [
        SequenceElement('logicalWire'),
    ]
    _name_space = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


class Wire(SequenceModel):
    qualifier = CharField()
    onSystem = ModelCollectionField(CharField())
    onMaster = CharField()
    onSlave = CharField()
    defaultValue = CharField()
    requiresDriver = CharField()
    _sequence = [
        SequenceElement('qualifier'),
        SequenceElement('onSystem'),
        SequenceElement('onMaster'),
        SequenceElement('onSlave'),
        Choice(required=False, options=[
            SequenceElement('defaultValue', min_occurs=1),
            SequenceElement('requiresDriver', min_occurs=1)])
    ]
    _name_space = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


class Port(SequenceModel):
    logicalName = CharField()
    displayName = CharField()
    description = CharField()
    wire = ModelField(Wire, accept_none=True)
    transactional = CharField()
    vendorExtensions = ModelField(VendorExtensions)
    _sequence = [
        SequenceElement('logicalName', min_occurs=1),
        SequenceElement('displayName'),
        SequenceElement('description'),
        Choice(options=[
            SequenceElement('wire', min_occurs=1),
            SequenceElement('transactional', min_occurs=1),
        ]),
        SequenceElement('vendorExtensions'),
    ]
    _name_space = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


class LibraryRef(AttributeModel):
    vendor = CharField()
    library = CharField()
    name = CharField()
    version = CharField()
    _name_space = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


class Ports(SequenceModel):
    port = ModelCollectionField(Port)
    _sequence = [SequenceElement('port', min_occurs=1)]
    _name_space = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


class AbstractDefinition(SequenceModel):
    vendor = CharField()
    library = CharField()
    name = CharField()
    version = CharField()
    busType = ModelField(LibraryRef)
    extends = ModelField(LibraryRef)
    ports = ModelField(Ports)
    description = CharField()
    _sequence = [
        SequenceElement('vendor', min_occurs=1),
        SequenceElement('library', min_occurs=1),
        SequenceElement('name', min_occurs=1),
        SequenceElement('version', min_occurs=1),
        SequenceElement('busType', min_occurs=1),
        SequenceElement('extends'),
        SequenceElement('ports', min_occurs=1),
        SequenceElement('description'),
    ]
    _name_space = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"

