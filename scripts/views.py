from django.shortcuts import render
from django.http import HttpResponse
import datetime
import firebase_admin
import google.cloud
import pandas as pd
import json
import numpy as np
from scipy.sparse import csr_matrix
from .forms import newUserRegistration
from scipy.sparse import csr_matrix, lil_matrix
from ebaysdk.finding import Connection as finding
from bs4 import BeautifulSoup
import asyncio

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
import requests

from selectorlib import Extractor
import requests
import json
from time import sleep
from scripts import fingerprint
from firebase_admin import credentials, firestore
from scripts import utils

credz = credentials.Certificate("scripts/serviceKey.json")
app = firebase_admin.initialize_app(credz)

store = firestore.client()
user_id = ""


#SCRAPE THE PRODUCT DATA
def scrape(url):  

    # Create an Extractor by reading from the YAML file
    e = Extractor.from_yaml_file('scripts/search_results.yml')

    headers = {
        'dnt': '1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-dest': 'document',
        'referer': 'https://www.amazon.in/',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    }

    # Download the page using requests

    print("Downloading %s"%url)
    r = requests.get(url, headers=headers, timeout=28)
    # Simple check to check if page was blocked (Usually 503)
    if r.status_code > 500:
        if "To discuss automated access to Amazon data please contact" in r.text:
            print(
                "Page %s was blocked by Amazon. Please try using better proxies\n" % url)
        else:
            print("Page %s must have been blocked by Amazon as the status code was %d" % (
                url, r.status_code))
        print(r.status_code)
        return None

    # Pass the HTML of the page and create 
    return e.extract(r.text)



'''Function to get data from firestore collection.
    collection = "users/{userid}/followers/{followerid}/followedHashtags"
Args:
    userid : string value
Returns:
    data : dictionary of {follower_id -> hashtagList} 
'''


def getCollectionData(userid):
    col_ref = store.collection("users/"+userid+"/following")
    print(userid)
    data = {}

    try:
        print("131")

        followers = col_ref.get()
        print(followers)
        for follower in followers:
            print(follower.id)
            current_path = "users/" + userid + "/following/" + follower.id
            print(current_path)
            print(follower.to_dict())
            if follower.to_dict()['recommendations'] != None:
                data[follower.id] = follower.to_dict()['recommendations']
                print(data) 

    except google.cloud.exceptions.NotFound:
        print('Missing data')

    return data


'''
Convert list of hashtags to long string
'''

def listToString(s):      
    # initialize an empty string 
    str1 = " "     
    # return string   
    return (str1.join(s)) 

 
'''Function to manipulate fetched data into desired dataframe.
Args:
    none.
Returns:
    list: dataframe of followerid x hashtags, followers, hashtags

'''


def finalData():
    
    data = getCollectionData("prakhargupta")

    # data = {"Nish":["MHA","Darkacademia","Knights","Poetry","Pups"],
    # "Sarthak":["Disney","Brooklyn99","Pups","Babies","Poetry"],
    # "Riya":["MHA","Darkacademia","Brookyln99","Cupcakes","HarryPotter"],
    # }
    print(data)
    tmp1= [] # tmp1 is storing followers [data ka key]
    tmp3= [] # tmp3 is storing products ke urls
    

    for key in data:

        hashtags=fingerprint.main(listToString(data[key]))
        print(len(hashtags))

        for hashtag in hashtags[:10]:
            print(hashtag)
            url = "https://www.amazon.in/s?k=" + hashtag
            data1 = scrape(url) 
            if data1 == None: print("None!")          
            else:
                if data1['products']!=None:
                    productfeed=data1['products']
                    for product in productfeed[:5]:
                        # tmp3, tmp1 for zipping into df
                        product_url= "https://www.amazon.in" + product['url']
                        print(product_url)
                        tmp3.append(product_url)
                        tmp1.append(key)
        
    print(key,len(tmp1),len(tmp3))

    df = pd.DataFrame(list(zip(tmp1, tmp3)), 
                columns =['Followerid', 'product'])

    followers = df["Followerid"].unique()
    products = df["product"].unique()

    # transitioning Followerid and products
    df['followers'] = df['Followerid'].apply(lambda x : np.argwhere(followers == x)[0][0])
    df['products'] = df['product'].apply(lambda x : np.argwhere(products == x)[0][0])
    print(len(followers),len(products))
    print(df.head(10))
    return df,followers,products,tmp1

    # url = "https://www.amazon.in/s?k=Parasite"
    # return HttpResponse(scrape(url)[1])         
    

''' 
functions computing co-occurence matrix, and the math needed for recommendations.
'''


def set_occurences(follower, item, occurences):
    occurences[follower, item] += 1


def co_occurences():

    df,followers,products,tmp1 = finalData()
    occurences = lil_matrix((followers.shape[0], products.shape[0]), dtype='int8')
    print("164")
    df.apply(lambda row: set_occurences(
        row['followers'], row['products'], occurences), axis=1)
    print("167")
    cooc = occurences.transpose().dot(occurences)
    print("169")
    cooc.setdiag(0)
    print("171")
    return cooc, followers, tmp1, products


def xLogX(x):
    return x * np.log(x) if x != 0 else 0.0


def entropy(x1, x2=0, x3=0, x4=0):
    return xLogX(x1 + x2 + x3 + x4) - xLogX(x1) - xLogX(x2) - xLogX(x3) - xLogX(x4)


def LLR(k11, k12, k21, k22):
    rowEntropy = entropy(k11 + k12, k21 + k22)
    columnEntropy = entropy(k11 + k21, k12 + k22)
    matrixEntropy = entropy(k11, k12, k21, k22)
    if rowEntropy + columnEntropy < matrixEntropy:
        return 0.0
    return 2.0 * (rowEntropy + columnEntropy - matrixEntropy)


def rootLLR(k11, k12, k21, k22):
    llr = LLR(k11, k12, k21, k22)
    sqrt = np.sqrt(llr)
    if k11 * 1.0 / (k11 + k12) < k21 * 1.0 / (k21 + k22):
        sqrt = -sqrt
    return sqrt


'''
Using the above functions to compute result indices for each product
'''


def final_calculations():
    co_occurence, followers, tmp1, products = co_occurences()

    row_sum = np.sum(co_occurence, axis=0).A.flatten()
    column_sum = np.sum(co_occurence, axis=1).A.flatten()
    total = np.sum(row_sum, axis=0)
    pp_score = lil_matrix(
        (co_occurence.shape[0], co_occurence.shape[1]), dtype='double')
    print("205")  # pp_score.tolil()
    cx = co_occurence.tocoo()
    for i, j, v in zip(cx.row, cx.col, cx.data):
        if v != 0:
            k11 = v
            k12 = row_sum[i] - k11
            k21 = column_sum[j] - k11
            k22 = total - k11 - k12 - k21
            pp_score[i, j] = rootLLR(k11, k12, k21, k22)

    result = np.flip(np.sort(pp_score.A, axis=1), axis=1)
    result_indices = np.flip(np.argsort(pp_score.A, axis=1), axis=1)
    minLLR = 5
    indicators = result[:, :50]
    indicators[indicators < minLLR] = 0.0
    indicators_indices = result_indices[:, :50]
    max_indicator_indices = (indicators == 0).argmax(axis=1)
    max = max_indicator_indices.max()
    indicators = indicators[:, :max+1]
    indicators_indices = indicators_indices[:, :max+1]
    return result_indices, followers, tmp1, products


'''
Computing final results.
'''
def Results():
    user_id = "prakhargupta"
    results,followers,tmp1,products = final_calculations()
    
# followers = [0,0,0,0,0,0,0,0,1,1,1,1,1,2,2.......]
# products = [0,1,2,3,4,5,6,3,4,5,6,.................]

    for i in range(len(results)):
        print(len(results))
        follower = tmp1[i]
        result = results[i]
        print(follower)
        dict = {}
        dict[str(0)] = str(products[i])
        for j in range(1,10):
            print(j)
            dict[str(j)] = str(products[result[j]])

    # {"0":"",}

        store.collection("recommendations").document(follower).set(dict)

    # now = datetime.datetime.now()
    # html = "<html><body>It is now %s,and the function is successfully deployed!!</body></html>" % now
    # return HttpResponse(html)


def scrapper(userNamed, ps, target):
    count = 100  # number of profiles you want to scrap
    # User
    account = userNamed  # account from
    page = "following"  # from following or followers
    page2 = "followers"
    yourusername = userNamed  # your Instagram username
    yourpassword = ps  # your Instagram password
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
        attack = target
        username_input.send_keys(yourusername)
        password_input.send_keys(yourpassword)
        login_button = driver.find_element_by_xpath("//button[@type='submit']")
        login_button.click()
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(.,'Not Now')]"))).click()
    except:
        return ("Check Your Network!!")
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
    f.write(('*'+attack))
    f.write('\n')
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
    # following
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
    for i in range(1, 10):
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
    faccount.close()

    #
    faccount = open("account", 'r')
    for x in faccount:
        try:
            f.write('*'+x.split('\n')[0])
            f.write('\n')
            driver.set_page_load_timeout(6)
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
        publicNo = 0
        # 100 people of all 7 peeps
        for i in range(1, 100):
            try:
                scr1 = driver.find_element_by_xpath(
                    '/html/body/div[5]/div/div/div[2]/ul/div/li[%s]' % i)
                driver.execute_script("arguments[0].scrollIntoView();", scr1)
                sleep(0.1)
                text = scr1.text
                list = text.encode('utf-8').split()
                for ar in list:
                    if(str(ar) == 'b\'Verified\''):
                        publicNo = publicNo+1
                        if publicNo > 10:
                            break
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
            if(x[0] == '*'):
                flock.write(x)
                continue
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
        if(x[0] == '*'):
            fhash.write(x)
            continue
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
    username = ''
    col_ref = store.collection('users')
    tr = ""
    print("a")
    for x in attack:
        if x.isalpha():
            tr += x
    print(tr)
    final = {}
    for x in fhash:
        if x[0] == '*':
            if username != '':
                username = removeUnderscore(username)

                final["recommendations"] = dataG
                try:
                    docs = col_ref.get()
                    for doc in docs:
                        tmp = 'users/' + str(tr) + '/following'
                        store.collection(tmp).document(username).set(final)
                except google.cloud.exceptions.NotFound:
                    print(u'Missing data')
                final = {}
                dataG.clear()
                username = x.split('*')[1]
            else:
                username = x.split('*')[1]
            continue
        dataG.append(x.split('\n')[0])
    # f.close()
    fhash.close()
    return ("st")


def removeUnderscore(ref):
    tr = ""
    print("a")
    for x in ref:
        if x.isalpha():
            tr += x
    return tr


def home(request):

    if request.method == 'POST':
        form = newUserRegistration(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            ps = form.cleaned_data['ps']
            target = form.cleaned_data['Target']
            if username == '' or ps == '' or target == '':
                return render(request, 'scripts/home.html', {'form': form, 'message': 'Invalid Details'})
            else:
                scrapper(username, ps, target)
                return render(request, 'scripts/home.html', {'form': form, })
    else:
        form = newUserRegistration()
        return render(request, 'scripts/home.html', {'form': form, })


def getResults(request, target='prakhar__gupta__'):
    userid = removeUnderscore(target)
    col_ref = store.collection("recommendations").document(userid)
    data = {}

    counter = 0
    try:
        followers = col_ref.get()
        if followers.exists:
            for x in followers.to_dict():
                r = requests.get(
                    url="https://urlpreview.vercel.app/api/v1/preview?url="+str(followers.to_dict()[x]))
                url_names = r.json()
                if url_names['title'] == None:
                    continue
                data[followers.to_dict()[x]] = url_names['title']
                print(url_names['title'])
                counter += 1
                if counter == 6:
                    break
    except google.cloud.exceptions.NotFound:
        print('Missing data')
    return render(request, 'scripts/results.html', {'data': data})
