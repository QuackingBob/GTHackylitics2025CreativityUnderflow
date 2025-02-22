#!/usr/bin/env python3
from bs4 import BeautifulSoup
import requests
import re
import sys
import os
import http.cookiejar
import json
import urllib.request, urllib.error, urllib.parse

def get_soup(url,header):
    #return BeautifulSoup(urllib2.urlopen(urllib2.Request(url,headers=header)),
    # 'html.parser')
    return BeautifulSoup(urllib.request.urlopen(
        urllib.request.Request(url,headers=header)),
        'html.parser')

if len(sys.argv) != 2:
    print("Usage: python scraper.py [description]")
    sys.exit(0)
    
query = sys.argv[1]
query= query.split()
query='+'.join(query)
url="http://www.bing.com/images/search?q=" + query + "&FORM=HDRSC2"

#add the directory for your image here
DIR="Pictures"
header={'User-Agent':"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"}
soup = get_soup(url,header)

ActualImages=[]# contains the link for Large original images, type of  image
for a in soup.find_all("a", {"class": "iusc"}):
    # First try the "m" attribute
    m_data = a.get("m")
    if m_data:
        try:
            m = json.loads(m_data)
        except json.JSONDecodeError as e:
            print("Error decoding 'm':", e)
            continue
        turl = m.get("turl")
        murl = m.get("murl")
    else:
        # Fallback to "mad" attribute if "m" is missing
        mad_data = a.get("mad")
        if mad_data:
            try:
                mad = json.loads(mad_data)
            except json.JSONDecodeError as e:
                print("Error decoding 'mad':", e)
                continue
            turl = mad.get("turl")
            murl = None  # Or handle accordingly if "murl" is only available in "m"
        else:
            print("No 'm' or 'mad' attribute found in this element.")
            continue

    if not (turl and murl):
        print("Missing URL information; skipping this image.")
        continue

    image_name = urllib.parse.urlsplit(murl).path.split("/")[-1]
    print(image_name)
    ActualImages.append((image_name, turl, murl))


print("there are total" , len(ActualImages),"images")

if not os.path.exists(DIR):
    os.mkdir(DIR)

DIR = os.path.join(DIR, query.split()[0])
if not os.path.exists(DIR):
    os.mkdir(DIR)

##print images
for i, (image_name, turl, murl) in enumerate(ActualImages):
    try:
        #req = urllib2.Request(turl, headers={'User-Agent' : header})
        #raw_img = urllib2.urlopen(req).read()
        #req = urllib.request.Request(turl, headers={'User-Agent' : header})
        raw_img = urllib.request.urlopen(turl).read()

        cntr = len([i for i in os.listdir(DIR) if image_name in i]) + 1
        #print cntr

        f = open(os.path.join(DIR, image_name), 'wb')
        f.write(raw_img)
        f.close()
    except Exception as e:
        print("could not load : " + image_name)
        print(e)