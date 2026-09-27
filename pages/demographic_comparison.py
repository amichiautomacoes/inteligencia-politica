"""Comparable demographic points, grouped by the same dominant category."""
from __future__ import annotations

import html

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from pages.dna_copy import sentence_label


def comparison_chart(rows: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    ideal = rows[rows["source"].eq("ICP geral")]
    if not ideal.empty:
        fig.add_vline(x=float(ideal.iloc[0]["pct_votos"]), line_dash="dot", line_color="#b7c7e6", opacity=0.65)
    for index, (_, row) in enumerate(rows.iterrows()):
        is_ideal = row["source"] == "ICP geral"
        pct = float(row["pct_votos"])
        fig.add_trace(go.Scatter(
            x=[pct], y=[index], mode="markers+text",
            text=[f"{pct:.2f}%".replace(".", ",")],
            textposition="middle left" if pct > 85 else "middle right",
            marker={"size": 15 if is_ideal else 12, "symbol": "diamond" if is_ideal else "circle", "color": "#f8fbff" if is_ideal else "#60a5fa"},
            customdata=[[row["display"], row["value"], row["reason"]]],
            hovertemplate="%{customdata[0]}<br>%{customdata[1]}: %{x:.2f}% no perfil<extra></extra>",
            showlegend=False, name=row["display"], cliponaxis=False,
        ))
    labels = [html.escape(label).replace(" — ICP", "<br>ICP") for label in rows["display"]]
    fig.update_layout(
        height=max(260, 90 + len(rows) * 65),
        margin={"l": 12, "r": 35, "t": 15, "b": 45},
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#eaf2ff"},
        xaxis={"range": [0, 100], "ticksuffix": "%", "title": "Participação da categoria no perfil", "gridcolor": "rgba(147,197,253,.12)", "fixedrange": True},
        yaxis={"tickmode": "array", "tickvals": list(range(len(rows))), "ticktext": labels, "range": [len(rows) - .5, -.5], "automargin": True, "fixedrange": True},
    )
    return fig


def render_comparison(frame: pd.DataFrame) -> None:
    st.html("""<style>
    .st-key-dna-demographic-comparison {background:linear-gradient(135deg,rgba(11,31,77,.76),rgba(7,24,54,.68));border:1px solid rgba(96,165,250,.3);border-radius:20px;padding:24px;margin:24px 0;}
    .st-key-dna-demographic-comparison h3 {font-size:1.35rem;color:#f8fbff;}
    </style>""")
    with st.container(key="dna-demographic-comparison"):
        st.subheader("Composição demográfica do eleitor")
        st.caption("Compare as características demográficas dos perfis de eleitores com o Eleitor Ideal, a referência geral da candidatura.")
        if frame.empty:
            st.info("Composição demográfica indisponível para este candidato.")
            return
        frame = frame.copy()
        frame["display"] = frame.apply(lambda row: "Eleitor Ideal" if row["source"] == "ICP geral" else f'{sentence_label(row["strategy_label"])} — {row["cluster"]}', axis=1)
        dimensions = [d for d in ["Gênero", "Faixa etária", "Escolaridade", "Estado civil"] if d in frame["dimension"].values]
        dimension = st.selectbox("Dimensão demográfica", dimensions, key="dna_comparison_dimension")
        selected = frame[frame["dimension"].eq(dimension)]
        if not selected["source"].eq("ICP geral").any():
            st.caption("Eleitor Ideal indisponível nesta dimensão.")
        if not selected["source"].eq("ICP clusters").any():
            st.caption("ICPs de clusters indisponíveis nesta dimensão.")
        st.caption("◆ Eleitor Ideal · ● Perfis de eleitores · Linha pontilhada: percentual do Eleitor Ideal na mesma categoria.")
        for index, (category, rows) in enumerate(selected.groupby("value", sort=False)):
            st.markdown(f"**{html.escape(sentence_label(category))}**")
            st.plotly_chart(comparison_chart(rows), use_container_width=True, key=f"dna_comparison_{dimension}_{index}", config={"displayModeBar": False, "scrollZoom": False})
        if selected["value"].nunique() > 1:
            st.caption("Categorias dominantes diferentes aparecem em gráficos separados; não representam o mesmo grupo demográfico.")
        labels = selected["display"].tolist()
        # Candidate and dimension changes reset the detail to a valid profile.
        if st.session_state.get("dna_comparison_detail") not in labels:
            st.session_state["dna_comparison_detail"] = labels[0]
        detail = st.selectbox("Perfil para leitura estratégica", labels, key="dna_comparison_detail")
        row = selected[selected["display"].eq(detail)].iloc[0]
        st.caption(f'{row["value"]} · {row["pct_votos"]:.2f}% no perfil'.replace(".", ","))
        st.info(row["reason"])
