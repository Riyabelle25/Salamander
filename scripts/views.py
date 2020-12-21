from django.shortcuts import render, redirect
from django.http import HttpResponse
import datetime
import webbrowser
import firebase_admin
from django.http import JsonResponse
import google.cloud
import pandas as pd
import json
import numpy as np
import environ
from scipy.sparse import csr_matrix
from .forms import newUserRegistration
from scipy.sparse import csr_matrix, lil_matrix
from ebaysdk.finding import Connection as finding
from bs4 import BeautifulSoup
import asyncio
import threading
from django.http import HttpResponseRedirect
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

env = environ.Env()
environ.Env.read_env()
# SCRAPE THE PRODUCT DATA


# GET items from EBAY-API
def ebayAPI(hashtag,key,min=10,max=50):
    tmp1= []
    tmp3 = []
    api = finding(appid = 'SarthakS-Salamand-PRD-8f78dd8ce-ef33d6b3', config_file=None)
    api_request = { 'keywords': hashtag,'itemFilter': [               
                # {'name': 'LocatedIn',
                #  'value': 'IN'},
                #  {'name':'Currency',
                #  'value':'INR'},
                 {'name': 'BestOfferOnly',
                 'value': 1},
                #  {'name':'FeaturedOnly',
                #  'value': 1},
                 {'name':'HideDuplicateItems',
                 'value': 1},
                 {'name':'MaxPrice',
                 'value':max
                #  'paramName':'Currency',
                #  'paramValue':'INR'
                 },
                 {'name':'MinPrice',
                 'value':min}
                #  'paramName':'Currency',
                #  'paramValue':'INR'
                #  }
                 ],
                 'SortOrderType':'PricePlusShippingLowest'}
    response = api.execute('findItemsByKeywords', api_request)
    soup = BeautifulSoup(response.content,'lxml')
    
    if (soup.find('totalentries'))!= None:
        print("total enteries for:",hashtag, int(soup.find('totalentries').text))
        items = soup.find_all('viewitemurl')
        
        if len(items)>=2:
            for item in items[:3]:
                print(key,item.contents[0])
                tmp3.append(item.contents[0])
                tmp1.append(key)
    print("size of tmp3",len(tmp3))
    print("size of tmp1",len(tmp1))
    return tmp3, tmp1

# SCRAPE THE PRODUCT DATA
def amazonScrape(hashtag,key):
    tmp1 = []
    tmp3 = []

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
    url = "https://www.amazon.in/s?k=" + hashtag
    print("Downloading %s" % url)
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
        return tmp1,tmp3

    if e.extract(r.text) == None:
        print("None!")
        return tmp1,tmp3

    else:
        if e.extract(r.text)['products'] != None:
            productfeed = e.extract(r.text)['products']
            counter = 0
            for product in productfeed:
                if counter > 3: break
                if product['price']==None:print("Price is NONE")
                elif product['price']!=None: 
                    print(counter,"price NOT NONE")
                    price = int(float(product['price'][1:].replace(',','')))
                    print(price)
                    if price>=500:
                        product_url = "https://www.amazon.in" + product['url']
                        counter+=1
                        print(product_url)
                        tmp3.append(product_url)
                        tmp1.append(key)
                        
    return tmp1,tmp3

    # Pass the HTML of the page and create HttpResponse(items[0])
    
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


'''Function to manipulate fetched data into desired dataframe.
Args:
    none.
Returns:
    list: dataframe of followerid x hashtags, followers, hashtags
'''

def finalData(target,opt="amazon",mi=10,ma=50):
    try:
        updateStatus(target, 'a7', '1')
    except:
        pass
    data = getCollectionData(target)

    # dummy data = {"Nish":["MHA","Darkacademia","Knights","Poetry","Pups"],
    # "Sarthak":["Disney","Brooklyn99","Pups","Babies","Poetry"],
    # "Riya":["MHA","Darkacademia","Brookyln99","Cupcakes","HarryPotter"],
    # }
    # print(data)

    tmp1 = []  # tmp1 is storing followers [data ka key]
    tmp3 = []  # tmp3 is storing products ke urls

# key means each person
    for key in data:
# pre processing hashtags:
        print("HASHTAGS before preprocessed:", key,"length:",len(data[key]))
        hashtags = fingerprint.main(data[key])
        print("HASHTAGS after preprocessed for :",key,"length:",len(hashtags))
        # hashtags = data[key]
        print("177",len(hashtags))

        for hashtag in hashtags[:10]:
            print(hashtag)            
            if opt == "ebay":
                data1 = ebayAPI(hashtag,key,mi,ma)
                tmp3+= data1[0]
                tmp1+=data1[1]
            elif opt=="amazon":
                data1= amazonScrape(hashtag,key)
                tmp1+= data1[0]
                tmp3+=data1[1]
        
        print(key,len(tmp1),len(tmp3))
    
    # print(tmp1,tmp3)
    df = pd.DataFrame(list(zip(tmp1,tmp3)),

                      columns=['Followerid', 'product'])

    followers = df["Followerid"].unique()
    products = df["product"].unique()

    # transitioning Followerid and products
    df['followers'] = df['Followerid'].apply(
        lambda x: np.argwhere(followers == x)[0][0])
    df['products'] = df['product'].apply(
        lambda x: np.argwhere(products == x)[0][0])

    print(len(followers),len(products))
    print("ORDERED non-Normalised LIST OF PERSONS:",tmp1)
    print("ORDERED non-Normalised LIST OF ITEMS:",tmp3)
    print("DATAFRAME:",df.head(20))

    followers=df['followers']
    products=df['products']
    print("normalised persons:",followers)
    print("normalised items:",products)

    try:
        updateStatus(target, 'a8', '1')
    except:
        pass
    return df, followers, products, tmp1,tmp3

    # url = "https://www.amazon.in/s?k=Parasite"
    # return HttpResponse(scrape(url)[1])


''' 
functions computing co-occurence matrix, and the math needed for recommendations.
'''

def set_occurences(follower, item, occurences):
    occurences[follower, item] += 1


def co_occurences(target,gf,mi,ma):

    df, followers, products, tmp1,tmp3 = finalData(target,gf,mi,ma)
    occurences = lil_matrix(
        (followers.shape[0], products.shape[0]), dtype='int8')
    print("164")
    df.apply(lambda row: set_occurences(
        row['followers'], row['products'], occurences), axis=1)
    print("167")
    cooc = occurences.transpose().dot(occurences)
    print("169")
    cooc.setdiag(0)
    print("171")
    return cooc, followers, tmp1, products ,tmp3


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


def final_calculations(target,gf,mi,ma):
    try:
        updateStatus(target, 'a6', '1')
    except:
        pass
    co_occurence, followers, tmp1, products , tmp3 = co_occurences(target,gf,mi,ma)

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
    try:
        updateStatus(target, 'a9', '1')
    except:
        pass
    return result_indices, followers, tmp1, products , tmp3


'''
Computing final results.
'''
def Results(username, ps, target,current_url,gf,mi,ma):
    scrapper(username, ps, target)
    user_id = removeUnderscore(target)
    try:
        updateStatus(user_id, 'a2', '1')
    except:
        pass
    results, followers, tmp1, products, tmp3 = final_calculations(user_id,gf,mi,ma)

# followers = [0,0,0,0,0,0,0,0,1,1,1,1,1,2,2.......], tmp1=[Nish,Riya,Sarthak]
# products = [0,1,2,3,4,5,6,3,4,5,6,.................], tmp3=[bag,mug,poster......]
       
    # for i in range(len(tmp1)):
    # # we're first iterating over the list of persons. 
    # # At the end of each iteration we shall set the dict {follower:{0:item0,1:item1..}} into Firestore
    # # There shall be 2 items stored after each iteration: one is the original item the other is the top ranked recommendation
    #     dict = {}
    #     counter+=1
    #     print(len(tmp1))
        
    #     follower = tmp1[i]
    #     result = results[products[i]]
    #     dict[str(i)]=  tmp3[i]
    # # result is a sorted list of items that can be recommended along with the product at that index i.e products[i]
    #     print(i,follower)
    #     for j in range(0,1):
    #         print(j)
    #         dict[str(j)]=tmp3[result[j]]
    #     store.collection("recommendations").document(follower).set(dict)
    counter=0
    dict = {}
# Results matrix is n x n: if n is the total number of products suggested for all the persons involved.
    for i in range(len(results)):
        print(len(results))
        print(followers.tolist()[i])
        if counter==10:
            temp = {val : key for key, val in dict.items()} 
            res = {val : key for key, val in temp.items()}
            store.collection("recommendations").document(tmp1[i]).set(res)
            print("stored!",dict)
            
            if followers[i]==followers[i-1]:                         
    # we have 6 items in our dict now.
                continue
            elif followers[i]!=followers[i-1]:
                print("switch")
                dict={}
                counter = 0
                                       
        follower = tmp1[i]
        print(i,counter) # i =1 pe counter=2, print that i jispe counter is again 0
        result = results[i]
        print(follower)
                                           
        dict[str(counter)] = str(tmp3[i])
        counter+=1
        for j in range(1,3):
            print(j,counter) 
            dict[str(counter)] = str(tmp3[result[j-1]])
            counter+=1
        print(dict) # counter 3 pe first iteration end hua and 2 items dikhega   
    


    print(current_url)
    current_url += 'getResults/'+user_id
    targetUrl=removeUnderscore(target)
    updateStatus(targetUrl, 'a10', current_url)
    hash = "./scripts/hash"+target
    abc = "./scripts/abc"+target
    account = "./scripts/account"+target
    salam = "./scripts/"+target+".txt"
    print(os.listdir())
    try:
        os.remove(hash)
    except Exception as e:
        print(e)
    try:
        os.remove(abc)
    except:
        pass
    try:
        os.remove(account)
    except:
        pass
    try:
        os.remove(salam)
    except:
        pass



def scrapper(userNamed, ps, target):
    try:
        updateStatus(targetShort, 'a3', '1')
    except:
        pass
    count = 100  # number of profiles you want to scrap
    # User
    account = userNamed  # account from
    page = "following"  # from following or followers
    page2 = "followers"
    yourusername = userNamed  # your Instagram username
    yourpassword = ps  # your Instagram password
    options = webdriver.ChromeOptions()
    print(env('is_heroku'))
    if(env('is_heroku') == 'true'):
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument(
            '--user-agent="Mozilla/5.0 (iPhone; CPU iPhone OS 12_1_4 like Mac OS X) (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36"')
        try:
            options.binary_location = os.environ.get(
                'GOOGLE_CHROME_BIN', '/app/.apt/usr/bin/google-chrome')
        except:
            pass
        try:
            driver = webdriver.Chrome(
                executable_path='/app/.chromedriver/bin/chromedriver', chrome_options=options)
        except:
            driver = webdriver.Chrome(
                executable_path='./scripts/chromedriver', chrome_options=options)
    else:
        options.add_argument('--ignore-certificate-errors')
        options.add_argument(
            '--user-agent="Mozilla/5.0 (iPhone; CPU iPhone OS 12_1_4 like Mac OS X) (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36"')
        try:
            driver = webdriver.Chrome(
                executable_path='./scripts/chromedriver', chrome_options=options)
        except:
            driver = webdriver.Chrome(
                executable_path='./scripts/chromedriver.exe', chrome_options=options)
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
    csvfilename = os.path.join(dirname, target + ".txt")
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
    for i in range(1, 220):
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
    alltosearch = os.path.join(dirname, "account"+target)
    faccount = open(alltosearch, 'w')
    try:
        driver.set_page_load_timeout(12)
        driver.get('https://www.instagram.com/%s' % account)
    except:
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
    # user's 9 peeps
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
        file_exists = os.path.isfile(alltosearch)
        print('{};{}'.format(i, str(list[0]).split('\'')[1]))
        faccount.write((str(list[0]).split('\'')[1]) + "\r\n")
        if i == (count-1):
            print(x)
    faccount.close()

    #
    faccount = open(alltosearch, 'r')
    for x in faccount:
        try:
            f.write('*'+x.split('\n')[0])
            f.write('\n')
            driver.set_page_load_timeout(12)
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
        for i in range(1, 70):
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
                        if publicNo > 6:
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
    alltoabc = os.path.join(dirname, "abc" + target)
    flock = open(alltoabc, 'w')
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
            try:
                webUrl = urlopen(req, timeout=4).read()
            except:
                continue
            flock.write(webUrl.decode("utf-8"))
            flock.write("\n")
            print(link)
        except Exception as e:
            continue
    f.close()
    flock.close()
    f = open(alltoabc, 'r')
    alltohash = os.path.join(dirname, "hash" + target)
    fhash = open(alltohash, 'w')
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
    fhash = open(alltohash, 'r')
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
                    tmp = 'users/' + str(tr) + '/following'
                    if username != '':
                        store.collection(tmp).document(username).set(final)
                    else:
                        print('harrr')
                except google.cloud.exceptions.NotFound:
                    print(u'Missing data')
                    continue
                final = {}
                dataG.clear()
                username = x.split('*')[1]
            else:
                username = x.split('*')[1]
            continue
        dataG.append(x.split('\n')[0])
    # f.close()
    fhash.close()
    try:
        updateStatus(targetShort, 'a4', '1')
    except:
        pass
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
            geeks_field = form.cleaned_data['geeks_field']
            min = form.cleaned_data['minP']
            max = form.cleaned_data['maxP']
            target = form.cleaned_data['Target']
            if username == '' or ps == '' or target == '':
                return render(request, 'scripts/home.html', {'form': form, 'message': 'Invalid Details'})
            else:
                thread = utils.ThreadingExample()
                current_url = request.build_absolute_uri()
                print(current_url)
                print("aa")
                thread.thread(request, username, ps, target, current_url,geeks_field,min,max)
                return render(request, 'scripts/home.html', {'form': form, })
    else:
        form = newUserRegistration()
        return render(request, 'scripts/home.html', {'form': form, })


def getResults(request, target='prakhar__gupta__'):
    userid = removeUnderscore(target)
    print("628",userid)
    col_ref = store.collection("recommendations").document(userid)
    data = {}
    doneGuys = []
    counter = 0
    try:
        followers = col_ref.get()
        if followers.exists:
            for x in followers.to_dict():
                doneGuys.append(str(x))
                r = requests.get(
                    url="https://urlpreview.vercel.app/api/v1/preview?url="+str(followers.to_dict()[x]))
                url_names = r.json()
                if url_names['title'] == None:
                    continue
                data[followers.to_dict()[x]] = url_names['title']
                print(url_names['title'])
                counter += 1
                if counter == 12:
                    break
    except google.cloud.exceptions.NotFound:
        print('Missing data')
    return render(request, 'scripts/results.html', {'data': data})


def validate_username(request):
    username = request.GET.get('username', None)
    username = removeUnderscore(username)
    col_ref = store.collection("update/"+username+"/status")
    data = {}
    try:
        followers = col_ref.get()
        for follower in followers:
            current_path = "update/"+username+"/status" + follower.id
            if follower.to_dict()["isDone"] != None:
                data[follower.id] = follower.to_dict()["isDone"]
                # print(data)
            else:
                data[follower.id] = '0'
    except google.cloud.exceptions.NotFound:
        print('Missing data')
    return JsonResponse(data)


def updateStatus(userid, name, update):
    try:
        tmp = "update/"+userid+"/status"
        data = {"isDone": update}
        store.collection(tmp).document(name).set(data)
    except google.cloud.exceptions.NotFound:
        print(u'Missing data')
