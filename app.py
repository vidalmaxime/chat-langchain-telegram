import os
from typing import Optional, Tuple

import gradio as gr
import pickle
from query_data import get_chain
from ingest_data import embed_chat
from threading import Lock


def click_embed(file):
    """Embed Telegram chat.
       """
    embed_chat(file.name)
    with open("vectorstore.pkl", "rb") as f:
        vectorstore = pickle.load(f)
    chain = get_chain(vectorstore)
    return chain, gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(
        visible=True), gr.update(visible=True), gr.update(
        visible=True), gr.update(visible=True)


def set_openai_api_key(api_key: str):
    """Set the api key.
    """
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key


def upload_file(file_obj):
    return file_obj


class ChatWrapper:

    def __init__(self):
        self.lock = Lock()

    def __call__(
            self, api_key: str, inp: str, history: Optional[Tuple[str, str]], chain
    ):
        """Execute the chat functionality."""
        self.lock.acquire()
        try:
            history = history or []
            # If chain is None, that is because no API key was provided.
            if chain is None:
                history.append((inp, "Please paste your OpenAI key to use"))
                return history, history
            # Set OpenAI key
            import openai
            openai.api_key = api_key
            # Run chain and append input.
            output = chain({"question": inp, "chat_history": history})["answer"]
            history.append((inp, output))
        except Exception as e:
            raise e
        finally:
            self.lock.release()
        return history, history


chat = ChatWrapper()

block = gr.Blocks(css=".gradio-container {background-color: lightgray}")

with block:
    with gr.Row():
        gr.Markdown("<h3><center>Telegram Chat Chat</center></h3>")

        openai_api_key_textbox = gr.Textbox(
            placeholder="Paste your OpenAI API key (sk-...)",
            show_label=False,
            lines=1,
            type="password",
            visible=True
        )
        telegram_chat_file = gr.File(file_count="single", file_types=["json"], interactive=True, show_label=True,
                                     visible=True,
                                     label="Telegram chat history exported .json file")
        embed_button = gr.Button("Create embeddings", visible=True)

    chatbot = gr.Chatbot(visible=False)

    with gr.Row():
        message = gr.Textbox(
            label="What's your question?",
            placeholder="Ask questions about your Telegram conversation",
            lines=1,
            visible=False
        )
        submit = gr.Button(value="Send", variant="secondary", visible=False).style(full_width=False)
    with gr.Row(visible=False) as examples_row:
        gr.Examples(
            examples=[
                "When was [your name] happy and how does it show?",
                "How could [your name] have been more compassionate?",
                "What triggers [your name] instantly?",
            ],
            inputs=message,
        )

    gr.HTML(
        "<center>Powered by <a href='https://github.com/hwchase17/langchain'>LangChain 🦜️🔗</a></center>"
    )

    state = gr.State()
    agent_state = gr.State()

    embed_button.click(click_embed, inputs=[telegram_chat_file],
                       outputs=[agent_state, openai_api_key_textbox, telegram_chat_file, embed_button, chatbot, message,
                                submit, examples_row])

    submit.click(chat, inputs=[openai_api_key_textbox, message, state, agent_state], outputs=[chatbot, state])
    print(agent_state)
    message.submit(chat, inputs=[openai_api_key_textbox, message, state, agent_state], outputs=[chatbot, state])

    openai_api_key_textbox.change(
        set_openai_api_key,
        inputs=[openai_api_key_textbox],
    )

block.launch(debug=True)
