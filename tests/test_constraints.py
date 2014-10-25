import pytest

from xmodels import constraints
from xmodels.fields import ValidationException, Name


__author__ = 'bernd'


def test_init_key_store_add_duplicate_key_name_fail():
    stores = constraints.Stores()
    ks = constraints.InitKeyStore('TestKeys')
    path='root,'
    ks.add_keys(path=path, stores=stores)
    with pytest.raises(ValidationException):
        ks.add_keys(path=path, stores=stores)


def test_init_unique_store_pass():
    stores = constraints.Stores()
    ks = constraints.InitUniqueStore('TestUnique')
    path = 'root.test'
    ks.add_keys(path=path, stores=stores)
    assert stores.keyStore.keys == {'TestUnique:root.test': {}}


def test_init_key_store_pass():
    stores = constraints.Stores()
    ks = constraints.InitKeyStore('TestKey')
    path = 'root.test'
    ks.add_keys(path=path, stores=stores)
    assert stores.keyStore.keys == {'TestKey:root.test': {}}


def test_key_value_count_0_pass():
    stores = constraints.Stores()
    actual = stores.keyStore.key_value_count('dummy', '/')
    assert actual == 0

def test_key_value_count_1_pass():
    stores = constraints.Stores()
    ks = constraints.InitKeyStore('TestKey')
    ks.add_keys(path='root', stores=stores)
    stores.keyStore.add_value('TestKey', 'root', 'TestKey0', '/ads/cgfh')
    actual = stores.keyStore.key_value_count('TestKey', 'root')
    assert actual == 1


def test_key_store_add_value_pass():
    stores = constraints.Stores()
    ks = constraints.InitKeyStore('TestKey')
    ks.add_keys(path='/', stores=stores)
    stores.keyStore.add_value('TestKey', '/', 'key_value', '/ads/cgfh')
    expected = {'TestKey:/': {'key_value': '/ads/cgfh'}}
    assert stores.keyStore.keys == expected


def test_check_ids_add_id_pass():
    stores = constraints.Stores()
    ks = constraints.ID()
    ks.validate('ID42', path='root.id', stores=stores)
    stores.idStore.add_id('key_value', '/ads/cgfh')
    expected = {'ID:/': {'key_value': '/ads/cgfh', 'ID42': 'root.id'}}
    assert stores.idStore.keys == expected


def test_id_count_0_pass():
    stores = constraints.Stores()
    actual = stores.idStore.id_count()
    assert actual == 0


def test_id_count_1_pass():
    stores = constraints.Stores()
    ks = constraints.ID()
    ks.validate('id42', path='root.id', stores=stores)
    actual = stores.idStore.id_count()
    assert actual == 1


def test_init_key_store_two_keys_pass():
    stores = constraints.Stores()
    ks0 = constraints.InitKeyStore('TestKey')
    path0 = 'root.test[0]'
    path1 = 'root.test[1]'
    ks0.add_keys(path=path0, stores=stores)
    ks1 = constraints.InitKeyStore('TestKey')
    ks1.add_keys(path=path1, stores=stores)
    expected = {'TestKey:root.test[0]': {}, 'TestKey:root.test[1]': {}}
    assert stores.keyStore.keys == expected


def test_setup_key_refs_store_pass():
    stores = constraints.Stores()
    ks = constraints.SetupKeyRefsStore('TestKeyRef')
    ks.validate('refName', path='root.test', stores=stores)
    assert (stores.refStore.refs ==
        [constraints.KeyRef(key_name='TestKeyRef', key_value='refName',
            ref_path='root.test')])


def test_setup_key_refs_store_string_validator_pass():
    stores = constraints.Stores()
    ks = constraints.SetupKeyRefsStore('TestKeyRef',
                                       string_validator_instance=Name())
    ks.validate('refName', path='root.test', stores=stores)
    assert (stores.refStore.refs == [constraints.KeyRef(
        key_name='TestKeyRef', key_value='refName',
        ref_path='root.test')])


def test_setup_key_refs_store_value_none_fail():
    stores = constraints.Stores()
    ks = constraints.SetupKeyRefsStore('TestKeyRef')
    with pytest.raises(ValidationException):
        ks.validate(None, path='/', stores=stores)


def test_setup_key_refs_store_value_empty_fail():
    stores = constraints.Stores()
    ks = constraints.SetupKeyRefsStore('TestKeyRef')
    with pytest.raises(ValidationException):
        ks.validate('', path='root', stores=stores)


def test_init_key_store_no_key_fail():
    with pytest.raises(AssertionError):
        constraints.InitKeyStore('')


def test_check_keys_single_key_pass():
    stores = constraints.Stores()
    ks = constraints.InitKeyStore('FieldKey')
    ks.add_keys(path='root.register[0]', stores=stores)
    ck = constraints.CheckKeys(key_names='FieldKey', level=1)
    assert ck.validate('field22', path='root.register[0].field[2]',
                       stores=stores) == 'field22'


def test_check_keys_single_key_no_stores():
    stores = constraints.Stores()
    ks = constraints.InitKeyStore('FieldKey')
    ks.add_keys(path='root.register[0]', stores=stores)
    ck = constraints.CheckKeys(key_names='FieldKey', level=1)
    assert ck.validate('field22', path='root.register[0].field[2]') == 'field22'


def test_check_keys_single_key_stores_type_error():
    stores = constraints.Stores()
    ks = constraints.InitKeyStore('FieldKey')
    ks.add_keys(path='root.register[0]', stores=stores)
    ck = constraints.CheckKeys(key_names='FieldKey', level=1)
    with pytest.raises(TypeError):
        ck.validate('field22', path='', stores=True) == 'field22'


def test_check_uniques_empty_value_pass():
    stores = constraints.Stores()
    ks = constraints.InitUniqueStore('FieldKey')
    path = "root.register[0]"
    ks.add_keys(path=path, stores=stores)
    ck = constraints.CheckUniques(key_names='FieldKey', level=1)
    assert ck.validate(None, path=path+'.field[2]', stores=stores) is None


def test_check_uniques_single_key_pass():
    stores = constraints.Stores()
    ks = constraints.InitUniqueStore('FieldKey')
    path = "root.register[0]"
    ks.add_keys(path=path, stores=stores)
    ck = constraints.CheckUniques(key_names='FieldKey', level=1)
    actual = ck.validate('field2', path=path+'.field2', stores=stores)
    assert actual == 'field2'


def test_check_uniques_duplicate_value_fail():
    stores = constraints.Stores()
    ks = constraints.InitUniqueStore('FieldKey')
    path = "root.register[0]"
    ks.add_keys(path=path, stores=stores)
    ck = constraints.CheckUniques(key_names='FieldKey', level=1)
    ck.validate('field2', path=path+'.field2', stores=stores)
    with pytest.raises(ValidationException):
        ck.validate('field2', path=path+'.field12', stores=stores)


def test_check_keys_duplicate_value_fail():
    stores = constraints.Stores()
    ks = constraints.InitKeyStore('FieldKey')
    path = "root.register[0]"
    ks.add_keys(path=path, stores=stores)
    ck = constraints.CheckKeys(key_names='FieldKey', level=1)
    ck.validate('field2', path=path+'.field2', stores=stores)
    with pytest.raises(ValidationException):
        ck.validate('field2', path=path+'.field12', stores=stores)


def test_check_keys_empty_value_fail():
    stores = constraints.Stores()
    ks = constraints.InitKeyStore('FieldKey')
    path = "/register-0,reg6"
    ks.add_keys(path=path, stores=stores)
    ck = constraints.CheckKeys(key_names='FieldKey', level=1)
    with pytest.raises(ValidationException):
        ck.validate('', path=path+'.field12', stores=stores)


def test_check_keys_three_keys_pass():
    stores = constraints.Stores()
    ks = constraints.InitKeyStore('FieldKey')
    path = "root.register[0]"
    ks.add_keys(path=path, stores=stores)
    ck = constraints.CheckKeys(key_names=['OtherKey', 'FieldKey',
                                          'YetAnotherKey'], level=1)
    expected = {'FieldKey:root.register[0]':
                    {'field2': 'root.register[0].field[2]'}}
    ck.validate('field2', path=path+'.field[2]', stores=stores)
    assert stores.keyStore.keys == expected


def test_check_keys_no_level_fail():
    with pytest.raises(AssertionError):
        constraints.CheckKeys(key_names=['OtherKey', 'FieldKey',
                                         'YetAnotherKey'], level=None)


def test_check_keys_level_type_fail():
    with pytest.raises(AssertionError):
        constraints.CheckKeys(key_names=['OtherKey', 'FieldKey'], level='55')


def test_check_keys_wrong_keynames_type_fail():
    with pytest.raises(AssertionError):
        constraints.CheckKeys(key_names=13, level=2)


def test_check_keys_path_mismatch_fail():
    stores = constraints.Stores()
    ks = constraints.InitKeyStore('FieldKey')
    path = "root.register[0]"
    ks.add_keys(path=path, stores=stores)
    ck = constraints.CheckKeys(key_names='FieldKey', level=1)
    with pytest.raises(ValidationException):
        ck.validate('field2', path='field2', stores=stores)


def test_check_ids_single_pass():
    stores = constraints.Stores()
    ci = constraints.ID()
    ci.validate('ID42', path='field[0].id', stores=stores)
    expected = {'ID:/': {'ID42': 'field[0].id'}}
    assert stores.idStore.keys == expected


def test_set_id_ref_store_pass():
    idr = constraints.IDREFStore()
    idr.add_idref('key_value', 'ref_path')
    expected = [constraints.KeyRef(key_name='ID',
                                   key_value='key_value',
                                   ref_path='ref_path')]
    assert idr.refs == expected


def test_check_idref_single_pass():
    stores = constraints.Stores()
    cr = constraints.IDREF()
    path = 'root.ref.for.field'
    cr.validate('ID42', path=path, stores=stores)
    expected = constraints.KeyRef(key_name='ID', key_value='ID42',
                                  ref_path=path)
    assert stores.idrefStore.refs[0] == expected


def test_set_target_pass():
    rs = constraints.RefStore()
    rs.set_target('ref_path', 'target_path')
    assert rs.targets == {'ref_path': 'target_path'}


def test_set_target_duplicate_target_fail():
    rs = constraints.RefStore()
    rs.set_target('ref_path', 'target_path')
    with pytest.raises(ValidationException):
        rs.set_target('ref_path', 'target_path')


def test_match_ref_nonexistent_key_fail():
    stores = constraints.Stores()
    ks = constraints.InitKeyStore('key_name')
    ks.add_keys(path='root', stores=stores)
    with pytest.raises(ValidationException):
        stores.keyStore.match_ref('wrong_name', 'field22')


def test_match_ref_nonexistent_key_name_fail():
    stores = constraints.Stores()
    ks = constraints.InitKeyStore('key_name')
    ks.add_keys(path='root', stores=stores)
    with pytest.raises(ValidationException):
        stores.keyStore.match_ref('key_name', 'field22')


def test_match_ref_pass():
    stores = constraints.Stores()
    ks = constraints.InitKeyStore('key_name')
    path = 'root.register[0]'
    ks.add_keys(path=path, stores=stores)
    ck = constraints.CheckKeys(key_names=['OtherKey', 'key_name'], level=1)
    ck.validate('field2', path=path+'.field[2]', stores=stores)
    instance_path = stores.keyStore.match_ref('key_name', 'field2')
    assert instance_path == path + '.field[2]'


def test_match_id_pass():
    stores = constraints.Stores()
    path = 'root.register[0]'
    ck = constraints.ID()
    ck.validate('field2', path=path+'.field[2].id', stores=stores)
    instance_path = stores.idStore.match_id('field2')
    assert instance_path == path + '.field[2].id'


def test_match_ref_key_value_not_found_fail():
    stores = constraints.Stores()
    ks = constraints.InitKeyStore('key_name')
    ks.add_keys(path='root', stores=stores)
    with pytest.raises(ValidationException):
        stores.keyStore.match_ref('key_name', 'field220')


def test_match_refs_pass():
    stores = constraints.Stores()
    component_path = 'root.component'
    key_path = component_path + '.memoryMaps.memoryMap[0].name'
    ref_path = component_path + '.busInterfaces.busInterface[0].slave' \
                                '.memoryMapRef.memoryMapRef'
    constraints.InitKeyStore('memoryMapKey').add_keys(path=component_path,
                                                      stores=stores)
    constraints.CheckKeys(key_names='memoryMapKey',
                          level=3).validate('myMemoryMap',
                                            path=key_path,
                                            stores=stores)
    kr = constraints.SetupKeyRefsStore('memoryMapKey')
    kr.validate('myMemoryMap', path=ref_path, stores=stores)
    constraints.match_refs(stores)
    targets = {'root.component.busInterfaces.busInterface[0].slave.'
               'memoryMapRef.memoryMapRef':
                   'root.component.memoryMaps.memoryMap[0].name'}
    assert stores.refStore.targets == targets


def test_match_refs_value_not_found_fail():
    stores = constraints.Stores()
    root_path = 'root.component'
    ref_path = root_path + '.busInterfaces.busInterface[0].slave' \
                           '.memoryMapRef.memoryMapRef'
    constraints.InitKeyStore('memoryMapKey').add_keys(path=root_path,
                                                      stores=stores)
    kr = constraints.SetupKeyRefsStore('memoryMapKey')
    kr.validate('myMemoryMap', path=ref_path, stores=stores)
    with pytest.raises(ValidationException):
        constraints.match_refs(stores)


def test_match_idref_to_id_single_pass():
    stores = constraints.Stores()
    ci = constraints.ID()
    cr = constraints.IDREF()
    id_path = 'root.component.id'
    ref_path = 'root.component.ref.for.id'
    ci.validate('ID42', path=id_path, stores=stores)
    cr.validate('ID42', path=ref_path, stores=stores)
    constraints.match_refs(stores)
    assert stores.idrefStore.targets == {ref_path: id_path}


def test_unique_name_two_keys_pass():
    ks = constraints.InitUniqueStore('Key2')
    stores = constraints.Stores()
    root_path = 'root'
    ks.add_keys(path=root_path, stores=stores)
    u_name = constraints.UniqueName(key_names='Key1 Key2'.split(), level=1)
    key_path = root_path + '.child[1]'
    actual = u_name.validate('child:name', path=key_path, stores=stores)
    assert actual == 'child:name'


def test_key_name_two_keys_pass():
    ks = constraints.InitKeyStore('Key2')
    stores = constraints.Stores()
    root_path = 'root'
    ks.add_keys(path=root_path, stores=stores)
    u_name = constraints.KeyName(key_names='Key1 Key2'.split(), level=1)
    key_path = root_path + '.child[1]'
    actual = u_name.validate('child:name', path=key_path, stores=stores)
    assert actual == 'child:name'


def test_key_sub_class_name_two_keys_pass():
    class TestKeyName(constraints.KeyName):
        key_names = 'Key1 Key2'.split()
        refer_key_name = 'referKey'
        level = 1

    ks = constraints.InitKeyStore('Key2')
    stores = constraints.Stores()
    root_path = 'root'
    ks.add_keys(path=root_path, stores=stores)
    u_name = TestKeyName()
    key_path = root_path + '.child[1]'
    u_name.validate('child:name', path=key_path, stores=stores)
    assert stores.refStore.refs == [constraints.KeyRef(key_name='referKey',
                                                       key_value='child:name',
                                                       ref_path=key_path)]
