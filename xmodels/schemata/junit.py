from .. import SequenceModel, CharField, AttributeModel, \
    ModelCollectionField, FloatField, DateTimeField, IntegerField
from ..fields import Token, NonNegativeInteger, Attribute
from ..models import SequenceElement


class Property(AttributeModel):
    name = Token(minLength=1, required=True)
    value = Attribute(CharField(required=True))


class FailureStatus(AttributeModel):
    message = CharField()
    type = CharField(required=True)


class TestCase(SequenceModel):
    error = FailureStatus()
    failure = FailureStatus()
    name = Attribute(Token(required=True))
    classname = Attribute(Token(required=True))
    time = Attribute(FloatField(required=True))
    _sequence = [
        SequenceElement('error'),
        SequenceElement('failure'),
    ]


class TestSuite(SequenceModel):
    """Contains the results of executing a testsuite
    """
    properties = ModelCollectionField(Property)
    testcase = ModelCollectionField(TestCase)
    system_out = CharField(source='system-out')
    error_out = CharField(source='error-out')
    name = Attribute(CharField(required=True))
    timestamp = Attribute(DateTimeField(required=True,
                              serial_format="%Y-%m-%dT%H:%M:%S"))
    hostname = Attribute(Token(required=True))
    package = Attribute(Token(required=True))
    id = Attribute(NonNegativeInteger(required=True))
    errors = Attribute(IntegerField(required=True))
    failures = Attribute(IntegerField(required=True))
    time = Attribute(FloatField(required=True))
    _sequence = [
        SequenceElement('properties'),
        SequenceElement('testcase'),
        SequenceElement('system_out'),
        SequenceElement('error_out'),
    ]


class TestSuites(SequenceModel):
    testsuite = ModelCollectionField(TestSuite)
    _sequence = [
        SequenceElement('testsuite'),
    ]
