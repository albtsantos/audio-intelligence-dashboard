import gradio as gr
import plotly.express as px

DICT = {}

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

def change_audio_source(val):
    if val == "Audio File":
        return [gr.Audio.update(visible=True), gr.Image.update(visible=False)]
    elif val == "Record Audio":
        return [gr.Audio.update(visible=False), gr.Image.update(visible=True)]


# Plot audio
def plot_audio(val):
    audio_data = val[1]
    fig = px.line(audio_data)
    return fig


# Set visibility of transcription option components when de/selected
def set_lang_vis(transcription_options):
    if 'Automatic Language Detection' in transcription_options:
        return gr.Dropdown.update(visible=False)
    else:
        return gr.Dropdown.update(visible=True)


def option_verif(language, transcription_options, audio_intelligence_selector):
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

    return [gr.CheckboxGroup.update(list(set(transcription_options) - set(not_available_tran))),
            gr.CheckboxGroup.update(list(set(audio_intelligence_selector) - set(not_available_audint)))]


'''
def make_true_dict(transcription_options, audio_intelligence_selector):
    global DICT
    print(DICT)
    aai_tran_keys = [transcription_options_headers[elt] for elt in transcription_options]
    aai_audint_keys = [audio_intelligence_headers[elt] for elt in audio_intelligence_selector]

    aai_tran_dict = {key: True for key in aai_tran_keys}
    aai_audint_dict = {key: True for key in aai_audint_keys}

    make_final_header = {**aai_tran_dict, **aai_audint_dict}
    DICT = make_final_header
'''

with gr.Blocks() as demo:
    radio = gr.Radio(["Audio File", "Record Audio"], label="Audio Source", value="Audio File")
    with gr.Box():
        audio_file = gr.Audio(interactive=True)
        mic_recording = gr.Audio(source="microphone", visible=False, interactive=True)

    audio_wave = gr.Plot()

    transcription_options = gr.CheckboxGroup(
        list(transcription_options_headers.keys()),
        label="Transcription Options",
        value=["Automatic Language Detection"]
    )

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


    ####################################### Functionality ######################################################

    # Changing audio source changes Audio input component
    radio.change(fn=change_audio_source, inputs=radio, outputs=[audio_file, mic_recording])

    # Inputting audio updates plot
    for component in [audio_file, mic_recording]:
        getattr(component, 'change')(fn=plot_audio, inputs=component, outputs=audio_wave)

    # Deselecting Automatic Language Detection shows Language Selector
    transcription_options.change(
        fn=set_lang_vis,
        inputs=transcription_options,
        outputs=language)

    # Changing language deselects certain Audio Intelligence options
    language.change(
        fn=option_verif,
        inputs=[language, transcription_options, audio_intelligence_selector],
        outputs=[transcription_options, audio_intelligence_selector]
    )


    #submit.click(fn=make_true_dict, inputs=[transcription_options, audio_intelligence_selector], outputs=None)

demo.launch()