"""Small reproducible parameter grid; scoring waits for real app captures."""

from inkbridge.optimization.parameters import EncoderParameters


def default_candidates() -> list[EncoderParameters]:
    return [EncoderParameters(), EncoderParameters(translate_x=-2),
            EncoderParameters(translate_x=2), EncoderParameters(translate_y=-2),
            EncoderParameters(translate_y=2), EncoderParameters(scale_x=0.98, scale_y=0.98),
            EncoderParameters(scale_x=1.02, scale_y=1.02),
            EncoderParameters(width_scale=0.9), EncoderParameters(width_scale=1.1)]
