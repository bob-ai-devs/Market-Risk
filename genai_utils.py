"""
Thin wrapper around the new `google-genai` SDK (the `genai` package),
replacing the old `google.generativeai` usage from the Colab/Flask version.

Docs: https://ai.google.dev/gemini-api/docs/sdks
"""

from google import genai

DEFAULT_MODEL = "gemini-flash-lite-latest"


def get_client(api_key: str) -> genai.Client:
    """Create a genai Client. Cache this at the call site (e.g. st.cache_resource)."""
    if not api_key:
        raise ValueError("A Gemini API key is required (set GEMINI_API_KEY in secrets).")
    return genai.Client(api_key=api_key)


def list_model_names(client: genai.Client):
    """Return a sorted list of model names usable with generate_content."""
    # names = []
    # try:
    #     for model in client.models.list():
    #         # Only keep models that support text generation.
    #         actions = getattr(model, "supported_actions", None)
    #         if actions is None or "generateContent" in actions:
    #             names.append(model.name.split("/")[-1])
    # except Exception:
    #     pass
    # return sorted(set(names))
    return set(['gemini-flash-lite-latest', 'gemini-flash-latest'])


def generate_text(client: genai.Client, prompt: str, model: str = "") -> str:
    model_name = model or DEFAULT_MODEL
    response = client.models.generate_content(model=model_name, contents=prompt)
    return response.text or ""
