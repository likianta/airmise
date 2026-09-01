import pickle
import typing as tp


def encode(data: tp.Any) -> bytes:
    return pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)


def decode(data: bytes) -> tp.Any:
    return pickle.loads(data)
