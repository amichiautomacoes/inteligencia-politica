"""Consistent editorial formatting for DNA profile labels."""


def sentence_label(value: object) -> str:
    text = str(value).strip()
    if not text or text in {"Nao informado", "Não informado"}:
        return "Não informado"
    if text.isupper():
        text = text.lower()
    return text[:1].upper() + text[1:]
