from .. import SequenceModel, CharField, AttributeModel, \
    ModelCollectionField, FloatField, DateTimeField, IntegerField
from ..fields import Token, NonNegativeInteger, RequiredAttribute, \
    OptionalAttribute
from ..models import SequenceElement


class Property(AttributeModel):
    name = Token(minLength=1, required=True)
    value = RequiredAttribute(CharField())


class FailureStatus(AttributeModel):
    message = CharField()
    type = CharField(required=True)


class TestCase(SequenceModel):
    error = FailureStatus()
    failure = FailureStatus()
    name = RequiredAttribute(Token())
    classname = RequiredAttribute(Token())
    time = RequiredAttribute(FloatField())
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
    name = RequiredAttribute(CharField())
    timestamp = OptionalAttribute(DateTimeField(
        required=True, serial_format="%Y-%m-%dT%H:%M:%S"))
    hostname = RequiredAttribute(Token())
    package = RequiredAttribute(Token())
    id = RequiredAttribute(NonNegativeInteger())
    errors = RequiredAttribute(IntegerField())
    failures = RequiredAttribute(IntegerField())
    time = RequiredAttribute(FloatField())
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
