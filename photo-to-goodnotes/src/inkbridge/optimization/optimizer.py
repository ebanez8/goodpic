"""Future SciPy/CMA-ES candidate search."""

from typing import Protocol

from inkbridge.optimization.parameters import EncoderParameters


class CandidateGenerator(Protocol):
    def propose(self, history: list[tuple[EncoderParameters, float]]) -> EncoderParameters: ...
