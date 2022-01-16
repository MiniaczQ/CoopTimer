from abc import ABC, abstractmethod
from typing import Callable
import re


class LineCheckBase(ABC):
    @abstractmethod
    def check(self, string: str) -> None: ...

class LineChecker(LineCheckBase):
    callback: Callable[[], None]
    message: str

    def __init__(self, callback: Callable[[], None], message: str) -> None:
        self.callback = callback
        self.message = message

    def check(self, string: str) -> None:
        if self.message in string:
            self.callback()

class RELineChecker(LineCheckBase):
    callback: Callable[[], None]
    pattern: re.Pattern

    def __init__(self, callback: Callable[[], None], pattern_str: str) -> None:
        self.callback = callback
        self.pattern = re.compile(pattern_str)

    def check(self, string: str) -> None:
        if self.pattern.match(string):
            self.callback()