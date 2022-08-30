import gradio as gr
import plotly.express as px

DICT = {}

# Converts Gradio checkboxes to AssemlbyAI header arguments
transcription_options_headers = {
        'Speaker Labels': 'speaker_labels',
        'Language': 'language_code',
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
def change_audio_source(val):
    if val == "Audio File":
        return [gr.Audio.update(visible=True), gr.Image.update(visible=False)]
    elif val == "Record Audio":
        return [gr.Audio.update(visible=False), gr.Image.update(visible=True)]


def plot_audio(val):
    audio_data = val[1]
    #fig = plt.Figure()
    #plt.plot(audio_data)
    fig = px.line(audio_data)
    return fig

def make_true_dict(transcription_options, audio_intelligence_selector):
    global DICT
    print(DICT)
    aai_tran_keys = [transcription_options_headers[elt] for elt in transcription_options]
    aai_audint_keys = [audio_intelligence_headers[elt] for elt in audio_intelligence_selector]

    aai_tran_dict = {key: True for key in aai_tran_keys}
    aai_audint_dict = {key: True for key in aai_audint_keys}

    make_final_header = {**aai_tran_dict, **aai_audint_dict}
    DICT = make_final_header

with gr.Blocks() as demo:
    radio = gr.Radio(["Audio File", "Record Audio"], label="Audio Source", value="Audio File")
    with gr.Box():
        audio_file = gr.Audio(interactive=True)
        mic_recording = gr.Audio(source="microphone", visible=False, interactive=True)

    audio_wave = gr.Plot()

    transcription_options = gr.Checkboxgroup([
        'Speaker Labels',
        'Language',
        'Filter Profanity',
    ])

    audio_intelligence_selector = gr.Checkboxgroup([
        'Summarization',
        'Auto Highlights',
        'Topic Detection',
        'Entity Detection',
        'Sentiment Analysis',
        'PII Redaction',
        'Content Moderation',
    ])

    submit = gr.Button('Submit')


    ####################################### Functionality ######################################################

    # Changing audio source changes Audio input component
    radio.change(fn=change_audio_source, inputs=radio, outputs=[audio_file, mic_recording])

    # Inputting audio updates plot
    for component in [audio_file, mic_recording]:
        getattr(component, 'change')(fn=plot_audio, inputs=component, outputs=audio_wave)

    submit.click(fn=make_true_dict, inputs=[transcription_options, audio_intelligence_selector], outputs=None)

demo.launch()