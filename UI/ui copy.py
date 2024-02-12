import gradio as gr
import os
import time
from huggingface_hub import InferenceClient
import requests

# Chatbot demo with multimodal input (text, markdown, LaTeX, code blocks, image, audio, & video). Plus shows support for streaming text.
base_url = "http://localhost:8090"
client = InferenceClient(model=f'{base_url}/llm_service/')

def inference(message):
    message[-1][1] = ""
    for token in client.text_generation(message[-1][0], max_new_tokens=500, stream=True):
        message[-1][1] += token
        yield message

def add_text(history, text):
    history = history + [(text, None)]
    return history, gr.Textbox(value="", interactive=False)


def check_model_status():
    x = requests.get(f'{base_url}/check_llm_service')
    return x.text

def request_llm():
    x = requests.get(f'{base_url}/demand_llm_service')
    return x.text


with gr.Blocks() as demo:
        
    btn_demandLLM = gr.Button("Request LLM")
    btn_checkLLM = gr.Button("Check LLM")
    out_checkLLM = gr.Textbox(label="LLM-Status")
    btn_demandLLM.click(fn=request_llm, outputs=out_checkLLM, api_name="greet").then(fn=check_model_status, outputs=out_checkLLM, api_name="greet")
    btn_checkLLM.click(fn=check_model_status, outputs=out_checkLLM, api_name="greet")


    chatbot = gr.Chatbot(
        [],
        elem_id="chatbot",
        bubble_full_width=False
    )

    with gr.Row():
        txt = gr.Textbox(
            scale=4,
            show_label=False,
            placeholder="Enter text and press enter!",
            container=False,
        )
        btn_submit = gr.Button("Submit")
    
    with gr.Row():
        btn_retry = gr.Button("Retry")
        btn_clear = gr.Button("Clear")

    txt_msg = txt.submit(add_text, [chatbot, txt], [chatbot, txt], queue=False).then(
        inference, chatbot, chatbot, api_name="bot_response"
    )
    txt_msg.then(lambda: gr.Textbox(interactive=True), None, [txt], queue=False)
    txt_msg = btn_submit.click(add_text, [chatbot, txt], [chatbot, txt], queue=False).then(
        inference, chatbot, chatbot, api_name="bot_response"
    )
    txt_msg.then(lambda: gr.Textbox(interactive=True), None, [txt], queue=False)


demo.queue()
demo.launch()
