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
import time


def get_db_num_query_results(db_mode):
    if db_mode == 'slow':
        return 100000
    elif db_mode == 'fast':
        return 5000
    else:
        return 20000


def translate_query(query):
    translator = Translator()
    translated_query = translator.translate(query, dest='en').text
    return translated_query


def retrieve_frames_from_image(image_paths, folder_path, num_frames, device, model, collection, preprocess, db_mode):
    if len(image_paths) == 0:
        return []
    if not os.path.exists(folder_path):
        # Change this to the path of the folder containing the data
        folder_path = 'D:/AIC24/Data'

    start = time.time()

    # We load the images
    images = []
    for image_path in image_paths:
        image = preprocess(Image.open(image_path)).unsqueeze(0)
        images.append(image)

    with torch.no_grad():
        image_features = model.encode_image(
            torch.cat(images).to(device)).float()
        image_features /= image_features.norm(dim=-1, keepdim=True)

    print(f"shape: {image_features.shape}")

    # Convert the image_features to a list of list
    results = collection.query(
        query_embeddings=image_features.tolist(),
        n_results=get_db_num_query_results(db_mode)
    )

    data_result = []
    embedding_result = []

    for i in range(len(results['ids'])):
        data_result.append(collection.get(
            ids=results['ids'][i], include=["embeddings", "metadatas"]))
        embedding_result.append(data_result[-1]['embeddings'])

    print(f"inference time: {time.time() - start}")

    A = torch.FloatTensor(embedding_result)
    B = image_features
    C = torch.matmul(A, B.unsqueeze(-1)).squeeze(-1)

    print(A.shape)
    print(B.shape)
    print(C.shape)

    # C has the shape of (q, n) where q is the number of queries and n is the number of results
    # C[i, j] is the similarity score between query i and result j
    # sort the results based on the similarity score

    sorted_indices = torch.argsort(C, dim=1, descending=True)

    results = []
    for i in range(len(image_paths)):
        results.append([])
        for j in range(num_frames * 2):
            results[-1].append({"meta_data": data_result[i]['metadatas']
                               [sorted_indices[i, j]], "similarity": C[i, sorted_indices[i, j]].item()})

    return results


def retrieve_frames(queries, folder_path, num_frames, device, model, collection, db_mode):
    if len(queries) == 0:
        return []
    if not os.path.exists(folder_path):
        # Change this to the path of the folder containing the data
        folder_path = 'D:/AIC24/Data'

    start = time.time()

    text = []
    for query in queries:
        query = translate_query(query[1])
        text.append(query)

    text_tokens = tokenizer.tokenize(text)
    text_tokens = text_tokens.to(device)

    with torch.no_grad():
        text_features = model.encode_text(text_tokens).float()
        text_features /= text_features.norm(dim=-1, keepdim=True)

    print(f"shape: {text_features.shape}")

    # Convert the text_features to a list of list

    results = collection.query(
        query_embeddings=text_features.tolist(),
        n_results=get_db_num_query_results(db_mode)
    )

    data_result = []
    embedding_result = []

    for i in range(len(results['ids'])):
        data_result.append(collection.get(
            ids=results['ids'][i], include=["embeddings", "metadatas"]))
        embedding_result.append(data_result[-1]['embeddings'])

    print(f"inference time: {time.time() - start}")

    A = torch.FloatTensor(embedding_result)
    B = text_features
    C = torch.matmul(A, B.unsqueeze(-1)).squeeze(-1)

    print(A.shape)
    print(B.shape)
    print(C.shape)

    # C has the shape of (q, n) where q is the number of queries and n is the number of results
    # C[i, j] is the similarity score between query i and result j
    # sort the results based on the similarity score

    sorted_indices = torch.argsort(C, dim=1, descending=True)

    results = []
    for i in range(len(queries)):
        results.append([])
        for j in range(num_frames * 2):
            results[-1].append({"meta_data": data_result[i]['metadatas']
                               [sorted_indices[i, j]], "similarity": C[i, sorted_indices[i, j]].item()})

    return results


def convert_to_suggestion_input(top_frames, len_file_name):
    # top_frames is the output of retrieve_frames function
    # list_frames is the output of retrieve_frames function
    # We need to convert these into a list of lists, where each list contains the top n frames for a query
    # Each frame is a tuple (similarity_score, video_name, frame_number, timestamp, file_name)

    suggestions_input = []

    for item in top_frames:
        frame_idx = item['meta_data']['frame_idx']
        timestamp = float(item['meta_data']['timestamp'])
        file_name = item['meta_data']['path'][-len_file_name:]
        video_name = item['meta_data']['video_name']
        suggestions_input.append(
            (item['similarity'], video_name, frame_idx, timestamp, file_name))

    return suggestions_input


def create_suggestion(retrieved_frames=[]):
    # Assuming there are total k text queries
    # retrieved_frames will be a list of k lists, where each list will contain the top n frames for the corresponding query
    # Each frame is a tuple (similarity_score, video_name, frame_number, timestamp)
    # We now create a new list, each element is (video_name, frame_number, timestamp, similarity_score, query_number, file_name)
    # query_number is the index of the query in the list of queries (0-based index)

    print(f"Number of queries: {len(retrieved_frames)}")
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
        candidates = [[] for _ in range(len(retrieved_frames) + 1)]
        i = l
        while i < r:
            start_timestamp = combined_frames[i][2]
            max_end_timestamp = start_timestamp + 60
            query_appearances = [False] * len(retrieved_frames)
            unique_queries = 0
            j = i
            while j < r:
                end_timestamp = combined_frames[j][2]
                if end_timestamp > max_end_timestamp:
                    break
                if not query_appearances[combined_frames[j][4]]:
                    query_appearances[combined_frames[j][4]] = True
                    unique_queries += 1
                j += 1
            candidates[unique_queries].append(
                (i, j - 1, end_timestamp - start_timestamp))
            i = j
        # Now we have the best suggestion for this video for each number of unique queries
        # We choose the best suggestion among these, which has the highest number of unique queries
        best_suggestions = None
        max_unique_queries = 0
        for i in range(len(retrieved_frames), 0, -1):
            if len(candidates[i]) > 0:
                best_suggestions = sorted(candidates[i], key=lambda x: x[2])[
                    :min(5, len(candidates[i]))]
                max_unique_queries = i
                break

        if best_suggestions != None:
            # Find the max similarity score among the frames in the best suggestion
            for i in range(len(best_suggestions)):
                best_suggestion = best_suggestions[i]
                max_sim = -1
                for j in range(best_suggestion[0], best_suggestion[1] + 1):
                    max_sim = max(max_sim, combined_frames[j][3])

                max_frames_sim = [-1] * len(retrieved_frames)
                max_frames = [-1] * len(retrieved_frames)
                for j in range(best_suggestion[0], best_suggestion[1] + 1):
                    if combined_frames[j][3] > max_frames_sim[combined_frames[j][4]]:
                        max_frames_sim[combined_frames[j]
                                       [4]] = combined_frames[j][3]
                        max_frames[combined_frames[j][4]] = j - \
                            best_suggestion[0]

                suggestions.append({
                    'video_name': combined_frames[best_suggestion[0]][0],
                    'frames': combined_frames[best_suggestion[0]:best_suggestion[1] + 1],
                    'max_frames': max_frames,
                    'num_unique': max_unique_queries,
                    'max_sim': max_sim
                })

        l = r

    # Sort suggestions based on the num_unique, then max_sim, both in descending order
    suggestions.sort(key=lambda x: (-x['num_unique'], -x['max_sim']))

    return suggestions


# @db_mode: 'slow' or 'fast' or 'standard'
def retrieve_frames_multiple_queries(queries, folder_path,
                                     num_frames, device, model,
                                     collection, image_paths, preprocess,
                                     db_mode):
    suggestions_inputs = []
    list_top_frames = retrieve_frames(
        queries, folder_path, num_frames, device, model, collection, db_mode)
    list_top_frames_from_image = retrieve_frames_from_image(
        image_paths, folder_path, num_frames, device, model, collection, preprocess, db_mode)

    print("Text queries: ", queries)
    print("Image queries: ", image_paths)
    print("Number of frames: ", num_frames)
    print(f"DB Mode: {db_mode}")

    if collection.name == 'image_embeddings':
        len_file_name = 7
    else:
        len_file_name = 9

    for top_frames in list_top_frames:
        suggestions_input = convert_to_suggestion_input(
            top_frames, len_file_name)
        suggestions_inputs.append(suggestions_input)

    for top_frames in list_top_frames_from_image:
        suggestions_input = convert_to_suggestion_input(
            top_frames, len_file_name)
        suggestions_inputs.append(suggestions_input)

    suggestions = create_suggestion(suggestions_inputs)
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
