"""HTML presentation of electoral clusters inside the DNA subsection."""
from __future__ import annotations

import html

import pandas as pd

from pages.dna_copy import sentence_label


def cluster_cards_html(profiles: list[dict]) -> str:
    esc = lambda value: html.escape(str(value), quote=True)
    percent = lambda value: f"{value:.2f}%".replace(".", ",")
    classes = ["BASE ELEITORAL", "ELEITOR CONSOLIDADO", "ELEITOR EMERGENTE"]
    classes += sorted({p["classification"] for p in profiles} - set(classes))
    summary = []
    cards = []
    for classification in classes:
        members = [p for p in profiles if p["classification"] == classification]
        share = sum(p["share"] for p in members)
        summary.append(
            f'<div class="dna-base-summary-item"><span>{esc(sentence_label(classification))}</span>'
            f'<strong>{percent(share) if members else "—"}</strong>'
            f'<small>{"da votação do candidato" if members else "Sem perfil nesta classificação"}</small></div>'
        )
        for profile in sorted(members, key=lambda p: p["share"], reverse=True):
            bars = []
            for label, category, value in profile["demographics"]:
                valid = pd.notna(value) and 0 <= value <= 100
                bar = (
                    f'<div class="dna-base-track" role="meter" aria-label="{esc(label)}: {esc(category)}" '
                    f'aria-valuemin="0" aria-valuemax="100" aria-valuenow="{value:.4f}">'
                    f'<span style="width:{value:.4f}%"></span></div>'
                    if valid else ""
                )
                bars.append(
                    f'<div class="dna-base-demographic"><div><span>{esc(label)}</span>'
                    f'<strong>{percent(value) if valid else "Não informado"}</strong></div>'
                    f'<p>{esc(sentence_label(category))}</p>{bar}</div>'
                )
            votes = f'{profile["votes"]:,.0f}'.replace(",", ".")
            cards.append(f'''<details class="dna-base-profile">
                <summary class="dna-base-profile-summary">
                    <span class="dna-base-profile-heading">
                        <span class="dna-base-classification">{esc(sentence_label(classification))} · ICP {esc(profile["id"])}</span>
                        <span class="dna-base-persona">{esc(sentence_label(profile["persona"]))}</span>
                    </span>
                    <span class="dna-base-profile-result"><strong>{percent(profile["share"])}</strong><small>da votação do candidato · {votes} votos</small></span>
                    <span class="dna-base-chevron" aria-hidden="true"></span>
                </summary>
                <div class="dna-base-profile-content">
                    <div class="dna-base-demographics">{''.join(bars)}</div>
                    <p class="dna-base-note">Percentuais das categorias dominantes dentro deste perfil.</p>
                    <div class="dna-base-reason"><strong>Leitura estratégica</strong><p>{esc(profile["reason"])}</p></div>
                </div>
            </details>''')
    content = (
        f'<div class="dna-base-summary">{"".join(summary)}</div><div class="dna-base-list">{"".join(cards)}</div>'
        if profiles else '<p class="dna-base-note">Perfis de clusters indisponíveis para este candidato.</p>'
    )
    return f'''<style>
    .dna-base-section {{margin:28px 0;padding:30px;border:1px solid rgba(96,165,250,.3);border-radius:20px;background:linear-gradient(135deg,rgba(11,31,77,.76),rgba(7,24,54,.68));color:#eaf2ff;box-shadow:0 12px 30px rgba(0,0,0,.14)}}
    .dna-base-heading {{border-bottom:1px solid rgba(147,197,253,.2);padding-bottom:20px}}
    .dna-base-section h3 {{font-size:clamp(1.55rem,2.4vw,2rem);line-height:1.15;margin:0 0 10px;color:#f8fbff;letter-spacing:.025em;font-weight:800}}
    .dna-base-intro {{color:#b7c7e6;font-size:1rem;line-height:1.5;margin:0;max-width:70ch}}
    .dna-base-note {{color:#b7c7e6;font-size:.86rem;line-height:1.5}}
    .dna-base-summary {{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin:22px 0 26px}}
    .dna-base-summary-item {{border-left:3px solid #60a5fa;padding:8px 14px;display:flex;flex-direction:column;gap:5px}}
    .dna-base-summary-item span,.dna-base-classification {{font-size:.75rem;font-weight:700;letter-spacing:.05em;color:#b7c7e6}}
    .dna-base-summary-item strong {{font-size:1.7rem;color:#f8fbff}}
    .dna-base-summary-item small {{color:#b7c7e6}}
    .dna-base-list {{display:grid;gap:12px}}
    .dna-base-profile {{min-width:0;border:1px solid rgba(96,165,250,.23);border-radius:14px;background:rgba(15,42,80,.5);overflow-wrap:anywhere}}
    .dna-base-profile[open] {{border-color:rgba(147,197,253,.5);background:rgba(15,42,80,.7)}}
    .dna-base-profile-summary {{display:flex;align-items:center;gap:18px;padding:18px 22px;cursor:pointer;list-style:none}}
    .dna-base-profile-summary::-webkit-details-marker {{display:none}}
    .dna-base-profile-summary:focus-visible {{outline:2px solid #93c5fd;outline-offset:-3px;border-radius:14px}}
    .dna-base-profile-summary:hover {{background:rgba(96,165,250,.08)}}
    .dna-base-profile-heading {{display:flex;flex:1;min-width:0;flex-direction:column;gap:6px}}
    .dna-base-persona {{font-size:1.08rem;font-weight:700;line-height:1.35;color:#f8fbff}}
    .dna-base-profile-result {{display:flex;flex-direction:column;align-items:flex-end;gap:3px;white-space:nowrap}}
    .dna-base-profile-result strong {{font-size:1.45rem;color:#93c5fd}}
    .dna-base-profile-result small {{font-size:.78rem;color:#b7c7e6}}
    .dna-base-chevron {{width:9px;height:9px;flex:none;border-right:2px solid #93c5fd;border-bottom:2px solid #93c5fd;transform:rotate(45deg);transition:transform .2s;margin:0 4px 5px}}
    .dna-base-profile[open] .dna-base-chevron {{transform:rotate(225deg);margin-bottom:0;margin-top:5px}}
    .dna-base-profile-content {{padding:20px 22px 22px;border-top:1px solid rgba(96,165,250,.2)}}
    .dna-base-demographics {{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}
    .dna-base-demographic>div:first-child {{display:flex;justify-content:space-between;gap:8px;font-size:.8rem}}
    .dna-base-demographic p {{font-size:.9rem;margin:5px 0 9px;line-height:1.4}}
    .dna-base-track {{height:6px;border-radius:4px;background:rgba(147,197,253,.15);overflow:hidden}}
    .dna-base-track span {{height:100%;display:block;background:#60a5fa;border-radius:4px}}
    .dna-base-reason {{border-top:1px solid rgba(96,165,250,.2);padding-top:16px;font-size:.9rem;line-height:1.6}}
    .dna-base-reason p {{margin:8px 0 0;color:#b7c7e6}}
    @media(max-width:700px) {{.dna-base-profile-summary {{align-items:flex-start;flex-wrap:wrap;gap:12px}}.dna-base-profile-result {{align-items:flex-start;white-space:normal}}.dna-base-chevron {{margin-left:auto}}}}
    @media(max-width:600px) {{.dna-base-section {{padding:18px}}.dna-base-summary,.dna-base-demographics {{grid-template-columns:1fr}}.dna-base-profile-summary {{padding:16px}}.dna-base-profile-content {{padding:18px 16px}}}}
    </style><section class="dna-base-section" aria-label="Base eleitoral do candidato"><div class="dna-base-heading"><h3>BASE ELEITORAL DO CANDIDATO</h3><p class="dna-base-intro">Quais perfis sustentam a candidatura e qual o peso de cada um na votação?</p></div>{content}</section>'''
