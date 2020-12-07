from django.shortcuts import render
from django.http import HttpResponse
import datetime
import firebase_admin
import google.cloud
import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix

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
            tmp = 'users/'+ str(doc.id) + '/followers/HJqFZWxxwnh0qxm8GiFF/pagesFollowed'
            print(tmp)
            sub_doc_refs = store.collection(tmp).get()
            sub_docs=[]         
            for sub_doc in sub_doc_refs:
                sub_docs.append(sub_doc.id)
            data["recommendations"] = sub_docs
            print(data)
        # mapping follower_id -> pagesFollowed_id
    except google.cloud.exceptions.NotFound:
        print(u'Missing data')
    return data


def calculate_recommendations(request):
    """Responds to any HTTP request.
    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>`.
    """
    col_ref = store.collection('users')
    try:
        docs = col_ref.get()
        for doc in docs:
            tmp = 'users/'+ str(doc.id) + '/followers'
            print(tmp)
            store.collection(tmp).document("HJqFZWxxwnh0qxm8GiFF").set(Results_toFirestore())

            print("DONE!")
    except google.cloud.exceptions.NotFound:
        print(u'Missing data')
    now = datetime.datetime.now()
    html = "<html><body>It is now %s,and the function is successfully deployed!!</body></html>" % now
    return HttpResponse(html)
