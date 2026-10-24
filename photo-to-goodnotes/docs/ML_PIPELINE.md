# InkSight integration

As checked on 2026-10-21, [upstream InkSight](https://github.com/google-research/inksight) recommends cloning and running `uv sync` then `uv run jupyter notebook colab.ipynb`, or creating its Conda environment. It publishes Small-p weights on [Hugging Face](https://huggingface.co/Derendering/InkSight-Small-p). Acquire weights separately after reviewing their terms; setup scripts do not download them.

The future worker will accept an image path, model path, output path, and request ID in JSON, then write native predicted trajectories and a response JSON. The core adapter will parse the actual worker output and emit `InkDocument`. `inkml_parser.py` is reserved for InkML only if the selected inference path emits it; the notebook's exact output must be confirmed before implementing a parser. Keep TensorFlow in the upstream worker environment and PyTorch in the optional training group.

`setup_inksight` scripts only validate `uv` and an existing local clone, then run upstream `uv sync --locked` in that clone. Clone manually to `external/inksight` so the repository and revision are explicit. On Windows, the upstream CUDA extra is Linux oriented; use WSL2/Linux for GPU work. A subprocess JSON boundary avoids shared interpreter dependency conflicts.
