import requests
import time
from scipy.io.wavfile import read, write
import io

upload_endpoint = "https://api.assemblyai.com/v2/upload"
transcript_endpoint = "https://api.assemblyai.com/v2/transcript"

def make_header(api_key):
    return {
    'authorization': api_key,
    'content-type': 'application/json'
    }


# Helper for `upload_file()`
def _read_file(filename, chunk_size=5242880):
    with open(filename, "rb") as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            yield data


# Like _read_file but for array - creates temporary unsaved "file" from sample rate and audio np.array
def _read_array(audio, chunk_size=5242880):
    sr, aud = read(audio)

    # Create temporary "file" and write data to it
    bytes_wav = bytes()
    temp_file = io.BytesIO(bytes_wav)
    write(temp_file, sr, aud)

    while True:
        data = temp_file.read(chunk_size)
        if not data:
            break
        yield data


# Uploads a file to AAI servers
def upload_file(audio_file, header):
    upload_response = requests.post(
        upload_endpoint,
        headers=header,
        data=_read_file(audio_file)
    )
    if upload_response.status_code != 200:
        upload_response.raise_for_status()
    # Returns {'upload_url': <URL>}
    return upload_response.json()


'''
Example **kwargs:

{
"speaker_labels": True,
"language_detection": True,  # Otherwise need to specify language with e.g. "language_code": "en_us"
"filter_profanity": True,
# AUDIO INTELLIGENCE:
"redact_pii": True,
"redact_pii_policies": ["drug", "injury", "person_name"], - more types https://www.assemblyai.com/docs/audio-intelligence#pii-redaction
"redact_pii_sub": "entity_name",
"auto_highlights": True,
"content_safety": True,
"iab_categories": True,
"sentiment_analysis": True,
"auto_chapters": True,
"entity_detection": True,
}
'''
def request_transcript(upload_url, header, **kwargs):
    # If input is a dict returned from `upload_file` rather than a raw upload_url string
    if type(upload_url) is dict:
        upload_url = upload_url['upload_url']

    # Create request
    transcript_request = {
        'audio_url': upload_url,
        **kwargs
    }

    # POST request
    transcript_response = requests.post(
        transcript_endpoint,
        json=transcript_request,
        headers=header
    )

    return transcript_response.json()


def make_polling_endpoint(transcript_id):
    # If upload response is input rather than raw upload_url string
    if type(transcript_id) is dict:
        transcript_id = transcript_id['id']

    polling_endpoint = "https://api.assemblyai.com/v2/transcript/" + transcript_id
    return polling_endpoint


def wait_for_completion(polling_endpoint, header):
    while True:
        polling_response = requests.get(polling_endpoint, headers=header)
        polling_response = polling_response.json()

        if polling_response['status'] == 'completed':
            break
        elif polling_response['status'] == 'error':
            raise Exception(f"Error: {polling_response['error']}")

        time.sleep(5)


# Get the paragraphs of the transcript
def get_paragraphs(polling_endpoint, header):
    paragraphs_response = requests.get(polling_endpoint + "/paragraphs", headers=header)
    paragraphs_response = paragraphs_response.json()

    paragraphs = []
    for para in paragraphs_response['paragraphs']:
        paragraphs.append(para)

    return paragraphs