import json
from collections import defaultdict

import pandas as pd
from elasticsearch import Elasticsearch

# Instantiate a client instance
client = Elasticsearch("http://3.101.85.85:9200")


def clean_data(x):
    return str.lower(x.replace(" ", ""))


def create_soup(x):
    return x['original_title'] + ' ' + x['authors'] + ' ' + x['average_rating']


def get_song_details_by_song_id(song_id):
    build_query = {
        "query": {
            "query_string": {
                "default_field": "song_id",
                "query": song_id
            }
        }
    }
    #print(build_query)
    result = client.search(index="msd", body=build_query)
    #print(result)
    return  result["hits"]["hits"][0]["_source"]

def search_multiple_songs(listOfSongIds):
    build_query = {
        "query": {
            "terms": {
                "song_id": listOfSongIds,
                "boost": 1.0
            }
                }
            }
    #print(build_query)
    result = client.search(index="msd", body=build_query)
    #print(result)
    return  [d["_source"] for d in result["hits"]["hits"]]

def get_song_by_name(title):
    #print('get_song_by_name')
    query_body = {
        "query": {"query_string": {"default_field": "title", "query": title}}}
    #print(query_body)
    result = client.search(index="msd", body=query_body)
    #print('get_song_by_name-result')
    #print(result)
    song_id=0
    if len(result["hits"]["hits"]) >0 :
        song_id = result["hits"]["hits"][0]['_source']['song_id']
    #print("query hits:", song_id)

    return get_recommendations_by_song_id(song_id)


def get_song_list(search_string):
    response_dic = defaultdict(list)
    result = client.search(index="msd", body={"size": 1000,"from": 0,"query": {"multi_match": {"query": search_string ,"fields": ["title","year","artist_name"]}}})
    if len(result["hits"]["hits"]) > 0:
        all_hits = result["hits"]["hits"]
        for _song in all_hits:
            # remove the duplicate song_id
            if (_song['_source']["song_id"]) not in response_dic["song_id"]:
                #print('Added the song_id', _song['_source']["song_id"])
                response_dic["song_id_category"].append(_song['_source']["song_id_category"])
                response_dic["song_id"].append(_song['_source']["song_id"])
                response_dic["title"].append(_song['_source']["title"])
                response_dic["artist_id"].append(_song['_source']["artist_id"])
                response_dic["artist_name"].append(_song['_source']["artist_name"])
                response_dic["danceability"].append(_song['_source']["danceability"])
                response_dic["duration"].append(_song['_source']["duration"])
                response_dic["key"].append(_song['_source']["key"])
                response_dic["key_confidence"].append(_song['_source']["key_confidence"])
                response_dic["tempo"].append(_song['_source']["tempo"])
                response_dic["time_signature"].append(_song['_source']["time_signature"])
                response_dic["time_signature_confidence"].append(_song['_source']["time_signature_confidence"])
                response_dic["year"].append(_song['_source']["year"])

    return pd.DataFrame(response_dic)


def get_recommendations_by_song_id(id):
    list_mf = get_recommendations_by_song_id_mf(id)
    list_cs = get_recommendations_by_song_id_cs(id)
    final_list = list_mf + list_cs
    #print('final_list',final_list)
    final_list=sorted(final_list, key=lambda x: (x['score_type'], x['rating']),reverse=True)

    unique_songs = set()
    unique_final_list = []
    for x in final_list:
        x['song_id']=int(x['song_id'])
        #print(x['song_id'], ':' ,unique_songs)
        if x['song_id'] not in unique_songs and x['song_id'] != int(id):
            unique_songs.add(x['song_id'])
            unique_final_list.append(x)

    return unique_final_list

#Matrix Factorization
def get_recommendations_by_song_id_mf(id):
    #print('get_recommendations_by_song_id=',id)
    resp = client.info()
    #print('resp=',resp)
    query_body = {
        "query": {
            "bool": {
                "must": {
                    "match": {
                        "recommendations.song_id": id
                    }
                }
            }
        }
    }
    #print(query_body)
    result = client.search(index="result", body=query_body)
    #print('sidd-result')
    #print(result)
    list2=[]
    if len(result["hits"]["hits"]) > 0:
        list2 = result["hits"]["hits"][0]['_source']['recommendations']
        # it may need to be changed to song_id
        song_ids = [d['song_id'] for d in list2]
        #print(song_ids)
        list1 = search_multiple_songs(song_ids)
        #pprint.pprint(list2)
        #pprint.pprint(list1)
        #print(len(list2), len(list1))
        for x in list2:
            x['score_type'] = '1-mf'
            songs=[i for i in list1 if i['song_id'] == str(x['song_id'])]
            if len(songs) >0:
                song_details = songs[0]
                x['title'] = song_details['title']
                x['artist_name'] = song_details['artist_name']
                x['year'] = song_details['year']
            else:
                x['title'] = ''
                x['artist_name'] = ''
                x['year'] = ''

    return list2

#Cosine Similarity
def get_recommendations_by_song_id_cs(id):
    #print('get_recommendations_by_song_id_cs(id)=',id)
    resp = client.info()
    query_body = {
        "query": {
            "bool": {
                "must": {
                    "match": {
                        "song_id": id
                    }
                }
            }
        }
    }
    result = client.search(index="cosine", body=query_body)
    final_list=[]
    if len(result["hits"]["hits"]) > 0:
        list2 = result["hits"]["hits"][0]['_source']['collect_list(recommendations)']
        #print('type of list2',type(list2))
        # it may need to be changed to song_id

        # for d in list2:
        #     print(d)
        #     print(type(d))
        #     print((json.loads(d))['compared_song_id'])

        song_ids = [(json.loads(d))['compared_song_id'] for d in list2]
        list1 = search_multiple_songs(song_ids)
        for x in list2:
            #print('type of x', type(x))
            x=json.loads(x)
            x['score_type'] = '2-cs'
            x['song_id'] = x['compared_song_id']
            x['rating'] = x['similarity']
            songs=[i for i in list1 if i['song_id'] == str(x['song_id'])]
            if len(songs) >0:
                song_details = songs[0]
                x['title'] = song_details['title']
                x['artist_name'] = song_details['artist_name']
                x['year'] = song_details['year']
            else:
                x['title'] = ''
                x['artist_name'] = ''
                x['year'] = ''

            final_list.append(x)
    return final_list