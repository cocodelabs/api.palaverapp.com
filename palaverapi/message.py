# Adapted from https://github.com/kylef/irctk/blob/master/irctk/message.py

from typing import List, Optional


class Message:
    @classmethod
    def parse(cls, string: str) -> 'Message':
        prefix = None
        parameters = []

        if string.startswith('@'):
            _, string = string[1:].split(' ', 1)

        if string.startswith(':'):
            prefix, string = string.split(' ', 1)
            prefix = prefix[1:]

        if ' ' in string:
            command, string = string.split(' ', 1)
        else:
            command = string
            string = ''

        while len(string) != 0:
            if string[0] == ':':
                parameters.append(string[1:])
                string = ''
            elif ' ' in string:
                parameter, string = string.split(' ', 1)
                parameters.append(parameter)
            else:
                parameters.append(string)
                string = ''

        return cls(prefix, command, parameters)

    def __init__(
        self,
        prefix: str = None,
        command: str = '',
        parameters: List[str] = None,
    ):
        self.prefix = prefix
        self.command = command
        self.parameters = parameters or []

    def get(self, index: int) -> Optional[str]:
        if index >= len(self.parameters):
            return None

        return self.parameters[index]
