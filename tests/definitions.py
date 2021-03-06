from xmodels import CharField, FieldCollectionField, IntegerField, ModelField, \
    FloatField, Model, DateTimeField, ModelCollectionField, AttributeModel
from xmodels.constraints import ID
from xmodels.fields import EnumField, RequiredAttribute, AttributeField
from xmodels.models import SequenceModel, SequenceElement, Choice

__author__ = 'bernd'

SPIRIT_NS = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"
POWER_VE = "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/POWER-1.0"


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

    class Meta:
        sequence = [
            SequenceElement('name', min_occurs=1), SequenceElement('tags'),
            ]


class VLNVAttributes(AttributeModel):
    vendor = CharField()
    library = CharField()
    name = CharField()
    version = CharField()

    class Meta:
        required_attributes = ['vendor', 'library', 'name', 'version']


class LoadConstraint(AttributeModel):
    id = AttributeField(ID())
    value = CharField()
    count = IntegerField(min=0, default=3)


class Size(AttributeModel):
    id = ID()
    size_int = IntegerField(min=1)
    format = CharField()
    resolve = CharField(default='resolve')

    class Meta:
        value_key = 'size_int'


class HierarchicalSequenceModel(SequenceModel):

    name = CharField()
    id = AttributeField(ID())
    busRef = ModelField(VLNVAttributes)
    count = IntegerField(min=0, default=0)
    child = ModelField(ChildModel)
    timingConstraint = FloatField(min=0, max=100)
    driveConstraint = CharField()
    loadConstraint = ModelField(LoadConstraint)
    marketShare = FloatField(min=0, max=100)

    class Meta:
        sequence = [
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
                    busRef={'@vendor': 'vendor.com',
                            '@library': 'testLibrary',
                            '@name': 'BusName',
                            '@version': 'v1.0'},
                    loadConstraint='medium')

    @staticmethod
    def gen_child_min_dict():
        return {'name': 'child', '@alignment': 'serial'}


name_spaces = {
    SPIRIT_NS: "spirit",
    "http://www.w3.org/2001/XMLSchema-instance": "xsi",
    "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE": "accellera",
    POWER_VE:
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

    class Meta:
        sequence = [
            SequenceElement('left', min_occurs=1),
            SequenceElement('right', min_occurs=1),
        ]
        name_space = SPIRIT_NS


class LogicalWirePowerDef(SequenceModel):
    domain = CharField()
    isolation = CharField()
    idle = CharField()
    reset = CharField()
    vector = ModelField(Vector)

    class Meta:
        sequence = [
            SequenceElement('domain'),
            SequenceElement('isolation'),
            SequenceElement('idle'),
            SequenceElement('reset'),
            SequenceElement('vector'),
        ]
        name_space = POWER_VE


class LogicalWirePowerDefs(SequenceModel):
    logicalWirePowerDef = ModelCollectionField(LogicalWirePowerDef)

    class Meta:
        sequence = [
            SequenceElement('logicalWirePowerDef'),
        ]
        name_space = POWER_VE


class AccelleraLogicalWire(SequenceModel):
    id = AttributeField(ID(name_space=SPIRIT_NS))
    logicalWirePowerDefs = ModelField(LogicalWirePowerDefs)

    class Meta:
        sequence = [
            SequenceElement('logicalWirePowerDefs'),
        ]
        name_space = "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE"


class VendorExtensions(SequenceModel):
    logicalWire = ModelField(AccelleraLogicalWire)

    class Meta:
        sequence = [
            SequenceElement('logicalWire'),
        ]
        name_space = SPIRIT_NS


class Wire(SequenceModel):
    qualifier = CharField()
    onSystem = ModelCollectionField(CharField())
    onMaster = CharField()
    onSlave = CharField()
    defaultValue = CharField()
    requiresDriver = CharField()

    class Meta:
        sequence = [
            SequenceElement('qualifier'),
            SequenceElement('onSystem'),
            SequenceElement('onMaster'),
            SequenceElement('onSlave'),
            Choice(required=False, options=[
                SequenceElement('defaultValue', min_occurs=1),
                SequenceElement('requiresDriver', min_occurs=1)])
        ]
        name_space = SPIRIT_NS


class Port(SequenceModel):
    logicalName = CharField()
    displayName = CharField()
    description = CharField()
    wire = ModelField(Wire, accept_none=True)
    transactional = CharField()
    vendorExtensions = ModelField(VendorExtensions)

    class Meta:
        sequence = [
            SequenceElement('logicalName', min_occurs=1),
            SequenceElement('displayName'),
            SequenceElement('description'),
            Choice(options=[
                SequenceElement('wire', min_occurs=1),
                SequenceElement('transactional', min_occurs=1),
            ]),
            SequenceElement('vendorExtensions'),
        ]
        name_space = SPIRIT_NS


class LibraryRef(AttributeModel):
    vendor = CharField()
    library = CharField()
    name = CharField()
    version = CharField()

    class Meta:
        name_space = SPIRIT_NS


class Ports(SequenceModel):
    port = ModelCollectionField(Port)

    class Meta:
        sequence = [SequenceElement('port', min_occurs=1)]
        name_space = SPIRIT_NS


class AbstractDefinition(SequenceModel):
    vendor = CharField()
    library = CharField()
    name = CharField()
    version = CharField()
    busType = ModelField(LibraryRef)
    extends = ModelField(LibraryRef)
    ports = ModelField(Ports)
    description = CharField()

    class Meta:
        sequence = [
            SequenceElement('vendor', min_occurs=1),
            SequenceElement('library', min_occurs=1),
            SequenceElement('name', min_occurs=1),
            SequenceElement('version', min_occurs=1),
            SequenceElement('busType', min_occurs=1),
            SequenceElement('extends'),
            SequenceElement('ports', min_occurs=1),
            SequenceElement('description'),
        ]
        name_space = SPIRIT_NS
