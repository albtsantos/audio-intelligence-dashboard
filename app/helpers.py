import re

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
    sr, aud = audio

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
def upload_file(audio_file, header, is_file=True):
    upload_response = requests.post(
        upload_endpoint,
        headers=header,
        data=_read_file(audio_file) if is_file else _read_array(audio_file)
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


def _split_on_capital(string):
    """Adds spaces between capitalized words of a string"""
    return ' '.join(re.findall("[A-Z][^A-Z]*", string))


def _make_tree(c, ukey=''):
    '''
    Given a list whose elements are topics or lists of topics, generated a JSON-esque dictionary tree of topics and
    subtopics
    
    :param c: List of categories 
    :param ukey: Name of key for which value is key
    :return: Dictionary of tree structure
    '''
    # Create empty dict for current sublist
    d = dict()
    # If leaf, return None (alternative behavior: get rid of ukey and return None for if c is None)
    if c is None and ukey is None:
        return None
    elif c is None:
        return {None: None}
    else:
        for n, i in enumerate(c):
            # For topics with sublist e.g. if ['NewsAndPolitics' 'Politics'] and ['NewsAndPolitics' 'Politics', 'Elections] are both in list - need way to signify politics itself included
            if i is None:
                d[None] = None
            # If next subtopic not in dict, add it. If the remaining list empty, make value None
            elif i[0] not in d.keys():
                topic = i.pop(0)
                d[topic] = None if i == [] else [i]
            # If subtopic already in dict
            else:
                # If the value for this subtopic is only None (i.e. subject itself is a leaf), then append sublist
                if d[i[0]] is None:
                    d[i[0]] = [None, i[1:]]
                # If value for this subtopic is a list itself, then append the remaining list
                else:
                    d[i[0]].append(i[1:])
        # Recurse on remaining leaves
        for key in d:
            d[key] = _make_tree(d[key], key)
    return d


def _make_html_tree(dic, level=0, HTML = ''):
    """
    Generates an HTML tree from an output of _make_tree
    :param dic: 
    :param level: 
    :param HTML: 
    :return: 
    """
    for key in dic:
        # Add the topic to HTML, specifying the current level and whether or not it is a topic
        if type(dic[key]) == dict:
            if None in dic[key].keys():
                del dic[key][None]
                HTML += f'<p class="topic-L{level} istopic">{_split_on_capital(key)}</p>'
            else:
                HTML += f'<p class="topic-L{level}">{_split_on_capital(key)}</p>'

            HTML = _make_html_tree(dic[key], level=level+1, HTML=HTML)
        else:
            HTML += f'<p class="topic-L{level} istopic">{_split_on_capital(key)}</p>'
    return HTML

def _make_html_body(dic):
    """Makes an HTML body from an output of _make_tree"""
    HTML = '<body>'
    HTML += '<p class="detected-topics">Detected Topics</p>'
    HTML += _make_html_tree(dic)
    HTML += "</body>"
    return HTML


def _make_html(dic):
    """Makes a full HTML document from an output of _make_tree using styles.css styling"""
    HTML = '<!DOCTYPE html>' \
       '<html>' \
       '<head>' \
       '<title>Another simple example</title>' \
       '<link rel="stylesheet" type="text/css" href="styles.css"/>' \
       '</head>'
    HTML += _make_html_body(dic)
    HTML += "</html>"
    return HTML


#make_html_from_topics(j['iab_categories_result']['summary'])
def make_html_from_topics(dic, threshold=0.0):
    """Given a topics dictionary from AAI Topic Detection API, generates a structured HTML page from it"""
    # Filter low probab items out
    dic = {k:v for k,v in dic.items() if float(v) >= threshold}

    # Get list of remaining topics
    cats = list(dic.keys())

    # Sort remaining topics
    cats.sort()

    # Split items into lists
    cats = [i.split(">") for i in cats]

    tree = _make_tree(cats)

    return _make_html(tree)



def make_paras_string(paragraphs):
    '''input = response.json()['paragraphs'] from aai paragraphs endpoint'''
    paras = [i['text'] for i in paragraphs]
    paras = paras + paras
    paras = '\n\n'.join(paras)
    return paras


def create_highlighted_list(paragraphs_string, highlights_result, rank=0):
    """Creates list for argument `gr.HighlightedText()`"""
    # Max and min opacities to highlight to
    MAX_HIGHLIGHT = 1
    MIN_HIGHLIGHT = 0.25

    # Filter list for everything above the input rank
    highlights_result = [i for i in highlights_result if i['rank'] >= rank]

    # Get max/min ranks and find scale/shift we'll need so ranks are mapped to [MIN_HIGHLIGHT, MAX_HIGHLIGHT]
    max_rank = max([i['rank'] for i in highlights_result])
    min_rank = min([i['rank'] for i in highlights_result])
    scale = (MAX_HIGHLIGHT-MIN_HIGHLIGHT)/(max_rank-min_rank)
    shift = (MAX_HIGHLIGHT-max_rank*scale)

    # Isolate only highlight text and rank
    highlights_result = [(i['text'], i['rank']) for i in highlights_result]

    entities = []
    for highlight, rank in highlights_result:
        # For each highlight, find all starting character instances
        starts = [c.start() for c in re.finditer(highlight, paragraphs_string)]
        # Create list of locations for this highlight with entity value (highlight opacity) scaled properly
        # TODO: REPLACE WITH LIST COMPREHENSION
        e = [{"entity": rank*scale+shift,
              "start": start,
              "end": start + len(highlight)}
              for start in starts]
        entities += e

    # Create dictionary
    highlight_dict = {"text": paragraphs_string, "entities": entities}

    # Sort entities by start char - a bug in Gradio
    highlight_dict['entities'] = sorted(highlight_dict['entities'], key= lambda x: x['start'])

    return highlight_dict


def make_summary(chapters):
    """input = response.json()['chapters']"""
    html = "<div>"
    for chapter in chapters:
        html += "<details>" \
                f"<summary>{chapter['headline']}</summary>" \
                f"{chapter['summary']}" \
                "</details>"
    html += "</div>"
    return html
