import os

from cursor_sdk import Agent, LocalAgentOptions

from cursor_config import activation_error, load_link_config


class CursorAgent:

    def __init__(self):
        self.agent = Agent.create(model="composer-2.5",
            api_key="crsr_key",
            local=LocalAgentOptions(cwd=os.getcwd()),
        )