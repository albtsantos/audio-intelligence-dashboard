import gradio as gr


def change_audio_source(val):
    if val == "Audio File":
        return [gr.Audio.update(visible=True), gr.Image.update(visible=False)]
    elif val == "Record Audio":
        return [gr.Audio.update(visible=False), gr.Image.update(visible=True)]


def fn2(val):
    return val


with gr.Blocks() as demo:
    radio = gr.Radio(["Audio File", "Record Audio"], label="Audio Source", value="Audio File")
    with gr.Box():
        audio_file = gr.Audio(interactive=True)
        mic_recording = gr.Audio(source="microphone", visible=False, interactive=True)

    number = gr.Textbox()
    # audio_wave = gr.Plot()

    radio.change(fn=change_audio_source, inputs=radio, outputs=[audio_file, mic_recording])
    for component in [audio_file, mic_recording]:
        getattr(component, 'change')(fn=fn2, inputs=component, outputs=number)

demo.launch()