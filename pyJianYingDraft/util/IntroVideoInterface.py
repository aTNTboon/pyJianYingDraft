from abc import ABC, abstractmethod


class IntroVideoInterface(ABC):


    @abstractmethod
    def make_intro_video(self, duration: int, start_time: float, track: str) -> None:
        raise NotImplementedError()