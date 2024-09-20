import numpy as np
import torch
import open_clip
from open_clip import tokenizer
import os
from PIL import Image
import matplotlib.pyplot as plt
import glob
import argparse
import json
import matplotlib.pyplot as plt
from googletrans import Translator
import chromadb
import settings

def translate_query(query):
    translator = Translator()
    translated_query = translator.translate(query, dest='en').text
    return translated_query

def retrieve_frames(query, folder_path, num_frames):
    if not os.path.exists(folder_path):
        folder_path = 'D:/AIC24/Data' # Change this to the path of the folder containing the data
    #device = "cuda" if torch.cuda.is_available() else "cpu"
    device = "cpu"
    model, _, preprocess = open_clip.create_model_and_transforms('MobileCLIP-B', pretrained='datacompdr_lt',device=device)

    # Create database file at folder "AIC_db" or load into client if exists.
    chroma_client = chromadb.PersistentClient(path="AIC_db")

    # Create the collection
    collection = chroma_client.get_collection("image_embeddings")

    query = translate_query(query)

    text = [query]
    text_tokens = tokenizer.tokenize(text)
    text_tokens = text_tokens.to(device)

    with torch.no_grad():
        text_features = model.encode_text(text_tokens).float()
        text_features /= text_features.norm(dim=-1, keepdim=True)

    query_vector = text_features[0].tolist()
        
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=10000
    )
    
    data_result = collection.get(ids=results['ids'][0], include = ["embeddings", "metadatas"])
    
    images_features = torch.FloatTensor(data_result['embeddings'])
    similiarity = (text_features @ images_features.transpose(1, 0)).squeeze(0)
    similiarity_all = []

    for i in range(len(similiarity)):
        similiarity_all.append((similiarity[i].item(), data_result['metadatas'][i]))
    
    similiarity_all = sorted(similiarity_all, key=lambda x: x[0], reverse=True)

    return similiarity_all[:num_frames]

def convert_to_suggestion_input(top_frames):
    # top_frames is the output of retrieve_frames function
    # list_frames is the output of retrieve_frames function
    # We need to convert these into a list of lists, where each list contains the top n frames for a query
    # Each frame is a tuple (similarity_score, video_name, frame_number, timestamp, file_name)

    suggestions_input = []

    for item in top_frames:
        frame_idx = item[1]['frame_idx']
        timestamp = float(item[1]['timestamp'])
        file_name = item[1]['path'][-7:]
        video_name = item[1]['video_name']
        suggestions_input.append(
            (item[0], video_name, frame_idx, timestamp, file_name))

    return suggestions_input

def create_suggestion(retrieved_frames=[]):
    # Assuming there are total k text queries
    # retrieved_frames will be a list of k lists, where each list will contain the top n frames for the corresponding query
    # Each frame is a tuple (similarity_score, video_name, frame_number, timestamp)
    # We now create a new list, each element is (video_name, frame_number, timestamp, similarity_score, query_number, file_name)
    # query_number is the index of the query in the list of queries (0-based index)

    combined_frames = []
    for query_number, frames in enumerate(retrieved_frames):
        for frame in frames:
            combined_frames.append(
                (frame[1], frame[2], int(frame[3]), frame[0], query_number, frame[4]))

    # Sort the combined_frames list based on video_name first, then frame_number, then query_number
    combined_frames.sort(key=lambda x: (x[0], x[1], x[4]))

    # Now we create a new list of suggestions
    # We use two pointers to iterate through the combined_frames list

    suggestions = []

    l = 0
    while l < len(combined_frames):
        r = l
        while r < len(combined_frames) and combined_frames[r][0] == combined_frames[l][0]:
            r += 1
        candidates = [(-1, -1)] * (len(retrieved_frames) + 1)
        for i in range(l, r):
            start_timestamp = combined_frames[i][2]
            # Each suggestion is maximum 60 seconds long
            max_end_timestamp = start_timestamp + 60
            query_appearances = [False] * len(retrieved_frames)
            unique_queries = 0
            for j in range(i, r):
                end_timestamp = combined_frames[j][2]
                if end_timestamp > max_end_timestamp:
                    break
                if (query_appearances[combined_frames[j][4]] == False):
                    query_appearances[combined_frames[j][4]] = True
                    unique_queries += 1
                    if candidates[unique_queries] == (-1, -1) or combined_frames[candidates[unique_queries][1]][2] - combined_frames[candidates[unique_queries][0]][2] > end_timestamp - start_timestamp:
                        candidates[unique_queries] = (i, j)

                if unique_queries == len(retrieved_frames):
                    break
        # Now we have the best suggestion for this video for each number of unique queries
        # We choose the best suggestion among these, which has the highest number of unique queries
        best_suggestion = (-1, -1, -1)
        for i in range(len(retrieved_frames), 0, -1):
            if candidates[i] != (-1, -1):
                best_suggestion = (candidates[i][0], candidates[i][1], i)
                break

        if best_suggestion != (-1, -1, -1):
            # Find the max similarity score among the frames in the best suggestion
            max_sim = 0
            for i in range(best_suggestion[0], best_suggestion[1] + 1):
                max_sim = max(max_sim, combined_frames[i][3])
            suggestions.append({'num_unique': best_suggestion[2], 'max_sim': max_sim,
                               'frames': combined_frames[best_suggestion[0]:best_suggestion[1] + 1]})

        l = r

    # Sort suggestions based on the num_unique, then max_sim, both in descending order
    suggestions.sort(key=lambda x: (-x['num_unique'], -x['max_sim']))

    return suggestions

def retrieve_frames_multiple_queries(queries, folder_path, num_frames):
    suggestions_inputs = []
    for id, query in queries:
        top_frames = retrieve_frames(
            query, folder_path, num_frames)
        suggestions_input = convert_to_suggestion_input(
            top_frames)
        suggestions_inputs.append(suggestions_input)

    suggestions = create_suggestion(suggestions_inputs)
    # shorten the len(suggestions) to num_frames
    suggestions = suggestions[:num_frames]
    return suggestions

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Video Retrieval')
    parser.add_argument('--query', type=str, help='Query to search for')
    parser.add_argument('--folder_path', type=str, default=settings.DATA_PATH,
                        help='Path to the folder containing the data')
    parser.add_argument('--num_frames', type=int, default=10,
                        help='Number of frames to retrieve')
    args = parser.parse_args()

    queries = args.query.split(',')
    suggestions_inputs = []
    for query in queries:
        top_frames = retrieve_frames(
            query, args.folder_path, args.num_frames)
        suggestions_input = convert_to_suggestion_input(
            top_frames)
        suggestions_inputs.append(suggestions_input)

    suggestions = create_suggestion(suggestions_inputs)
    with open('suggestions.json', 'w') as f:
        json.dump(suggestions, f, indent=4)




