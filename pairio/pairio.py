import json
import urllib
import hashlib
import os
import pathlib
import pickledb

def _get_default_local_db_fname():
    dirname=str(pathlib.Path.home())+'/.pairio'
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    ret=dirname+'/database'
    if not os.path.exists(ret):
        os.mkdir(ret)
    return ret

_config=dict(
    user='',
    token='',
    users=[],
    admin_token='',
    url=os.getenv('PAIRIO_URL'),
    local_database_path=_get_default_local_db_fname(),
    local=True,
    remote=True
)
if not _config['url']:
    #_config['url']='http://localhost:25340'
    _config['url']='http://pairio.org:8080'
    
def setConfig(*,
              user=None,
              token=None,
              users=None,
              admin_token=None,
              url=None,
              local_database_path=None,
              local=None,
              remote=None
             ):
    if user is not None:
        _config['user']=user
    if token is not None:
        _config['token']=token
    if users is not None:
        _config['users']=users
    if admin_token is not None:
        _config['admin_token']=admin_token
    if url is not None:
        _config['url']=url
    if local_database_path is not None:
        _config['local_database_path']=local_database_path
    if local is not None:
        _config['local']=local
    if remote is not None:
        _config['remote']=remote
            
def get(
    key,
    user=None,
    local=None,
    remote=None,
    users=None
):
    url=_config['url']
    if local is None:
        local=_config['local']
    if remote is None:
        remote=_config['remote']
    if users is None:
        users=_config['users']
        
    key=_filter_key(key)
    if local:
        val=_get_local(key)
        if val:
            return val
        
    if remote:
        if user is not None:
            all_users=[user]
        else:
            all_users=users
            if _config['user']:
                if not _config['user'] in all_users:
                    all_users.append(_config['user'])
        for user0 in all_users:
            path='/get/{}/{}'.format(user0,key)
            url0=url+path
            obj=_http_get_json(url0)
            if obj['success']:
                return obj['value']
    return None
    
def set(
    key,
    value,
    local=None,
    remote=None
):
    user=_config['user']
    url=_config['url']
    if local is None:
        local=_config['local']
    if remote is None:
        remote=_config['remote']
    
    key=_filter_key(key)
    if local:
        _set_local(key,value)
        
    if remote:
        if not user:
            return
        if not url:
            return
        path='/set/{}/{}/{}'.format(user,key,value)
        url0=url+path
        token=_config['token']
        if not token:
            raise Exception('pairio token not set')
        signature=_sha1_of_object({'path':path,'token':token})
        url0=url0+'?signature={}'.format(signature)
        obj=_http_get_json(url0)
        if not obj['success']:
            raise Exception(obj['error'])
        
def _filter_key(key):
    if type(key)==str:
        return key
    if type(key)==dict:
        txt=json.dumps(key, sort_keys=True, separators=(',', ':'))
        return _sha1_of_string(txt)
    raise Exception('Invalid type for key')
        
def _http_get_json(url):
    return json.load(urllib.request.urlopen(url))

def _sha1_of_string(txt):
    hh = hashlib.sha1(txt.encode('utf-8'))
    ret=hh.hexdigest()
    return ret

def _sha1_of_object(obj):
    txt=json.dumps(obj, sort_keys=True, separators=(',', ':'))
    return _sha1_of_string(txt)

def _get_local(key):
    local_database_path=_config['local_database_path']
    if not local_database_path:
        return None
    hashed_key=_sha1_of_string(key)
    path=local_database_path+'/{}.db'.format(hashed_key[0:2])
    db = pickledb.load(path, False)
    doc=db.get(key)
    if doc:
        return doc['value']
    else:
        return None
    
def _set_local(key,val):
    local_database_path=_config['local_database_path']
    if not local_database_path:
        return
    hashed_key=_sha1_of_string(key)
    path=local_database_path+'/{}.db'.format(hashed_key[0:2])
    db = pickledb.load(path, False)
    doc=dict(value=val)
    db.set(key,doc)
    db.dump()
    