import gradio as gr
import numpy as np
import plotly.express as px
import plotly
import plotly.graph_objects as go

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

# Options that the use wants
selected_tran_opts = []
selected_audint_opts = []

# Current options = selected options - unavailable for specified language
current_tran_opts = []
current_audint_opts = []

plot = px.line(labels={'x':'Time (s)', 'y':''})
file_data = [1, [0]]
mic_data = [1, [0]]



def change_audio_source(val):
    global plot
    plot.update_traces(go.Line(y=[]))
    if val == "Audio File":
        global file_data
        sample_rate, audio_data = file_data
        plot.update_traces(go.Line(y=audio_data, x=np.arange(len(audio_data)) / sample_rate))
        return [gr.Audio.update(visible=True), gr.Audio.update(visible=False), gr.Plot.update(plot)]
    elif val == "Record Audio":
        global mic_data
        sample_rate, audio_data = mic_data
        plot.update_traces(go.Line(y=audio_data, x=np.arange(len(audio_data)) / sample_rate))

        return [gr.Audio.update(visible=False), gr.Audio.update(visible=True), gr.Plot.update(plot)]


# Plot audio
def plot_file_data(audio_data):
    global file_data
    global plot
    file_data = audio_data

    if audio_data is None:
        file_data = [1, [0]]
        plot.update_traces(go.Line(y=[]))
    else:
        sample_rate, audio_data = audio_data
        plot.update_traces(go.Line(y=audio_data, x=np.arange(len(audio_data))/sample_rate))
    return gr.Plot.update(plot)


# Plot audio
def plot_mic_data(audio_data):
    global mic_data
    global plot
    mic_data = audio_data

    if audio_data is None:
        mic_data = [1, [0]]
        plot.update_traces(go.Line(y=[]))
    else:
        sample_rate, audio_data = audio_data
        plot.update_traces(go.Line(y=audio_data, x=np.arange(len(audio_data)) / sample_rate))
    return gr.Plot.update(plot)


# Set visibility of transcription option components when de/selected
def set_lang_vis(transcription_options):
    if 'Automatic Language Detection' in transcription_options:
        return [gr.Dropdown.update(visible=False),
                gr.Textbox.update(visible=True)]
    else:
        return [gr.Dropdown.update(visible=True),
                gr.Textbox.update(visible=False)]


# Verify which options are used, deselecting unavailable ones
def option_verif(language, transcription_options, audio_intelligence_selector):
    global selected_tran_opts
    global selected_audint_opts
    global current_tran_opts
    global current_audint_opts

    not_available_tran, not_available_audint = get_unavailable_opts(language)

    current_tran_opts = list(set(selected_tran_opts) - set(not_available_tran))
    current_audint_opts = list(set(selected_audint_opts) - set(not_available_audint))

    return [gr.CheckboxGroup.update(current_tran_opts), gr.CheckboxGroup.update(current_audint_opts)]


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


# When selecting new audint option, checks to make sure allowed by language and
# then adds to selected_audint_opts and updates
def audint_selected(language, audio_intelligence_selector):
    global selected_audint_opts

    _, unavailable = get_unavailable_opts(language)
    selected_audint_opts = list(set(audio_intelligence_selector) - set(unavailable))

    return gr.CheckboxGroup.update(selected_audint_opts)

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

    audio_wave = gr.Plot(plot)

    transcription_options = gr.CheckboxGroup(
        list(transcription_options_headers.keys()),
        label="Transcription Options",
        value=["Automatic Language Detection"]
    )

    auto_lang_detect_warning = gr.HTML("<p>WARNING: Automatic Language Detection not available for Hindi or Japanese. "
                                       "For best results on non-US English audio, specify the dialect instead of using "
                                       "Automatic Language Detection</p>")

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
    radio.change(fn=change_audio_source, inputs=radio, outputs=[audio_file, mic_recording, audio_wave])

    # Inputting audio updates plot
    #for component in [audio_file, mic_recording]:
    #    getattr(component, 'change')(fn=plot_audio, inputs=component, outputs=audio_wave)
    audio_file.change(fn=plot_file_data, inputs=audio_file, outputs=audio_wave)
    mic_recording.change(fn=plot_mic_data, inputs=mic_recording, outputs=audio_wave)

    # Deselecting Automatic Language Detection shows Language Selector
    transcription_options.change(
        fn=set_lang_vis,
        inputs=transcription_options,
        outputs=[language, auto_lang_detect_warning])

    # Changing language deselects certain Audio Intelligence options
    language.change(
        fn=option_verif,
        inputs=[language, transcription_options, audio_intelligence_selector],
        outputs=[transcription_options, audio_intelligence_selector]
    )

    # Selecting audio intelligence options adds it to selected if language allows it
    audio_intelligence_selector.change(
        fn=audint_selected,
        inputs=[language, audio_intelligence_selector],
        outputs=audio_intelligence_selector
    )


    #submit.click(fn=make_true_dict, inputs=[transcription_options, audio_intelligence_selector], outputs=None)

demo.launch()