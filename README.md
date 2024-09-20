# VideoRetrieval

## How to install

```
pip install -r requirements.txt
```

In `local_settings.py`, specify `DATA_PATH` to match your data path. For example 

```py
# local_settings.py
DATA_PATH = 'E:/AIC2024/Data'
```

## How to run

```
python web.py
```

## How to use

Please specify the folder path. The file should be organized like this
```
folder_path
|
|--keyframes
|-----------L01_V001
|-------------------001.jpg
|-------------------...
|-----------L01_V002
|-----------....
|--MobileClip
|-----------L01_V001.pt
|-----------L01_V002.pt
|-----------...
|--frame_data.json
```
