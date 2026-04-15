import pickle
import typing as t


def encode(data: t.Any) -> bytes:
    return pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)


def decode(data: bytes) -> t.Any:
    return pickle.loads(data)
