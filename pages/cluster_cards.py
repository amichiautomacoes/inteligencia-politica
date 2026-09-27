"""HTML presentation of electoral clusters inside the DNA subsection."""
from __future__ import annotations

import html

import pandas as pd
from pages.dna_copy import sentence_label


def cluster_cards_html(profiles: list[dict]) -> str:
    esc = lambda value: html.escape(str(value))
    percent = lambda value: f"{value:.2f}%".replace(".", ",")
    classes = ["BASE ELEITORAL", "ELEITOR CONSOLIDADO", "ELEITOR EMERGENTE"]
    classes += sorted({p["classification"] for p in profiles} - set(classes))
    summary = []
    cards = []
    for classification in classes:
        members = [p for p in profiles if p["classification"] == classification]
        share = sum(p["share"] for p in members)
        summary.append(f'<div class="dna-base-summary-item"><span>{esc(sentence_label(classification))}</span><strong>{percent(share) if members else "—"}</strong><small>{"da votação do candidato" if members else "Sem perfil nesta classificação"}</small></div>')
        for profile in sorted(members, key=lambda p: p["share"], reverse=True):
            bars = []
            for label, category, value in profile["demographics"]:
                valid = pd.notna(value) and 0 <= value <= 100
                bar = f'<div class="dna-base-track" role="meter" aria-label="{esc(label)}: {esc(category)}" aria-valuemin="0" aria-valuemax="100" aria-valuenow="{value:.4f}"><span style="width:{value:.4f}%"></span></div>' if valid else ""
                bars.append(f'<div class="dna-base-demographic"><div><span>{esc(label)}</span><strong>{percent(value) if valid else "Não informado"}</strong></div><p>{esc(sentence_label(category))}</p>{bar}</div>')
            votes = f'{profile["votes"]:,.0f}'.replace(",", ".")
            cards.append(f'''<article class="dna-base-profile">
                <div class="dna-base-classification">{esc(sentence_label(classification))} · ICP {esc(profile["id"])}</div>
                <h4>{esc(sentence_label(profile["persona"]))}</h4>
                <div class="dna-base-share"><strong>{percent(profile["share"])}</strong><span>da votação do candidato · {votes} votos</span></div>
                <div class="dna-base-demographics">{''.join(bars)}</div>
                <p class="dna-base-note">Percentuais das categorias dominantes dentro deste perfil.</p>
                <div class="dna-base-reason"><strong>Leitura estratégica</strong><p>{esc(profile["reason"])}</p></div>
            </article>''')
    content = f'<div class="dna-base-summary">{"".join(summary)}</div><div class="dna-base-grid">{"".join(cards)}</div>' if profiles else '<p class="dna-base-note">Perfis de clusters indisponíveis para este candidato.</p>'
    return f'''<style>
    .dna-base-section {{margin:24px 0;padding:28px;border:1px solid rgba(96,165,250,.3);border-radius:20px;background:linear-gradient(135deg,rgba(11,31,77,.76),rgba(7,24,54,.68));color:#eaf2ff;box-shadow:0 12px 30px rgba(0,0,0,.14)}}
    .dna-base-section h3 {{font-size:1.35rem;margin:0 0 8px;color:#f8fbff;letter-spacing:.04em}}
    .dna-base-intro,.dna-base-note {{color:#b7c7e6;font-size:.86rem;line-height:1.5}}
    .dna-base-summary {{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin:24px 0}}
    .dna-base-summary-item {{border-left:3px solid #60a5fa;padding:8px 14px;display:flex;flex-direction:column;gap:5px}}
    .dna-base-summary-item span,.dna-base-classification {{font-size:.75rem;font-weight:700;letter-spacing:.05em;color:#b7c7e6}}
    .dna-base-summary-item strong {{font-size:1.7rem;color:#f8fbff}}
    .dna-base-summary-item small {{color:#b7c7e6}}
    .dna-base-grid {{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}}
    .dna-base-profile {{min-width:0;padding:22px;border:1px solid rgba(96,165,250,.2);border-radius:14px;background:rgba(15,42,80,.5);overflow-wrap:anywhere}}
    .dna-base-profile h4 {{font-size:1.12rem;color:#f8fbff;margin:12px 0 18px;line-height:1.4}}
    .dna-base-share {{display:flex;align-items:baseline;flex-wrap:wrap;gap:10px;margin-bottom:22px}}
    .dna-base-share strong {{font-size:1.8rem;color:#93c5fd}}
    .dna-base-share span {{font-size:.8rem;color:#b7c7e6}}
    .dna-base-demographics {{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}
    .dna-base-demographic>div:first-child {{display:flex;justify-content:space-between;gap:8px;font-size:.8rem}}
    .dna-base-demographic p {{font-size:.9rem;margin:5px 0 9px;line-height:1.4}}
    .dna-base-track {{height:6px;border-radius:4px;background:rgba(147,197,253,.15);overflow:hidden}}
    .dna-base-track span {{height:100%;display:block;background:#60a5fa;border-radius:4px}}
    .dna-base-reason {{border-top:1px solid rgba(96,165,250,.2);padding-top:16px;font-size:.9rem;line-height:1.6}}
    .dna-base-reason p {{margin:8px 0 0;color:#b7c7e6}}
    @media(max-width:1000px) {{.dna-base-grid {{grid-template-columns:1fr}}}}
    @media(max-width:600px) {{.dna-base-section {{padding:18px}}.dna-base-summary,.dna-base-demographics {{grid-template-columns:1fr}}}}
    </style><section class="dna-base-section" aria-label="Base eleitoral do candidato"><h3>BASE ELEITORAL DO CANDIDATO</h3><p class="dna-base-intro">Classificações estratégicas, participação na votação e identidade demográfica de cada ICP.</p>{content}</section>'''
