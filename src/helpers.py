import configparser

import tempfile
import errno

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

def getdsp(config, dspace):
  dsp = dict(dspace.items(config['dspace']['parser'], True))
  dsp.update({'root' : config['dspace']['href']})
  return dsp
