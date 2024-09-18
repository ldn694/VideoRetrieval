from flask import Flask, render_template, request, send_file, session
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
from VideoRetrieval import retrieve_frames, convert_to_suggestion_input, create_suggestion, retrieve_frames_multiple_queries
import settings

app = Flask(__name__)
app.secret_key = 'Yeu Phuong Anh<3'  # Necessary for session

# In-memory cache for storing frame data
cache_query = {}
cache_frame = {}
max_cache_query_size = 10
max_cache_frame_size = 1000

# Function to translate the query


def translate_query(query):
    translator = Translator()
    translated_query = translator.translate(query, dest='en').text
    return translated_query


# Global model variables (loaded once)
device = "cuda" if torch.cuda.is_available() else "cpu"
model, _, preprocess = open_clip.create_model_and_transforms(
    'MobileCLIP-B', pretrained='datacompdr_lt', device=device)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get input values
        # get all queries from the form
        queries = request.form.getlist('query')
        query = '#'.join(queries)
        folder_path = settings.DATA_PATH
        num_frames = int(request.form['num_frames'])
        view_mode = request.form['view_mode']

        # if view_mode == 'frame':
        #     suggestions = retrieve_frames_multiple_queries(
        #         queries, folder_path, num_frames)
        #     # Generate a unique key for this query
        #     cache_query_key = f"{query}_{folder_path}_{num_frames}"

        #     # Check if the frames are already cached in memory
        #     if cache_query_key not in cache_query:
        #         if len(cache_query) >= max_cache_query_size:
        #             # Remove the oldest cache entry
        #             oldest_key = next(iter(cache_query))
        #             del cache_query[oldest_key]
        #         # Retrieve frames if they are not cached
        #         suggestions = retrieve_frames_multiple_queries(
        #             queries, folder_path, num_frames)
        #         # Store the frames in the global cache
        #         cache_query[cache_query_key] = (suggestions)

        #     # Load the frames from the cache
        #     suggestions = cache_query[cache_query_key]
        #     # Frame view logic
        #     images = []
        #     for suggestion in suggestions:
        #         frames = suggestion['frames']
        #         frame = find_best_frame(frames)
        #         file_name = frame[5]
        #         frame_idx = frame[1]
        #         timestamp = frame[2]
        #         sim = frame[3]
        #         minute = int(float(timestamp)) // 60
        #         second = int(float(timestamp)) % 60
        #         cache_frame_key = f"{video_name}_{file_name}"
        #         if cache_frame_key not in cache_frame:
        #             if len(cache_frame) >= max_cache_frame_size:
        #                 # Remove the oldest cache entry
        #                 oldest_key = next(iter(cache_frame))
        #                 del cache_frame[oldest_key]
        #             # Load the image
        #             img = Image.open(os.path.join(
        #                 folder_path, 'keyframes', video_name, file_name))
        #             # Convert image to base64
        #             buffered = io.BytesIO()
        #             img.save(buffered, format="JPEG")
        #             img_str = base64.b64encode(
        #                 buffered.getvalue()).decode("utf-8")
        #             cache_frame[cache_frame_key] = img_str
        #         else:
        #             img_str = cache_frame[cache_frame_key]
        #         images.append(
        #             (img_str, video_name, frame_idx, sim, minute, second))

        #     return render_template('index.html', images=images, query=query, folder_path=folder_path, num_frames=num_frames)

        # elif view_mode == 'clip':
        # Clip view logic
        queries = request.form.getlist('query')

        # Create suggestions for clips
        suggestions = retrieve_frames_multiple_queries(
            queries, folder_path, num_frames)

        for suggestion in suggestions:
            frames = suggestion['frames']
            frame = find_best_frame(frames)
            file_name = frame[5]
            video_name = frame[0]

            # Load the image
            img = Image.open(os.path.join(
                folder_path, 'keyframes', video_name, file_name))

            # Resize the image to a lower quality version
            # Set the desired size for the low-quality image
            # max_size = (100, 100)
            # img.thumbnail(max_size)

            # Convert image to base64
            buffered = io.BytesIO()
            # Set the quality parameter to reduce quality
            img.save(buffered, format="JPEG", quality=20)
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            suggestion['img_str'] = img_str

        # Load the video_id.txt file to map video names to YouTube URLs
        video_urls = {}
        with open('video_id.txt', 'r') as f:
            for line in f:
                video_name, video_url = line.strip().split(' ')
                video_urls[video_name] = video_url

        return render_template(
            'index.html',
            suggestions=suggestions,
            video_urls=video_urls,
            num_frames=num_frames
        )

    return render_template('index.html')

# New route to handle the extraction of the current order and save to CSV


def find_best_frame(frames):
    # Find the frame with the highest similarity score
    best_frame = max(frames, key=lambda x: x[3])
    return best_frame


@app.route('/download_csv', methods=['POST'])
def download_csv():
    # Receive the order from the frontend
    data = json.loads(request.form['order'])
    custom_text = request.form['custom_text']  # Receive custom text

    # Create a CSV file
    csv_filename = 'query_answer.csv'
    csv_filepath = os.path.join(os.getcwd(), csv_filename)

    with open(csv_filepath, mode='w', newline='') as file:
        writer = csv.writer(file)
        for row in data:
            # If custom text is provided, add it as an extra column
            if custom_text:
                writer.writerow(
                    [row['video_name'], row['frame_idx'], custom_text])
            else:
                writer.writerow([row['video_name'], row['frame_idx']])

    # Send the file to the client using 'download_name' instead of 'attachment_filename'
    return send_file(csv_filepath, as_attachment=True, download_name=csv_filename)


if __name__ == '__main__':
    app.run(debug=True)
