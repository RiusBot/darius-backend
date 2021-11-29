from enum import Enum


class ChannelType(str, Enum):
    ROSE = "ROSE"
    PERPETUAL = "PERPETUAL"
    WHALE = "WHALE"
    DAILYSCALP = "DAILYSCALP"
    TEST2 = "test2"
    TEST = "test"
    DARIUS = "darius"
