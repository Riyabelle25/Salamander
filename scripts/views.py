from django.shortcuts import render
from django.http import HttpResponse
import datetime
import firebase_admin
import google.cloud
import pandas as pd
import json
import numpy as np
from scipy.sparse import csr_matrix
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from time import sleep
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
import time
import os
from urllib.request import urlopen
from urllib.request import Request
import datetime
from webdriver_manager.chrome import ChromeDriverManager

from firebase_admin import credentials, firestore
# Create your views here.


def current_datetime(request):
    now = datetime.datetime.now()
    html = "<html><body>Hey,It is now %s.</body></html>" % now
    return HttpResponse(html)


creds = credentials.Certificate("scripts/serviceKey.json")
myapp = firebase_admin.initialize_app(creds)

store = firestore.client()


def Results_toFirestore():
    col_ref = store.collection('users')
    # /users/XCeTunwzepf5rcvnLRS7/followers/HJqFZWxxwnh0qxm8GiFF/pagesFollowed
    data = {}
    try:
        docs = col_ref.get()
        for doc in docs:
            tmp = 'users/' + str(doc.id) + \
                '/followers/HJqFZWxxwnh0qxm8GiFF/pagesFollowed'
            print(tmp)
            sub_doc_refs = store.collection(tmp).get()
            sub_docs = []
            for sub_doc in sub_doc_refs:
                sub_docs.append(sub_doc.id)
            data["recommendations"] = sub_docs
            print(data)
        # mapping follower_id -> pagesFollowed_id
    except google.cloud.exceptions.NotFound:
        print(u'Missing data')
    return data


def calculate_recommendations(request):
    col_ref = store.collection('users')
    try:
        docs = col_ref.get()
        for doc in docs:
            tmp = 'users/' + str(doc.id) + '/following'
            print(tmp)
            store.collection(tmp).document(
                "HJqFZWxxwnh0qxm8GiFF").set(Results_toFirestore())

            print("DONE!")
    except google.cloud.exceptions.NotFound:
        print(u'Missing data')
    now = datetime.datetime.now()
    html = "<html><body>It is now %s,and the function is successfully deployed!!</body></html>" % now
    return HttpResponse(html)


def scrapper(request):
    count = 100  # number of profiles you want to scrap
    # User
    account = "salamandar_nemesis"  # account from
    page = "following"  # from following or followers
    page2="followers"
    yourusername = "salamandar_nemesis"  # your Instagram username
    yourpassword = "prakhar123"  # your Instagram password

    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument(
        '--user-agent="Mozilla/5.0 (iPhone; CPU iPhone OS 12_1_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/16D57"')
    try:
        driver = webdriver.Chrome(executable_path='./scripts/chromedriver')
    except:
        driver = webdriver.Chrome(executable_path='./scripts/chromedriver.exe')
    # Go to login page
    driver.get('https://www.instagram.com/accounts/login/')
    # needed
    sleep(2)
    try:
        username_input = driver.find_element_by_css_selector(
            "input[name='username']")
        password_input = driver.find_element_by_css_selector(
            "input[name='password']")
        # Person to get Gift For
        attack = 'prakhar__gupta__'
        username_input.send_keys(yourusername)
        password_input.send_keys(yourpassword)
        login_button = driver.find_element_by_xpath("//button[@type='submit']")
        login_button.click()
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(.,'Not Now')]"))).click()
    except:
        return HttpResponse("Check Your Network!!")
    # This file saves All people to be checked for public profile
    dirname = os.path.dirname(os.path.abspath(__file__))
    csvfilename = os.path.join(dirname, account + "-" + page + ".txt")
    f = open(csvfilename, 'w')
    # Going to someone's account
    driver.get('https://www.instagram.com/%s' % attack)
    driver.find_element_by_xpath('//a[contains(@href, "%s")]' % page).click()
    scr2 = driver.find_element_by_xpath(
        '//*[@id="react-root"]/section/main/div/header/section/ul/li[2]/a')
    # needed as popup loads
    sleep(2)
    text1 = scr2.text
    print(text1)
    x = datetime.datetime.now()
    print(x)
    # attack's 50 peeps
    for i in range(1, 700):
        try:
            scr1 = driver.find_element_by_xpath(
                '/html/body/div[5]/div/div/div[2]/ul/div/li[%s]' % i)
            driver.execute_script("arguments[0].scrollIntoView();", scr1)
            sleep(0.1)
            text = scr1.text
            list = text.encode('utf-8').split()
            for ar in list:
                if(str(ar) == 'b\'Verified\''):
                    print((str(list[0]).split('\'')[1]))
                    file_exists = os.path.isfile(csvfilename)
                    f.write((str(list[0]).split('\'')[1]) + "\r\n")
                    if i == (count-1):
                        print(x)
        except:
            continue

    # user
    #following
    faccount = open("account", 'w')
    driver.get('https://www.instagram.com/%s' % account)
    sleep(2)
    driver.find_element_by_xpath('//a[contains(@href, "%s")]' % page).click()
    scr2 = driver.find_element_by_xpath(
        '//*[@id="react-root"]/section/main/div/header/section/ul/li[2]/a')
    # needed as popup loads
    sleep(2)
    text1 = scr2.text
    print(text1)
    x = datetime.datetime.now()
    print(x)
    # user's 7 peeps
    for i in range(1, 7):
        try:
            scr1 = driver.find_element_by_xpath(
                '/html/body/div[5]/div/div/div[2]/ul/div/li[%s]' % i)
            driver.execute_script("arguments[0].scrollIntoView();", scr1)
        except:
            continue
        sleep(0.1)
        text = scr1.text
        list = text.encode('utf-8').split()
        file_exists = os.path.isfile("account")
        print('{};{}'.format(i, str(list[0]).split('\'')[1]))
        faccount.write((str(list[0]).split('\'')[1]) + "\r\n")
        if i == (count-1):
            print(x)
    #followers
    driver.get('https://www.instagram.com/%s' % account)
    sleep(2)
    driver.find_element_by_xpath('//a[contains(@href, "%s")]' % page2).click()
    scr2 = driver.find_element_by_xpath(
        '//*[@id="react-root"]/section/main/div/header/section/ul/li[2]/a')
    # needed as popup loads
    sleep(2)
    text1 = scr2.text
    print(text1)
    x = datetime.datetime.now()
    print(x)
    # user's 7 peeps
    for i in range(1, 7):
        try:
            scr1 = driver.find_element_by_xpath(
                '/html/body/div[5]/div/div/div[2]/ul/div/li[%s]' % i)
            driver.execute_script("arguments[0].scrollIntoView();", scr1)
            sleep(0.1)
            text = scr1.text
            list = text.encode('utf-8').split()
            file_exists = os.path.isfile("account")
            print('{};{}'.format(i, str(list[0]).split('\'')[1]))
            faccount.write((str(list[0]).split('\'')[1]) + "\r\n")
            if i == (count-1):
                print(x)
        except:
            continue
    faccount.close()
    
    #
    faccount = open("account", 'r')
    for x in faccount:
        try:
            driver.get('https://www.instagram.com/%s' % x.split('\n')[0])
            driver.find_element_by_xpath(
                '//a[contains(@href, "%s")]' % page).click()
            scr2 = driver.find_element_by_xpath(
                '//*[@id="react-root"]/section/main/div/header/section/ul/li[2]/a')
            # needed as popup loads
            sleep(2)
            text1 = scr2.text
            print(text1)
            x = datetime.datetime.now()
            print(x)
        except:
            continue
        # 40 people of all 7 peeps
        for i in range(1, 300):
            try:
                scr1 = driver.find_element_by_xpath(
                    '/html/body/div[5]/div/div/div[2]/ul/div/li[%s]' % i)
                driver.execute_script("arguments[0].scrollIntoView();", scr1)
                sleep(0.1)
                text = scr1.text
                list = text.encode('utf-8').split()
                for ar in list:
                    if(str(ar) == 'b\'Verified\''):
                        file_exists = os.path.isfile(csvfilename)
                        print('{};{}'.format(i, str(list[0]).split('\'')[1]))
                        f.write((str(list[0]).split('\'')[1]) + "\r\n")
                        if i == (count-1):
                            print(x)
            except:
                continue
    f.close()
    f = open(csvfilename, 'r')
    st = f.read()
    f.close()
    f = open(csvfilename, 'r')
    flock = open("abc", 'w')
    for x in f:
        try:
            link = "https://www.instagram.com/"+(x.split('\n')[0])+"/?__a=1"
            print(link)
            req = Request(
                link,
                data=None,
                headers={
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 12_1_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/16D57'
                }
            )
            webUrl = urlopen(req).read()
            flock.write(webUrl.decode("utf-8"))
            flock.write("\n")
            print(link)
        except Exception as e:
            continue
    f.close()
    flock.close()
    f = open("abc", 'r')
    fhash = open("hash", 'w')
    for x in f:
        while x.find("#") != -1:
            x = x[(x.find("#")+1):]
            data = ""
            i = 0
            while x[i].isalpha():
                data += x[i]
                i = i+1
            if data != "":
                fhash.write(data)
                fhash.write("\n")
    fhash.close()
    fhash = open("hash", 'r')
    dataG = []
    for x in fhash:
        dataG.append(x.split('\n')[0])
    final = {}
    final["recommendation"] = dataG
    col_ref = store.collection('users')
    tr=""
    print("a")
    for x in attack:
        if x.isalpha():
            tr+=x
    print(tr)
    try:
        docs = col_ref.get()
        for doc in docs:
            tmp = 'users/' + str(doc.id) + '/following/' + \
                tr+'/followedHashtags'
            store.collection(tmp).document(tr).set(final)
            print("DONE!")
    except google.cloud.exceptions.NotFound:
        print(u'Missing data')
    f.close()
    fhash.close()
    return HttpResponse("st")
