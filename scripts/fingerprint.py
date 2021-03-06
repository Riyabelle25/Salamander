# -*- coding: utf-8 -*-

import re, string
from unidecode import unidecode

PUNCTUATION = re.compile('[%s]' % re.escape(string.punctuation))

class Fingerprinter(object):
    '''
    Python implementation of Google Refine fingerprinting algorithm described here:
    https://github.com/OpenRefine/OpenRefine/wiki/Clustering-In-Depth
    Requires the unidecode module: https://github.com/iki/unidecode
    '''
    def __init__(self, string):
        self.string = self.uniqueSplit(string)

    def _preprocess(self, string):
        '''
        Strip leading and trailing whitespace, lowercase the string, remove all punctuation,
        in that order.
        '''
        return PUNCTUATION.sub('', string.strip().lower())

    def _latinize(self, string):
        '''
        Replaces unicode characters with closest Latin equivalent. For example,
        Alejandro González Iñárritu becomes Alejando Gonzalez Inarritu.
        '''
        return unidecode(string)

    def _unique_preserving_order(self, seq):
        '''
        Returns unique tokens in a list, preserving order. Fastest version found in this
        exercise: http://www.peterbe.com/plog/uniqifiers-benchmark
        '''
        seen = set()
        seen_add = seen.add
        return [x for x in seq if not (x in seen or seen_add(x))]
        
    def get_fingerprint(self):
        '''
        Gets conventional fingerpint.
        '''
        return self._latinize(' '.join(
            self._unique_preserving_order(
                sorted(self.string.split())
            )
        ))

    def get_ngram_fingerprint(self, n=1):
        '''
        Gets ngram fingerpint based on n-length shingles of the string.
        Default is 1.
        '''
        return self._latinize(''.join(
            self._unique_preserving_order(
                sorted([self.string[i:i + n] for i in range(len(self.string) - n + 1)])
            )
        ))
def uniqueSplit(hashtags):
    uniqueList=[]
    
    for hashtag in hashtags:
        if hashtag[0].islower():uniqueList.append(hashtag)
        elif hashtag[0:3].isupper():uniqueList.append(hashtag)
        else: uniqueList.append(re.findall('[A-Z][^A-Z]*', hashtag)[0])
    print(set(uniqueList))    
    return set(uniqueList)

def main(hashtags):
  
    return (list(uniqueSplit(hashtags)))
   
# nykaaLoves -> nykaa Loves
# BTS -> BTS
# 
