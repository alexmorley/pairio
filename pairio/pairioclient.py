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

class PairioClient():
    def __init__(self):
        self._config=dict(
            user=os.getenv('PAIRIO_USER',''),
            token=os.getenv('PAIRIO_TOKEN',''),
            users=[],
            admin_token=os.getenv('PAIRIO_ADMIN_TOKEN',''),
            url=os.getenv('PAIRIO_URL','http://pairio.org:8080'),
            local_database_path=_get_default_local_db_fname(),
            local=True,
            remote=True
        )
    
    def setConfig(self,*,
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
            self._config['user']=user
        if token is not None:
            self._config['token']=token
        if users is not None:
            self._config['users']=users
        if admin_token is not None:
            self._config['admin_token']=admin_token
        if url is not None:
            self._config['url']=url
        if local_database_path is not None:
            self._config['local_database_path']=local_database_path
        if local is not None:
            self._config['local']=local
        if remote is not None:
            self._config['remote']=remote
        
    def get(
        self,
        key,
        user=None,
        local=None,
        remote=None,
        users=None
    ):
        url=self._config['url']
        if local is None:
            local=self._config['local']
        if remote is None:
            remote=self._config['remote']
        if users is None:
            users=self._config['users']
            
        key=_filter_key(key)
        if local and (not user):
            val=self._get_local(key)
            if val:
                return val
            
        if remote:
            if user is not None:
                all_users=[user]
            else:
                all_users=users
                if self._config['user']:
                    if not self._config['user'] in all_users:
                        all_users.append(self._config['user'])
            for user0 in all_users:
                path='/get/{}/{}'.format(user0,key)
                url0=url+path
                obj=_http_get_json(url0)
                if obj['success']:
                    return obj['value']
        return None

    def set(
        self,
        key,
        value,
        local=None,
        remote=None
    ):
        user=self._config['user']
        url=self._config['url']
        if local is None:
            local=self._config['local']
        if remote is None:
            remote=self._config['remote']
        
        key=_filter_key(key)
        if local:
            self._set_local(key,value)
            
        if remote:
            if not user:
                return
            if not url:
                return
            path='/set/{}/{}/{}'.format(user,key,value)
            url0=url+path
            token=self._config['token']
            if not token:
                raise Exception('pairio token not set')
            signature=_sha1_of_object({'path':path,'token':token})
            url0=url0+'?signature={}'.format(signature)
            obj=_http_get_json(url0)
            if not obj['success']:
                raise Exception(obj['error'])

    def _get_local(self,key):
        local_database_path=self._config['local_database_path']
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
        
    def _set_local(self,key,val):
        local_database_path=self._config['local_database_path']
        if not local_database_path:
            return
        hashed_key=_sha1_of_string(key)
        path=local_database_path+'/{}.db'.format(hashed_key[0:2])
        db = pickledb.load(path, False)
        doc=dict(value=val)
        db.set(key,doc)
        db.dump()
        
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


# The global module client
client=PairioClient()
