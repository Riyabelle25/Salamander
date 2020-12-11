from django.shortcuts import render
from django.http import HttpResponse
import datetime
import firebase_admin
import google.cloud
import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix

#for item in items:
 #   title = item.title.string.lower()

   # input()
from firebase_admin import credentials, firestore
# Create your views here.
def current_datetime(request):
    api = finding(appid= 'JamesCan-HiMilesp-PRD-c246ab013-815fa751', config_file=None)
    api_request = { 'keywords': 'White Piano'}
    response = api.execute('findItemsByKeywords', api_request)
    soup = BeautifulSoup(response.content,'lxml')

    totalentries = int(soup.find('totalentries').text)
    items = soup.find_all('item')

    now = datetime.datetime.now()
    html = "<html><body>Hey,It is now %s.</body></html>" % now
    return HttpResponse(items[0])


creds = credentials.Certificate("scripts/serviceKey.json")
myapp = firebase_admin.initialize_app(creds)

store = firestore.client()

# def Results_toFirestore():
#     col_ref = store.collection('users')
#     # /users/XCeTunwzepf5rcvnLRS7/followers/HJqFZWxxwnh0qxm8GiFF/followedHashtags
#     data = {}
#     try:
#         docs = col_ref.get()  
#         for doc in docs:
#             tmp = 'users/'+ str(doc.id) + '/followers/HJqFZWxxwnh0qxm8GiFF/followedHashtags'
#             print(tmp)
#             sub_doc_refs = store.collection(tmp).get()
#             sub_docs=[]         
#             for sub_doc in sub_doc_refs:
#                 sub_docs.append(sub_doc.id)
#             data["recommendations"] = sub_docs
#             print(data)
#         # mapping follower_id -> followedHashtags_id
#     except google.cloud.exceptions.NotFound:
#         print(u'Missing data')
#     return data


# def calculate_recommendations(request):
#     """Responds to any HTTP request.
#     Args:
#         request (flask.Request): HTTP request object.
#     Returns:
#         The response text or any set of values that can be turned into a
#         Response object using
#         `make_response <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>`.
#     """
#     col_ref = store.collection('users')
#     try:
#         docs = col_ref.get()
#         for doc in docs:
#             tmp = 'users/'+ str(doc.id) + '/followers'
#             print(tmp)
#             store.collection(tmp).document("HJqFZWxxwnh0qxm8GiFF").set(Results_toFirestore())

#             print("DONE!")
#     except google.cloud.exceptions.NotFound:
#         print(u'Missing data')
#     now = datetime.datetime.now()
#     html = "<html><body>It is now %s,and the function is successfully deployed!!</body></html>" % now
#     return HttpResponse(html)

##################################################################################################################################################################


'''Function to get data from firestore collection.
    collection = "users/{userid}/followers/{followerid}/followedHashtags"
Args:
    userid : string value
Returns:
    data : dictiionary of {follower_id -> hashtagList} 
'''
def getCollectionData(userid):
    col_ref = store.collection("users/"+ userid+ "/followers")
    data = {}
    try:
        followers = col_ref.get()  
        for follower in followers:
            tmp = "users/"+ userid+ "/followers/"+ follower.id + "/followedHashtags"
            hashtags = store.collection(tmp).get()
            hashtagsList=[]         
            for hashtag in hashtags:
                hashtagsList.append(hashtag.id)
            data[follower.id] = hashtagsList
    except google.cloud.exceptions.NotFound:
        print(u'Missing data')
    return data

'''Function to manipulate fetched data into desired dataframe.
Args:
    none.
Returns:
    list: dataframe of followerid x hashtags, followers, hashtags

'''
def finalData():
    data = getCollectionData("XCeTunwzepf5rcvnLRS7")

    for key in data:    
        for hashtags in data[key]:        
            for hashtag in hashtags["hashtags"]:
                tmp1.append(key)
                tmp2.append(hashtag)

    df = pd.DataFrame(list(zip(tmp1, tmp2)), 
                   columns =['Followerid', 'Hashtag'])

    followers = df["Followerid"].unique()
    hashtags = df["Hashtag"].unique()  

    # transitioning Followerid and hashtags
    df['followers'] = df['Followerid'].apply(lambda x : np.argwhere(followers == x)[0][0])
    df['hashtags'] = df['Hashtag'].apply(lambda x : np.argwhere(hashtags == x)[0][0])
    
    return df, followers , hashtags        


def set_occurences(follower, item , occurences):
    occurences[follower,item] += 1
    
def co_occurences():
    data_array = finalData()
    df,followers,hashtags=data_array    
    occurences = csr_matrix((followers.shape[0], hashtags.shape[0]), dtype='int8')
    df.apply(lambda row: set_occurences(row['followers'],row['hashtags'],occurences), axis=1)
    cooc = occurences.transpose().dot(occurences)
    cooc.setdiag(0)
    return cooc, hashtags

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

def final_calculations():
    co_occurence,hashtags = co_occurences()
    
    row_sum = np.sum(co_occurence, axis=0).A.flatten()
    column_sum = np.sum(co_occurence, axis=1).A.flatten()
    total = np.sum(row_sum, axis=0)
    pp_score = csr_matrix((co_occurence.shape[0], co_occurence.shape[1]), dtype='double')
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
    return result_indices, hashtags

def Results_toFirestore(request):
    results,hashtags = final_calculations()

    for i in range(len(results)):
        hashtag = hashtags[i]
        result = results[i] 

        dict = {}

        for j in range(len(result)):
            dict[str(j)]= str(hashtags[result[j]])    

        store.collection("recommendations").document(hashtag).set(dict)

    now = datetime.datetime.now()
    html = "<html><body>It is now %s,and the function is successfully deployed!!</body></html>" % now
    return HttpResponse(html)
