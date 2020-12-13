from django.shortcuts import render
from django.http import HttpResponse
import datetime
import firebase_admin
import google.cloud
import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix,lil_matrix
from ebaysdk.finding import Connection as finding
from bs4 import BeautifulSoup

from selectorlib import Extractor
import requests 
import json 
from time import sleep
from scripts import fingerprint
from firebase_admin import credentials, firestore

credz = credentials.Certificate("scripts/serviceKey.json")
app = firebase_admin.initialize_app(credz)

store = firestore.client()


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
    r = requests.get(url, headers=headers)
    # Simple check to check if page was blocked (Usually 503)
    if r.status_code > 500:
        if "To discuss automated access to Amazon data please contact" in r.text:
            print("Page %s was blocked by Amazon. Please try using better proxies\n"%url)
        else:
            print("Page %s must have been blocked by Amazon as the status code was %d"%(url,r.status_code))
        print(r.status_code)
        return None
    # Pass the HTML of the page and create 
    return e.extract(r.text), r.text

'''Function to get data from firestore collection.
    collection = "users/{userid}/followers/{followerid}/followedHashtags"
Args:
    userid : string value
Returns:
    data : dictionary of {follower_id -> hashtagList} 
'''
def getCollectionData(userid):
    col_ref = store.collection("users/"+userid+"/following")
    data = {}

    try:
        print("131")

        followers = col_ref.get()
        for follower in followers:
            print(follower.id)
            current_path = "users/" + userid + "/following/" + follower.id
            print(current_path) 
            print(follower.to_dict()) 
            if follower.to_dict()['recommendations']!=None:
                data[follower.id] = follower.to_dict()['recommendations']
                print(data) 
            # hashtags = store.collection(tmp).get()    
            # for hashtag in hashtags: 
            #     print("137")
            #     print(hashtag.id)
            #     print(hashtag.to_dict()) 
            #     if hashtag.to_dict()['recommendations']!=None:
            #         data[hashtag.id] = hashtag.to_dict()['recommendations']
            #         print(data)
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
            data1 = scrape(url)[0]
    
            if data1['products']!= None:
                for product in data1['products']:

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
def set_occurences(follower, item , occurences):
    occurences[follower,item] += 1
    
def co_occurences():
    data_array = finalData()
    df,followers,products,tmp1=data_array    
    occurences = lil_matrix((followers.shape[0], products.shape[0]), dtype='int8')
    print("164")
    df.apply(lambda row: set_occurences(row['followers'],row['products'],occurences), axis=1)
    print("167")
    cooc = occurences.transpose().dot(occurences)
    print("169")
    cooc.setdiag(0)
    print("171")
    return cooc, followers , tmp1, products

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
    co_occurence,followers,tmp1,products = co_occurences()
    
    row_sum = np.sum(co_occurence, axis=0).A.flatten()
    column_sum = np.sum(co_occurence, axis=1).A.flatten()
    total = np.sum(row_sum, axis=0)
    pp_score = lil_matrix((co_occurence.shape[0], co_occurence.shape[1]), dtype='double')
    print("205") #pp_score.tolil()
    cx = co_occurence.tocoo()
    for i,j,v in zip(cx.row, cx.col, cx.data):
        if v != 0:
            k11 = v
            k12 = row_sum[i] - k11
            k21 = column_sum[j] - k11
            k22 = total - k11 - k12 - k21
            pp_score[i,j] = rootLLR(k11, k12, k21, k22)

    result = np.flip(np.sort(pp_score.A, axis=1), axis=1)
    result_indices = np.flip(np.argsort(pp_score.A, axis=1), axis=1)
    minLLR = 5
    indicators = result[:, :50]
    indicators[indicators < minLLR] = 0.0
    indicators_indices = result_indices[:, :50]
    max_indicator_indices = (indicators==0).argmax(axis=1)
    max = max_indicator_indices.max()
    indicators = indicators[:, :max+1]
    indicators_indices = indicators_indices[:, :max+1]
    return result_indices, followers , tmp1,products

'''
Computing final results.
'''
def Results(request):
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
        for j in range(1,31):
            print(j)
            dict[str(j)]= str(products[result[j]])  

    # {"0":"",}

        store.collection("recommendations").document(follower).set(dict)

    now = datetime.datetime.now()
    html = "<html><body>It is now %s,and the function is successfully deployed!!</body></html>" % now
    return HttpResponse(html)
