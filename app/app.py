import json

import gradio as gr
import numpy as np
import plotly.express as px
import plotly
import plotly.graph_objects as go
import requests

from scipy.io.wavfile import write

from helpers import make_header, upload_file, request_transcript, make_polling_endpoint, wait_for_completion, \
    get_paragraphs, make_html_from_topics, make_paras_string, create_highlighted_list

# Converts Gradio checkboxes to AssemlbyAI header arguments
transcription_options_headers = {
    'Automatic Language Detection': 'language_detection',
    'Speaker Labels': 'speaker_labels',
    'Filter Profanity': 'filter_profanity',
}

audio_intelligence_headers = {
    'Summarization': 'auto_chapters',
    'Auto Highlights': 'auto_highlights',
    'Topic Detection': 'iab_categories',
    'Entity Detection': 'entity_detection',
    'Sentiment Analysis': 'sentiment_analysis',
    'PII Redaction': 'redact_pii',
    'Content Moderation': 'content_safety',
}

language_headers = {
    'Global English': 'en',
    'US English': 'en_us',
    'British English': 'en_uk',
    'Australian English': 'en_au',
    'Spanish': 'es',
    'French': 'fr',
    'German': 'de',
    'Italian': 'it',
    'Portuguese': 'pt',
    'Dutch': 'nl',
    'Hindi': 'hi',
    'Japanese': 'jp',
}


def change_audio_source(val, plot, file_data=None, mic_data=None):
    plot.update_traces(go.Line(y=[]))
    if val == "Audio File":
        print("FILE DATA", file_data)
        sample_rate, audio_data = file_data
        plot.update_traces(go.Line(y=audio_data, x=np.arange(len(audio_data)) / sample_rate))
        return [gr.Audio.update(visible=True),
                gr.Audio.update(visible=False),
                gr.Plot.update(plot),
                plot]
    elif val == "Record Audio":
        print("MIX DATA", mic_data)
        sample_rate, audio_data = mic_data
        plot.update_traces(go.Line(y=audio_data, x=np.arange(len(audio_data)) / sample_rate))

        return [gr.Audio.update(visible=False),
                gr.Audio.update(visible=True),
                gr.Plot.update(plot),
                plot]


# Function to change saved data and plot it when audio file is input or mic is recorded
def plot_data(audio_data, plot):
    if audio_data is None:
        sample_rate, audio_data = [0, np.array([])]
        plot.update_traces(go.Line(y=[]))
    else:
        sample_rate, audio_data = audio_data
        plot.update_traces(go.Line(y=audio_data, x=np.arange(len(audio_data))/sample_rate))


    return [gr.Plot.update(plot), [sample_rate, audio_data]]


# Set visibility of transcription option components when de/selected
def set_lang_vis(transcription_options):
    if 'Automatic Language Detection' in transcription_options:
        return [gr.Dropdown.update(visible=False),
                gr.Textbox.update(visible=True)]
    else:
        return [gr.Dropdown.update(visible=True),
                gr.Textbox.update(visible=False)]


# Verify which options are used, deselecting unavailable ones
def option_verif(language, selected_tran_opts, selected_audint_opts):

    not_available_tran, not_available_audint = get_unavailable_opts(language)

    current_tran_opts = list(set(selected_tran_opts) - set(not_available_tran))
    current_audint_opts = list(set(selected_audint_opts) - set(not_available_audint))

    return [gr.CheckboxGroup.update(current_tran_opts),
            gr.CheckboxGroup.update(current_audint_opts),
            current_tran_opts,
            current_audint_opts]


# Get tran/audint opts that are not available by language
def get_unavailable_opts(language):
    if language in ['Spanish', 'French', 'German', 'Portuguese']:
        not_available_tran = ['Speaker Labels']
        not_available_audint = ['PII Redaction', 'Auto Highlights', 'Sentiment Analysis', 'Summarization',
                                'Entity Detection']

    elif language in ['Italian', 'Dutch']:
        not_available_tran = ['Speaker Labels']
        not_available_audint = ['PII Redaction', 'Auto Highlights', 'Content Moderation', 'Topic Detection',
                                'Sentiment Analysis', 'Summarization', 'Entity Detection']

    elif language in ['Hindi', 'Japanese']:
        not_available_tran = ['Speaker Labels']
        not_available_audint = ['PII Redaction', 'Auto Highlights', 'Content Moderation', 'Topic Detection',
                                'Sentiment Analysis', 'Summarization', 'Entity Detection']

    else:
        not_available_tran = []
        not_available_audint = []

    return not_available_tran, not_available_audint


# When selecting new tran option, checks to make sure allowed by language and
# then adds to selected_tran_opts and updates
def tran_selected(language, transcription_options):
    unavailable, _ = get_unavailable_opts(language)
    selected_tran_opts = list(set(transcription_options) - set(unavailable))

    return [gr.CheckboxGroup.update(selected_tran_opts), selected_tran_opts]


# When selecting new audint option, checks to make sure allowed by language and
# then adds to selected_audint_opts and updates
def audint_selected(language, audio_intelligence_selector):
    _, unavailable = get_unavailable_opts(language)
    selected_audint_opts = list(set(audio_intelligence_selector) - set(unavailable))

    return [gr.CheckboxGroup.update(selected_audint_opts), selected_audint_opts]


def submit_to_AAI(api_key,
                  transcription_options,
                  audio_intelligence_selector,
                  language,
                  radio,
                  audio_file,
                  mic_recording):
    # comment out when want to full test, for now just loading json response
    '''
    header = make_header(api_key)


    true_dict = make_true_dict(transcription_options, audio_intelligence_selector)

    final_json, language = make_final_json(true_dict, language)
    final_json = {**true_dict, **final_json}


    if radio == "Audio File":
        audio_data = audio_file
    elif radio == "Record Audio":
        audio_data = mic_recording

    upload_url = upload_file(audio_data, header, is_file=False)
    transcript_response = request_transcript(upload_url, header, **final_json)
    print(transcript_response)
    polling_endpoint = make_polling_endpoint(transcript_response)
    wait_for_completion(polling_endpoint, header)

    r = requests.get(polling_endpoint, headers=header, json=final_json)
    '''
    with open('../response.json', 'r') as f:
        j = json.load(f)
    #print(json.dumps(j, indent=4, separators=(',', ':')))

    topics = j['iab_categories_result']['summary']
    html = make_html_from_topics(topics)

    #endpoint = f"https://api.assemblyai.com/v2/transcript/{j['id']}/paragraphs"
    #highlights = requests.get(endpoint, headers=header)
    #highlights = highlights.json()['paragraphs']
    #paras = make_paras_string(highlights)
    # Load from file instead so dont have to use aai key
    with open("../paras.txt", 'r') as f:
        paras = f.read()

    highlight_dict = create_highlighted_list(paras, j['auto_highlights_result']['results'])

    print(html)

    #TODO Figure out how to parse the data and display it well in Gradio
    #paragraphs = get_paragraphs(polling_endpoint, header)

    #endpoints = ["redacted-audio", ]
    #r = []
    return [language, html, highlight_dict]


# Given transcription / audio intelligence options, create a dictionary to be used in AAI JSON
def make_true_dict(transcription_options, audio_intelligence_selector):
    aai_tran_keys = [transcription_options_headers[elt] for elt in transcription_options]
    aai_audint_keys = [audio_intelligence_headers[elt] for elt in audio_intelligence_selector]

    aai_tran_dict = {key: 'true' for key in aai_tran_keys}
    aai_audint_dict = {key: 'true' for key in aai_audint_keys}

    return {**aai_tran_dict, **aai_audint_dict}


# Takes in a dictionary of AAI API options and adds all required other kwargs
def make_final_json(true_dict, language):
    if 'language_detection' not in true_dict:
        # TODO handle this in a better way
        if language is None:
            language = "US English"
        true_dict = {**true_dict, 'language_code': language_headers[language]}
    # TODO: Allow selection of PII policies
    if 'redact_pii' in true_dict:
        true_dict = {**true_dict, 'redact_pii_policies': ['drug', 'injury', 'person_name']}
    print(true_dict)
    return true_dict, language


with open('styles.css', 'r') as f:
    css = f.read()


with gr.Blocks(css=css) as demo:
    gr.HTML('<img src="file/images/logo.png">')

    api_key = gr.Textbox(label="", elem_id="pw")

    plot = gr.State(px.line(labels={'x':'Time (s)', 'y':''}))
    file_data = gr.State([1, [0]])
    mic_data = gr.State([1, [0]])

    # Options that the user wants
    selected_tran_opts = gr.State([])
    selected_audint_opts = gr.State([])

    # Current options = selected options - unavailable for specified language
    current_tran_opts = gr.State([])
    current_audint_opts = gr.State([])

    # Dictionary for selected items
    final_header = gr.State({})


    radio = gr.Radio(["Audio File", "Record Audio"], label="Audio Source", value="Audio File")
    with gr.Box():
        audio_file = gr.Audio(interactive=True)
        mic_recording = gr.Audio(source="microphone", visible=False, interactive=True)

    print(plot.value)
    audio_wave = gr.Plot(plot.value)

    transcription_options = gr.CheckboxGroup(
        list(transcription_options_headers.keys()),
        label="Transcription Options",
        value=["Automatic Language Detection"]
    )

    w = "<div>" \
        "<p>WARNING: Automatic Language Detection not available for Hindi or Japanese. For best results on non-US " \
        "English audio, specify the dialect instead of using Automatic Language Detection</p>" \
        "<p>WARNING: Some Audio Intelligence features are not available in some languages. See " \
        "<a href='https://airtable.com/shr53TWU5reXkAmt2/tblf7O4cffFndmsCH?backgroundColor=green'>here</a> " \
        "for more details.</p>" \
        "</div>"
    auto_lang_detect_warning = gr.HTML(w)

    audio_intelligence_selector = gr.CheckboxGroup(
        list(audio_intelligence_headers.keys()),
        label='Audio Intelligence Options', interactive=True
    )

    language = gr.Dropdown(
        list(language_headers.keys()),
        label="Language Specification",
        value='US English',
        visible=False,
    )
    submit = gr.Button('Submit')

    #gr.HighlightedText(value=[('hello', 1), ('asdasdd', 0), ('asasd', 1), ('asasd', 2)]).style(color_map={
    #    '0': '#FFFFFF', '1' : '#FF00FF', '2': '#FF0F0F'})

    with gr.Tab('Transcription'):
        trans_tab = gr.Textbox(placeholder="Your transcription will appear here ...", lines=5, max_lines=25)
    with gr.Tab('Auto Highlights'):
        highlights = gr.HighlightedText()
    with gr.Tab('Summary'):
        gr.Textbox("Your transcription will appear here ...", interactive=True)
    with gr.Tab("Detected Topics"):
        topics_tab = gr.HTML()

    ####################################### Functionality ######################################################

    # Changing audio source changes Audio input component
    radio.change(fn=change_audio_source,
                 inputs=[
                     radio,
                     plot,
                     file_data,
                     mic_data],
                 outputs=[
                     audio_file,
                     mic_recording,
                     audio_wave,
                     plot])

    # Inputting audio updates plot
    #for component in [audio_file, mic_recording]:
    #    getattr(component, 'change')(fn=plot_audio, inputs=component, outputs=audio_wave)
    audio_file.change(fn=plot_data,
                      inputs=[audio_file, plot],
                      outputs=[audio_wave, file_data]
                      )
    mic_recording.change(fn=plot_data,
                         inputs=[mic_recording, plot],
                         outputs=[audio_wave, mic_data])

    # Deselecting Automatic Language Detection shows Language Selector
    transcription_options.change(
        fn=set_lang_vis,
        inputs=transcription_options,
        outputs=[language, auto_lang_detect_warning])

    # Changing language deselects certain Tran / Audio Intelligence options
    language.change(
        fn=option_verif,
        inputs=[language,
                selected_tran_opts,
                selected_audint_opts],
        outputs=[transcription_options, audio_intelligence_selector, current_tran_opts, current_audint_opts]
    )

    # Selecting Tran options adds it to selected if language allows it
    transcription_options.change(
        fn=tran_selected,
        inputs=[language, transcription_options],
        outputs=[transcription_options, selected_tran_opts]
    )


    # Selecting audio intelligence options adds it to selected if language allows it
    audio_intelligence_selector.change(
        fn=audint_selected,
        inputs=[language, audio_intelligence_selector],
        outputs=[audio_intelligence_selector, selected_audint_opts]
    )

    submit.click(fn=submit_to_AAI,
                 inputs=[api_key,
                         transcription_options,
                         audio_intelligence_selector,
                         language,
                         radio,
                         audio_file,
                         mic_recording],
                 outputs=[language, topics_tab, highlights])

demo.launch(share=True)