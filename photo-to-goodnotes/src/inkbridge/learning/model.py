"""Future geometry-correction model interface; no neural network defined."""

from typing import Protocol

from inkbridge.core.models import InkDocument


class GeometryCorrectionModel(Protocol):
    def predict(self, document: InkDocument) -> InkDocument: ...
