import configparser

import os
import sys

import requests

from bs4 import BeautifulSoup

import json

import io

import re

from tqdm import tqdm

from multiprocessing import Pool

import time # remove later

import urllib.request

import helpers

def recurse_lookahead(bs):
  t = bs.find_all('li');

  if t[0]['class'][0] == "communityLink":
    return 1
  return 0

def recurse_communities(book, dictionary, bs, depth):

  # get all li
  t = bs.find_all('li', recursive=False)

  # er?
  assert len(t) != 0

  # community
  community = False # "collectionListItem"
  if t[0]['class'][0] == "communityLink":
    community = True

  for it in t:
    if community: # communityLink
      c = it.find('strong', recursive=False).find('a')
      # c_name = c.contents[0]
      c_name = c['href'].split('/')[-1]

      # indent print community name
      # print( (' ' * (2 * depth)) + c_name)
      # print( (' ' * (2 * depth)) + c['href'].split('/')[-1] )

      c_bs   = it.find('ul', recursive=False)

      if c_bs != None:
        book[c['href'].split('/')[-1]] = c.contents[0]

        if recurse_lookahead(it):
          dictionary[c_name] = {}
        else:
          dictionary[c_name] = []

        recurse_communities(book, dictionary[c_name], c_bs, depth+1)
    else: # collectionListItem
      c = it.find('a')

      # indent print community name
      # print( (' ' * (2 * depth)) + c.contents[0])
      # print( (' ' * (2 * depth)) + c['href'].split('/')[-1])

      book[c['href'].split('/')[-1]] = c.contents[0]

      dictionary.append(c['href'].split('/')[-1])

def parsecommunities(href):
  ret = requests.get(href)

  if ret.status_code != 200:
    print("cannot access '%s': error code [%d]" % (href, ret.status_code))
    sys.exit()

  bs = BeautifulSoup(ret.content, "html.parser")

  b = {}
  d = {}

  # first li communityLink tag.
  t = bs.find('li', attrs={"class":"communityLink"})
  # find it's parent
  p = t.parent

  recurse_communities(b, d, p, 0);

  # print(b)

  # print(json.dumps(d, indent=2, ensure_ascii=False))

  return b, d

def parsetitles(href):
  ret = requests.get(href)

  if ret.status_code != 200:
    print("cannot access '%s': error code [%d]" % (href, ret.status_code))
    sys.exit()

  bs = BeautifulSoup(ret.content, "html.parser")

  titles = {}

  for table in bs.find_all('table', {'class' : 'miscTable'}):
    data = table.find_all('tr')

    for record in tqdm(data[1:]): # first table is th
      a = record.find('td', attrs={"headers":"t2"}).find('a')
      titles[a['href'].split('/')[-1]] = a.contents[0]

  return titles

def fetchtitles(href):
  ret = requests.get(href)

  if ret.status_code != 200:
    print("cannot access '%s': error code [%d]" % (href, ret.status_code))
    sys.exit()

  bs = BeautifulSoup(ret.content, "html.parser")

  titles = {}

  # get number of titles
  t = bs.find('div', attrs={"class":"browse_range"})
  n = int(re.sub(r"\D", "", t.contents[0].split(' ')[-1])) // 1000 + 1

  # http://10.1.32.112/jspui/browse?type=title&sort_by=2&order=ASC&rpp=1000&offset=0
  for _ in range(0, n):
    print("parsing range %d - %d" % ( (_ + 1) * 1000 - 999, (_ + 1) * 1000))
    titles.update(parsetitles("%s?type=title&sort_by=2&order=ASC&rpp=1000&offset=%d" % (href, (_ * 1000))))

  return titles

def init(config, dspace):

  dsp = helpers.getdsp(config, dspace)
  dspcore = dsp['root'] + dsp['core'];

  # get communities list
  communities, hierarchy = parsecommunities(dspcore + dsp['community'])

  # todo: fixup utf-8 encoding for non-ascii characters encoding
  cfpath = config['common']['path'] + '/communities.json';
  with io.open(cfpath, 'w', encoding='utf8') as f:
    data = json.dumps(communities, ensure_ascii=False)
    f.write(data)

  hfpath = config['common']['path'] + '/hierarchy.json';
  with io.open(hfpath, 'w', encoding='utf8') as f:
    data = json.dumps(hierarchy, ensure_ascii=False)
    f.write(data)

  # fetch all titles
  titles = fetchtitles(dspcore + dsp['browse'])

  tfpath = config['common']['path'] + '/titles.json';
  with io.open(tfpath, 'w', encoding='utf8') as f:
    data = json.dumps(titles, ensure_ascii=False)
    f.write(data)

def handlefetch(params):
  (dsp, handle, title) = params

  print("%s - %s" % (handle, title))

  # fix the handleid
  href = dsp['root'] + dsp['core'] + dsp['handle'] + '/' + handle + '?mode=full'

  # get folder name
  st = str(int(handle) // 1000).zfill(4)

  # directory
  directory = dsp['path'] + os.path.sep + st + os.path.sep + handle

  # check if path exists
  if (os.path.exists(directory)) == False:
    os.makedirs(directory)

  jpath = directory + '/info.json';
  if os.path.exists(jpath):
    with io.open(jpath, 'r', encoding='utf8') as f:
      try:
        data = json.load(f)
      except:
        pass

  ret = requests.get(href)

  if ret.status_code != 200:
    print("cannot access '%s': error code [%d]" % (href, ret.status_code))
    sys.exit()

  bs = BeautifulSoup(ret.content, "html.parser")

  table = bs.find('table', {'class' : 'itemDisplayTable'});
  meta_s = table.find_all('tr')
  data = {}

  for meta in meta_s[1:]:
    label = meta.find('td', {'class' : 'metadataFieldLabel'}).text.encode('utf-8')
    value = meta.find('td', {'class' : 'metadataFieldValue'}).text.encode('utf-8')

    if label in data:
      if (type(data[label]) != 'list'):
        data[label] = [data[label]]
      data[label].append(value)
    else:
      data[label] = value

  urlhref = []
  for td in bs.find_all('td', {'class' : 'standard'}):
    if (td.find('a') is not None):
      url = td.find('a').get('href').encode('utf-8')
      if url in urlhref:
        continue
      urlhref.append(url)

  data['href'] = urlhref

  for key in data.keys():
    if type(key) is not str:
      try:
        data[str(key)] = data[key]
      except:
        try:
          data[repr(key)] = data[key]
        except:
          pass
    del data[key]

  print(data)
  with io.open(jpath, 'w', encoding='utf8') as f:
    d_string = json.dumps(data, ensure_ascii=False)
    f.write(d_string)


  # multi this?
  for xref in urlhref:

    # print(dsp['root'] + xref.decode('utf-8'), directory);

    filename = directory + '/' + xref.decode('utf-8').split('/' + handle + '/')[1]
    if (os.path.exists(os.path.dirname(filename))) == False:
      os.makedirs(os.path.dirname(filename))

    # print (filename);

    urllib.request.urlretrieve(dsp['root'] + xref.decode('utf-8'), filename);



def sync(config, dspace):

  dsp = helpers.getdsp(config, dspace)
  dspcore = dsp['root'] + dsp['core'];

  # load in titles
  tfpath = config['common']['path'] + '/titles.json';
  with io.open(tfpath, 'r', encoding='utf8') as f:
    titles = json.load(f)

  l = len(titles)

  titles_list = [ (dsp, k, titles[k]) for k in titles ];

  pool = Pool(processes=int(config['dspace']['tasks']))

  print("syncing: ")

  with tqdm(total=l) as pbar:
    for i, _ in enumerate(pool.imap_unordered(handlefetch, titles_list), 1):
      if i % 10 == 0:
        pbar.update(10)
