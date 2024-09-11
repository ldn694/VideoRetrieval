from flask import Flask, render_template, request, send_file
import os
import torch
import open_clip
from open_clip import tokenizer
from PIL import Image
import matplotlib.pyplot as plt
import io
import base64
import json
import csv
from googletrans import Translator

app = Flask(__name__)

# Function to translate the query
def translate_query(query):
    translator = Translator()
    translated_query = translator.translate(query, dest='en').text
    return translated_query

# Global model variables (loaded once)
device = "cuda" if torch.cuda.is_available() else "cpu"
model, _, preprocess = open_clip.create_model_and_transforms('MobileCLIP-B', pretrained='datacompdr_lt', device=device)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get input values
        query = request.form['query']
        folder_path = request.form['folder_path']
        num_frames = int(request.form['num_frames'])

        # Translate the query
        query = translate_query(query)
        print("Translated query:", query)

        # Tokenize the input query
        text = [query]
        text_tokens = tokenizer.tokenize(text)
        text_tokens = text_tokens.to(device)
        
        # Encode text features
        with torch.no_grad():
            text_features = model.encode_text(text_tokens).float()
            text_features /= text_features.norm(dim=-1, keepdim=True)

        # Load frame data
        frame_data_path = os.path.join(folder_path, 'frame_data.json')
        if not os.path.exists(frame_data_path):
            return 'frame_data.json not found in the provided folder path'
        
        frame_data = json.load(open(frame_data_path))
        list_frames = {}
        list_videos = []

        # Organize frame data by video
        l = 0
        while l < len(frame_data):
            r = l
            while r < len(frame_data) and frame_data[r]['video_name'] == frame_data[l]['video_name']:
                r += 1
            video_name = frame_data[l]['video_name']
            list_frames[video_name] = frame_data[l:r]
            list_videos.append(video_name)
            l = r

        # Calculate similarity scores
        similiarity_all = []
        for video_name in list_videos:
            images_features_path = os.path.join(folder_path, 'MobileClip', video_name + '.pt')
            if os.path.exists(images_features_path):
                images_features = torch.load(images_features_path, map_location=device).float()
                similiarity = (text_features @ images_features.transpose(1, 0)).squeeze(0)
                for i in range(len(similiarity)):
                    similiarity_all.append((similiarity[i].item(), video_name, i))
        
        # Sort and retrieve top frames based on similarity
        similiarity_all.sort(reverse=True)
        top_frames = similiarity_all[:num_frames]

        # Prepare images to display
        images = []
        for sim, video_name, index in top_frames:
            frame = list_frames[video_name][index]
            img = Image.open(os.path.join(folder_path, 'keyframes', video_name, frame['file_name']))
            frame_idx = frame['frame_idx']
            
            # Convert image to base64
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            images.append((img_str, video_name, frame_idx, sim))

        return render_template('index.html', images=images, query=query, folder_path=folder_path, num_frames=num_frames)

    return render_template('index.html')

# New route to handle the extraction of the current order and save to CSV
@app.route('/download_csv', methods=['POST'])
def download_csv():
    data = json.loads(request.form['order'])  # Receive the order from the frontend
    custom_text = request.form['custom_text']  # Receive custom text

    # Create a CSV file
    csv_filename = 'query_answer.csv'
    csv_filepath = os.path.join(os.getcwd(), csv_filename)

    with open(csv_filepath, mode='w', newline='') as file:
        writer = csv.writer(file)
        for row in data:
            # If custom text is provided, add it as an extra column
            if custom_text:
                writer.writerow([row['video_name'], row['frame_idx'], custom_text])
            else:
                writer.writerow([row['video_name'], row['frame_idx']])

    # Send the file to the client using 'download_name' instead of 'attachment_filename'
    return send_file(csv_filepath, as_attachment=True, download_name=csv_filename)

if __name__ == '__main__':
    app.run(debug=True)
