from __future__ import annotations

from eleitoral.common.shared_header import (
    apply_shared_visual_model,
    major_section_header,
    render_page_header,
)
from eleitoral.dna.dna_expansion import render_vote_expansion


apply_shared_visual_model()
render_page_header("expansao_2030")
major_section_header(
    "Expansão & Oportunidades para 2030",
    "Mapeamento em nível de bairro e área ponderada. Localização dos clusters táticos e visualização de manchas de potencial de crescimento.",
)
render_vote_expansion()
