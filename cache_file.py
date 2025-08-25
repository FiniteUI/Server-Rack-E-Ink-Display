#very simple module for easily managing simple key/value json files

import os
import json
import logging

logger = logging.getLogger(__name__)

class CacheFile:
    def __init__(self, file='cache'):
        self.file = file

    def __getCachePath(self):
        #builds the cache file path
        path = os.path.join(os.getcwd(), '.cache')
        if not os.path.isdir(path):
            logging.info(f'Creating cache folder [{path}]...')
            os.makedirs(path)
        
        path = os.path.join(path, f'{self.file}.json')
        return path
    
    def getFilePath(self):
        return self.__getCachePath()

    def __getCacheJSONDictionary(self):
        #returns the cache json file as a dictionary
        path = self.__getCachePath()

        if os.path.exists(path):
            with open(path, 'r+') as f:
                cache = json.load(f)
        else:
            cache = {}

        return cache

    def __saveCacheFile(self, cache):
        #updates the cache file
        path = self.__getCachePath()

        with open(path, 'w') as f:
            json.dump(cache, f, indent = 4)

    def __is_serializable(value):
        try:
            json.dumps(value)
            return True
        except(TypeError, OverflowError):
            return False
        
    def setValue(self, key, value):
        #saves a value to the cache file
        cache = self.__getCacheJSONDictionary()

        if not CacheFile.__is_serializable(value):
            value = str(value)

        logging.info(f'Saving cache key [{key}] value [{value}]')
        cache[key] = value
        self.__saveCacheFile(cache)

    def getValue(self, key, default=None):
        #returns a value from the cache file
        cache = self.__getCacheJSONDictionary()

        if key in cache.keys():
            logging.debug(f'Retrieving cache key [{key}] value [{cache[key]}]')
            return cache[key]
        else:
            return default