import pydantic

type Encoder = pydantic.EncoderProtocol
def f(value: pydantic.ConfigDict) -> bool:
    return False
