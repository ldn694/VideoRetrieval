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

    print('Model loaded')

    query = translate_query(query)

    print(query)

    text = [query]
    text_tokens = tokenizer.tokenize(text)
    text_tokens = text_tokens.to(device)

    with torch.no_grad():
        text_features = model.encode_text(text_tokens).float()
        text_features /= text_features.norm(dim=-1, keepdim=True)

    list_frames = {}
    list_videos = []

    # read the frame_data.json
    frame_data = json.load(open(os.path.join(folder_path, 'frame_data.json')))
    print('Frame data loaded')
    print(len(frame_data))
    l = 0
    while l < len(frame_data):
        r = l
        while r < len(frame_data) and frame_data[r]['video_name'] == frame_data[l]['video_name']:
            r += 1
        video_name = frame_data[l]['video_name']
        list_frames[video_name] = frame_data[l:r]
        list_videos.append(video_name)
        l = r

    similiarity_all = []

    for video_name in list_videos:
        # load .pt file
        images_features_path = os.path.join(folder_path, 'MobileClip', video_name + '.pt')
        images_features = torch.load(images_features_path, map_location=device).float()
        similiarity = (text_features @ images_features.transpose(1, 0)).squeeze(0)
        for i in range(len(similiarity)):
            similiarity_all.append((similiarity[i].item(), video_name, i))
    
    similiarity_all.sort(reverse=True)
    

    return similiarity_all[:num_frames], list_frames



