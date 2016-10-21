import configparser
import os
import sys

import tempfile
import errno

import requests

from bs4 import BeautifulSoup

config = None
dspace = None
_inited = False

# http://stackoverflow.com/a/25868839
def isWritable(path):
  try:
    testfile = tempfile.TemporaryFile(dir = path)
    testfile.close()
  except OSError as e:
    if e.errno == errno.EACCES:  # 13
      return False
    e.filename = path
    raise
  return True

def pathcheck(path):
  if not os.path.exists(path):
    print ("config[common]: path does not exist!")
    return False

  if isWritable(path):
    return True

  return False # uh?

def preconfig():
  global config, dspace

  config = configparser.ConfigParser()
  config.read('config.ini')

  dspace = configparser.ConfigParser()
  dspace.read('dspace.ini')

  assert 'dspace' in config
  assert 'common' in config

  assert 'href' in config['dspace']
  assert 'parser' in config['dspace']

  assert 'path' in config['common']

  # check and fix relative paths
  _ = config['common']['path']
  if _.startswith("./") or _.startswith("../"):
    config['common']['path'] = os.path.abspath(config['common']['path'])

  # check if path is writable
  assert pathcheck(config['common']['path'])

  # set max dspace.tasks to 4 by default
  if config['dspace'].get('tasks') == None:
    config['dspace']['tasks'] = "4"

  # set max common.tasks to 4 by default
  if config['common'].get('tasks') == None:
    config['common']['tasks'] = "4"

def getdsp():
  global config, dspace
  dsp = dict(dspace.items(config['dspace']['parser'], True))
  dsp.update({'root' : config['dspace']['href']})
  return dsp

def test():
  global config, dspace

  if _inited == False:
    preconfig()

  dsp = getdsp()
  dspcore = dsp['root'] + dsp['core'];

  ret = requests.get(dspcore)

  if ret.status_code != 200:
    print("cannot access '%s': error code [%d]" % (dspcore, ret.status_code))
    sys.exit()

  bs = BeautifulSoup(ret.content, "html.parser")

  desc = bs.find(attrs={"name":"Generator"})
  generator = desc['content']

  if not generator.lower().startswith("dspace"):
    print("'%s' does not look like a dspace server" % dspcore)
    sys.exit()

  config['dspace']['version'] = str(generator.split(' ')[1:]) # future?

  print("%s running %s" % (dsp['root'], generator))
