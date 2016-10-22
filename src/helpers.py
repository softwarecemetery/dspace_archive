import configparser

import tempfile
import errno

import sys

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
  dsp.update({'path' : config['common']['path']})
  return dsp


# Print iterations progress
def printProgress (iteration, total, prefix = '', suffix = '', decimals = 1, barLength = 100):
  """
  Call in a loop to create terminal progress bar
  @params:
    iteration   - Required  : current iteration (Int)
    total       - Required  : total iterations (Int)
    prefix      - Optional  : prefix string (Str)
    suffix      - Optional  : suffix string (Str)
    decimals    - Optional  : positive number of decimals in percent complete (Int)
    barLength   - Optional  : character length of bar (Int)
  """
  formatStr       = "{0:." + str(decimals) + "f}"
  percents        = formatStr.format(100 * (iteration / float(total)))
  filledLength    = int(round(barLength * iteration / float(total)))
  bar             = '█' * filledLength + '-' * (barLength - filledLength)
  sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix)),
  if iteration == total:
    sys.stdout.write('\n')
  sys.stdout.flush()
