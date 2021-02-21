
import homeassistant.loader as loader
from requests import get
from requests import post
import xmltodict
import json
import logging
import datetime
import time

import voluptuous as vol

from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.core import callback


_LOGGER = logging.getLogger(__name__)

DOMAIN = 'proof'
ENTITY_ID_FORMAT = DOMAIN + '.{}'
GOOGLE_MAP_FORMAT = "https://www.google.com/maps/search/?api=1&query={},{}"
PROOF_STATE_API = "https://sm3.2proof.co.il/api/device?_dc=3313498240594&page=1&start=0&limit=60&access_token={}"
TOKEN_URL = "https://api.2proof.co.il/oauth/token?grant_type=password&client_id=app&client_secret=api1234&scope=SCOPE_READ&username={}&password={}"
TAKE_PIC_URL = "https://sm3.2proof.co.il/api/device/takepicv1?access_token={}"
GET_PIC_URL = 'https://sm3.2proof.co.il/api/device/geturlv2?access_token={}'
REQUIREMENTS = ['xml2dict==0.2.2']

def login(username, password):
    token_url = TOKEN_URL.format(username, password)
    # access_token = conf.get('access_token', get(token).json()['access_token'])
    res = get(token_url).json()
    # _LOGGER.error(str(res))
    return res
def setup(hass, config):

    component = EntityComponent(_LOGGER, DOMAIN, hass)
    
    entities = []
    
    for ent_id, conf in config[DOMAIN].items():
        if not config:
            config = {}

        username = conf.get('username', '')
        password = conf.get('password', '')
        res = login(username, password)
        access_token = res['access_token']
        expires_in = res['expires_in']
        expiration_time = time.mktime(time.gmtime()) + expires_in
        name = conf.get('name', "")
        update_interval = conf.get('update_interval', 120)
        proof_data = get_proof_data(access_token)
        proof_obj = Proof(access_token, update_interval, ent_id, name, proof_data)
        proof_obj._expiration_time = expiration_time
        proof_obj._username = username
        proof_obj._password = password
        entities.append(proof_obj)
        # _LOGGER.error(str(proof_obj))
        
        def handle_pic(call):
            if ent_id == call.data['entity_id']:
                # _LOGGER.error(name)
                url = TAKE_PIC_URL.format(access_token)
                post(url, 'did={}&cmd=2&vib=false&picsize=640x480'.format(proof_data['status']['did']))
                get_pic_url = GET_PIC_URL.format(access_token)
                pic_url = ''
                i = 1
                while i < 10:
                  i += 1
                  res = post(get_pic_url, data = 'did={}&type=pic'.format(proof_data['status']['did']), headers = {'accept' : 'application/json', 'content-type' : 'application/x-www-form-urlencoded; charset=UTF-8'})
                  print(res)
                  print(res.text)
                  if res.text.find("http") > -1:
                     pic_url = res.text
                     break
                  time.sleep(2.0)
                # _LOGGER.error(pic_url)
                proof_obj._last_pic = pic_url
    
        
        hass.services.register(DOMAIN, 'download_pic', handle_pic)
        hass.services.call(DOMAIN, 'download_pic', {'entity_id': ent_id})
        
    component.add_entities(entities)
    
    return True
    
def get_proof_data(access_token):
    url = PROOF_STATE_API.format(access_token)
    # _LOGGER.error('####################################')
    # _LOGGER.error(url)
    response = get(url)
    
    dic = response.json()
    try:
      return dic['items'][0]
    except:
      _LOGGER.error("exception getting proof data: " + str(response))
      return None

class Proof(Entity):
    def __init__(self, access_token, update_interval, ent_id, name, proof_data):
        self.entity_id = ENTITY_ID_FORMAT.format(ent_id.replace('-', '').replace(' ', '_').replace('.', '_'))
        self._access_token = access_token
        self._update_interval = update_interval
        self._name = name
        
        self._updated_at = time.mktime(time.gmtime())
        self._proof_data = proof_data
        self._last_pic = ''

        
    @property
    def should_poll(self):
        return True

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return str(self._proof_data['status']['gps']['lat']) + ',' + str(self._proof_data['status']['gps']['lng'])
        
    def update(self):
        if self._expiration_time - 3600 < time.mktime(time.gmtime()):
            login_res = login(self._username, self._password)
            self._access_token = login_res['access_token']
            expires_in = login_res['expires_in']
            self._expiration_time = time.mktime(time.gmtime()) + expires_in
        if self._updated_at + self._update_interval > time.mktime(time.gmtime()):
            return
        self._updated_at = time.mktime(time.gmtime())
        data = get_proof_data(self._access_token)
        if data == None:
            _LOGGER.error('Going yo login again....')
            
            res = login(self._username, self._password)
            self._access_token = res['access_token']
            expires_in = res['expires_in']
            self._expiration_time = time.mktime(time.gmtime()) + expires_in
            self.update()
        else:
            self._proof_data = data

        
    @property    
    def state_attributes(self):
        return {
            "latitude":self._proof_data['status']['gps']['lat'],
            "longitude":self._proof_data['status']['gps']['lng'],
            "altitude": self._proof_data['status']['gps']['alt'],
            "imei" : self._proof_data['status']['did'],
            "google_map" : GOOGLE_MAP_FORMAT.format(self._proof_data['status']['gps']['lat'], self._proof_data['status']['gps']['lng']),
            # "custom_ui_state_card" : "state-card-proof",
            "update_interval" : self._update_interval,
            "source_type" : "gps",
            "speed": self._proof_data['status']['gps']['speed'],
            "last_pic" : self._last_pic,
            "api_access_token" : self._access_token,
            "token_expiration_time" : self._expiration_time
            
            
        }
        
