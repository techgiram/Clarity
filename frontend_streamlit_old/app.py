import os
import uuid
from typing import Any, Dict, Optional

import requests
import streamlit as st

DEFAULT_API_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000")
MODES = ["Quick", "Standard", "Deep"]

st.set_page_config(
    page_title="Research Intelligence Workspace",
    page_icon="N",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def init_session_state() -> None:
    st.session_state.setdefault("api_url", DEFAULT_API_URL)
    st.session_state.setdefault("ui_theme", "dark")
    st.session_state.setdefault("research_mode", "Standard")
    st.session_state.setdefault("topic_input", "")
    st.session_state.setdefault("session_id_input", "")
    st.session_state.setdefault("current_run", None)
    st.session_state.setdefault("last_error", "")


def get_theme_palette(theme: str) -> Dict[str, str]:
    if theme == "light":
        return {
            "bg_app": "#f8f9fa",
            "bg_surface": "#ffffff",
            "bg_subtle": "#f1f3f4",
            "bg_pill": "#e8eaed",
            "text_main": "#1f1f1f",
            "text_muted": "#5f6368",
            "border": "#dadce0",
            "accent": "#1a73e8",
            "accent_soft": "rgba(26, 115, 232, 0.12)",
            "accent_text": "#ffffff",
            "badge_ok_bg": "#e6f4ea",
            "badge_ok_fg": "#137333",
            "badge_warn_bg": "#fef7e0",
            "badge_warn_fg": "#b06000",
        }
    return {
        "bg_app": "#131314",
        "bg_surface": "#1e1f20",
        "bg_subtle": "#282a2c",
        "bg_pill": "#2d2f31",
        "text_main": "#e3e3e3",
        "text_muted": "#9aa0a6",
        "border": "#333537",
        "accent": "#8ab4f8",
        "accent_soft": "rgba(138, 180, 248, 0.16)",
        "accent_text": "#0b1426",
        "badge_ok_bg": "rgba(52, 168, 83, 0.16)",
        "badge_ok_fg": "#81c995",
        "badge_warn_bg": "rgba(251, 188, 4, 0.16)",
        "badge_warn_fg": "#fdd663",
    }


def apply_theme_css(palette: Dict[str, str]) -> None:
    st.markdown(
        f"""
        <style>
            :root {{
                --bg-app: {palette["bg_app"]};
                --bg-surface: {palette["bg_surface"]};
                --bg-subtle: {palette["bg_subtle"]};
                --bg-pill: {palette["bg_pill"]};
                --text-main: {palette["text_main"]};
                --text-muted: {palette["text_muted"]};
                --border-subtle: {palette["border"]};
                --accent: {palette["accent"]};
                --accent-soft: {palette["accent_soft"]};
                --accent-text: {palette["accent_text"]};
            }}

            .stApp {{
                background-color: var(--bg-app);
                color: var(--text-main);
            }}

            [data-testid="stHeader"] {{
                background-color: transparent;
            }}

            .block-container {{
                padding-top: 0.85rem;
                padding-bottom: 1.75rem;
                max-width: 99%;
            }}

            .clean-header-row {{
                display: flex;
                align-items: baseline;
                gap: 12px;
                padding: 4px 2px 10px 2px;
                border-bottom: 1px solid var(--border-subtle);
                margin-bottom: 14px;
                flex-wrap: wrap;
            }}

            .clean-title {{
                font-size: 1.15rem;
                font-weight: 600;
                color: var(--text-main);
                letter-spacing: -0.01em;
            }}

            .clean-subtitle {{
                font-size: 0.8rem;
                color: var(--text-muted);
            }}

            .clean-col-title {{
                font-size: 0.92rem;
                font-weight: 600;
                color: var(--text-main);
                padding-bottom: 8px;
                margin-bottom: 10px;
                border-bottom: 1px solid var(--border-subtle);
            }}

            .health-pill {{
                display: inline-flex;
                align-items: center;
                gap: 5px;
                padding: 4px 10px;
                border-radius: 999px;
                font-size: 0.76rem;
                font-weight: 500;
                border: 1px solid var(--border-subtle);
            }}

            .health-ok {{
                background: {palette["badge_ok_bg"]};
                color: {palette["badge_ok_fg"]};
            }}

            .health-warn {{
                background: {palette["badge_warn_bg"]};
                color: {palette["badge_warn_fg"]};
            }}

            .search-plus-container {{
                position: relative;
                display: flex;
                align-items: center;
                justify-content: space-between;
                background: var(--bg-surface);
                border: 1px solid var(--border-subtle);
                border-radius: 22px;
                padding: 8px 14px;
                margin-bottom: 8px;
                transition: border-color 0.18s ease;
            }}

            .search-plus-container:focus-within {{
                border-color: var(--accent);
            }}

            .plus-hover-zone {{
                position: relative;
                display: inline-flex;
                align-items: center;
                gap: 8px;
                cursor: pointer;
            }}

            .plus-circle-btn {{
                width: 32px;
                height: 32px;
                border-radius: 999px;
                background: var(--bg-subtle);
                color: var(--text-main);
                border: 1px solid var(--border-subtle);
                display: inline-flex;
                align-items: center;
                justify-content: center;
                font-size: 1.2rem;
                font-weight: 600;
                line-height: 1;
                transition: all 0.16s ease;
                user-select: none;
            }}

            .plus-hover-zone:hover .plus-circle-btn {{
                background: var(--accent);
                color: var(--accent-text);
                border-color: var(--accent);
                transform: rotate(90deg);
            }}

            .mode-hover-menu {{
                display: none;
                position: absolute;
                left: 0;
                top: 40px;
                z-index: 999;
                min-width: 200px;
                background: var(--bg-surface);
                border: 1px solid var(--border-subtle);
                border-radius: 14px;
                padding: 6px;
                flex-direction: column;
                gap: 3px;
            }}

            .plus-hover-zone:hover .mode-hover-menu,
            .mode-hover-menu:hover {{
                display: flex;
            }}

            .mode-menu-title {{
                font-size: 0.7rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                color: var(--text-muted);
                padding: 4px 8px;
            }}

            .mode-chip {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 6px 10px;
                border-radius: 9px;
                font-size: 0.82rem;
                color: var(--text-main);
            }}

            .mode-chip.active {{
                background: var(--accent-soft);
                color: var(--accent);
                font-weight: 600;
            }}

            .active-mode-pill {{
                display: inline-flex;
                align-items: center;
                padding: 4px 10px;
                border-radius: 999px;
                font-size: 0.76rem;
                font-weight: 600;
                background: var(--accent-soft);
                color: var(--accent);
            }}

            .source-item {{
                background: var(--bg-surface);
                border: 1px solid var(--border-subtle);
                border-radius: 12px;
                padding: 9px 12px;
                margin-bottom: 8px;
                font-size: 0.82rem;
            }}

            .source-id {{
                font-weight: 600;
                color: var(--accent);
                margin-right: 6px;
            }}

            .summary-surface {{
                background: var(--bg-surface);
                border: 1px solid var(--border-subtle);
                border-radius: 14px;
                padding: 14px 16px;
                margin-bottom: 12px;
            }}

            .muted-note {{
                color: var(--text-muted);
                font-size: 0.78rem;
            }}

            .stButton > button {{
                border-radius: 999px;
                font-weight: 500;
                border: 1px solid var(--border-subtle);
                background: var(--bg-surface);
                color: var(--text-main);
            }}

            .stButton > button[kind="primary"] {{
                background-color: var(--accent);
                color: var(--accent-text);
                border-color: var(--accent);
                font-weight: 600;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def api_get(base_url: str, path: str, params: Optional[Dict[str, Any]] = None, timeout: int = 15) -> Any:
    url = f"{base_url.rstrip('/')}{path}"
    resp = requests.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def api_get_bytes(base_url: str, path: str, params: Optional[Dict[str, Any]] = None, timeout: int = 30) -> bytes:
    url = f"{base_url.rstrip('/')}{path}"
    resp = requests.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.content


def api_post(base_url: str, path: str, payload: Optional[Dict[str, Any]] = None, timeout: int = 300) -> Any:
    url = f"{base_url.rstrip('/')}{path}"
    resp = requests.post(url, json=payload or {}, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def api_upload_file(base_url: str, path: str, uploaded_file: Any, timeout: int = 120) -> Any:
    url = f"{base_url.rstrip('/')}{path}"
    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type or "application/octet-stream")}
    resp = requests.post(url, files=files, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def render_top_bar(palette: Dict[str, str]) -> None:
    api_ok = False
    health_info: Dict[str, Any] = {}
    try:
        health_info = api_get(st.session_state["api_url"], "/health", timeout=5)
        api_ok = True
    except Exception:
        api_ok = False

    col_title, col_health, col_theme = st.columns([5.2, 2.8, 2.0])
    with col_title:
        st.markdown(
            """
            <div class="clean-header-row" style="border-bottom: none; margin-bottom: 0; padding-bottom: 4px;">
                <span class="clean-title">Research Intelligence Workspace</span>
                <span class="clean-subtitle">7-Agent LangGraph ? RAG ? Fact Verification ? Exports</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_health:
        pill_class = "health-ok" if api_ok else "health-warn"
        status_label = "API Online" if api_ok else "API Offline"
        db_label = f"DB: {health_info.get('database', 'unknown')}" if api_ok else "Check :8000"
        st.markdown(
            f"""
            <div style="display:flex; gap:6px; align-items:center; justify-content:flex-end; padding-top:4px;">
                <span class="health-pill {pill_class}">{status_label}</span>
                <span class="health-pill" style="background: var(--bg-pill); color: var(--text-muted);">{db_label}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_theme:
        theme_choice = st.selectbox(
            "UI Theme",
            options=["dark", "light"],
            index=0 if st.session_state["ui_theme"] == "dark" else 1,
            format_func=lambda x: "Dark Theme" if x == "dark" else "Light Theme",
            label_visibility="collapsed",
            key="theme_selector_box",
        )
        if theme_choice != st.session_state["ui_theme"]:
            st.session_state["ui_theme"] = theme_choice
            st.rerun()

    st.markdown(
        '<div style="border-bottom: 1px solid var(--border-subtle); margin-top: 6px; margin-bottom: 12px;"></div>',
        unsafe_allow_html=True,
    )


def render_left_sources_column(api_url: str) -> None:
    st.markdown('<div class="clean-col-title">Sources & Knowledge Base</div>', unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Upload PDF, DOCX, TXT, CSV",
        type=["pdf", "docx", "txt", "csv"],
        label_visibility="collapsed",
        key="rag_file_uploader",
    )
    if uploaded is not None:
        if st.button("Index Document", use_container_width=True, key="btn_index_doc"):
            try:
                res = api_upload_file(api_url, "/documents/upload", uploaded)
                st.success(f"Indexed {res.get('filename', uploaded.name)} ({res.get('chunk_count', 0)} chunks)")
            except Exception as exc:
                st.error(f"Upload failed: {exc}")

    st.markdown('<div class="muted-note" style="margin: 8px 0 6px 0;">Indexed Documents</div>', unsafe_allow_html=True)
    try:
        docs = api_get(api_url, "/documents", timeout=10)
        if not docs:
            st.caption("No documents indexed yet.")
        else:
            for d in docs[:10]:
                fname = d.get("filename") or d.get("title") or "Document"
                ext = d.get("file_ext", "")
                chunks = d.get("chunk_count", 0)
                st.markdown(
                    f"""
                    <div class="source-item">
                        <span class="source-id">{ext.upper() or "DOC"}</span>
                        <span>{fname}</span>
                        <div class="muted-note" style="margin-top: 2px;">Chunks: {chunks}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    except Exception as exc:
        st.caption(f"Could not load documents: {exc}")

    run_data = st.session_state.get("current_run") or {}
    citations = run_data.get("citations") or []
    if citations:
        st.markdown('<div class="muted-note" style="margin: 10px 0 6px 0;">Active Run Citations</div>', unsafe_allow_html=True)
        for c in citations:
            cid = c.get("id") or c.get("citation_id") or "SRC"
            title = c.get("title") or c.get("source") or "Source"
            url = c.get("url") or ""
            link_html = f'<div><a href="{url}" target="_blank" style="color: var(--accent); font-size: 0.75rem;">Open Source</a></div>' if url else ""
            st.markdown(
                f"""
                <div class="source-item">
                    <span class="source-id">[{cid}]</span>
                    <span>{title}</span>
                    {link_html}
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_center_studio_column(api_url: str) -> None:
    st.markdown('<div class="clean-col-title">Research & Chat Studio</div>', unsafe_allow_html=True)

    current_mode = st.session_state["research_mode"]
    chips_html = "".join(
        [
            f'<div class="mode-chip {"active" if m == current_mode else ""}"><span>{m}</span><span>{"*" if m == current_mode else ""}</span></div>'
            for m in MODES
        ]
    )

    st.markdown(
        f"""
        <div class="search-plus-container">
            <div class="plus-hover-zone">
                <div class="plus-circle-btn" title="Hover to view research modes">+</div>
                <span class="muted-note">Hover + for modes</span>
                <div class="mode-hover-menu">
                    <div class="mode-menu-title">Research Modes</div>
                    {chips_html}
                </div>
            </div>
            <div class="active-mode-pill">Mode: {current_mode}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    topic = st.text_area(
        "Research Topic / Prompt",
        value=st.session_state["topic_input"],
        height=95,
        placeholder="Enter a research topic, technical question, or follow-up prompt...",
        label_visibility="collapsed",
        key="research_topic_area",
    )

    col_m, col_sid, col_btn = st.columns([2.2, 2.3, 2.5])
    with col_m:
        selected_mode = st.selectbox(
            "Mode",
            options=MODES,
            index=MODES.index(current_mode) if current_mode in MODES else 1,
            label_visibility="collapsed",
            key="mode_select_sync",
        )
        st.session_state["research_mode"] = selected_mode

    with col_sid:
        session_id_val = st.text_input(
            "Session ID (optional)",
            value=st.session_state["session_id_input"],
            placeholder="Session ID (auto-generated)",
            label_visibility="collapsed",
            key="session_id_input_box",
        )

    with col_btn:
        run_clicked = st.button("Run 7-Agent Research", type="primary", use_container_width=True, key="btn_run_research")

    if run_clicked:
        cleaned_topic = (topic or "").strip()
        if not cleaned_topic:
            st.warning("Please enter a research topic or question first.")
        else:
            st.session_state["topic_input"] = cleaned_topic
            st.session_state["session_id_input"] = (session_id_val or "").strip()
            payload = {
                "task": cleaned_topic,
                "research_mode": st.session_state["research_mode"],
                "session_id": st.session_state["session_id_input"] or str(uuid.uuid4()),
            }
            try:
                with st.spinner("Running 7-agent LangGraph research pipeline..."):
                    result = api_post(api_url, "/research/run", payload=payload, timeout=360)
                st.session_state["current_run"] = result
                st.session_state["last_error"] = ""
                st.rerun()
            except Exception as exc:
                st.session_state["last_error"] = str(exc)
                st.error(f"Research run failed: {exc}")

    run_data = st.session_state.get("current_run")
    if run_data:
        status = run_data.get("status", "completed")
        sid = run_data.get("session_id", "")
        summary = run_data.get("summary", "")
        st.markdown(
            f"""
            <div class="summary-surface">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                    <span style="font-weight:600; font-size:0.95rem;">Executive Summary</span>
                    <span class="health-pill health-ok">{status}</span>
                </div>
                <div class="muted-note" style="margin-bottom:8px;">Session: <code>{sid}</code></div>
                <div style="font-size: 0.9rem; line-height: 1.55;">{summary or "No summary returned."}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        followup = st.text_input(
            "Ask a follow-up or refine topic",
            placeholder="Ask a follow-up question based on this research...",
            key="followup_question_input",
        )
        if st.button("Run Follow-up Research", use_container_width=True, key="btn_followup_run"):
            if followup.strip():
                combined = f"{run_data.get('task', '')} ? Follow-up: {followup.strip()}"
                st.session_state["topic_input"] = combined
                try:
                    with st.spinner("Running follow-up 7-agent research..."):
                        res = api_post(
                            api_url,
                            "/research/run",
                            payload={
                                "task": combined,
                                "research_mode": st.session_state["research_mode"],
                                "session_id": str(uuid.uuid4()),
                            },
                            timeout=360,
                        )
                    st.session_state["current_run"] = res
                    st.rerun()
                except Exception as exc:
                    st.error(f"Follow-up failed: {exc}")


def render_right_studio_column(api_url: str) -> None:
    st.markdown('<div class="clean-col-title">Studio & Verification</div>', unsafe_allow_html=True)

    tab_report, tab_facts, tab_history = st.tabs(["Report", "Fact Check", "History & Export"])

    run_data = st.session_state.get("current_run") or {}

    with tab_report:
        report_md = run_data.get("final_report") or ""
        if report_md:
            st.markdown(report_md)
        else:
            st.info("Run a research topic from the center studio to view the generated report here.")

    with tab_facts:
        vc = run_data.get("verified_claims") or {}
        claims = vc.get("claims") if isinstance(vc, dict) else []
        if not claims:
            st.caption("No verified claims available for the active run.")
        else:
            for item in claims:
                st.markdown(
                    f"""
                    <div class="source-item">
                        <span class="source-id">[{item.get("status", "Unchecked")}]</span>
                        <strong>{item.get("claim", "")}</strong>
                        <div class="muted-note" style="margin-top: 4px;">
                            Evidence: {item.get("evidence", "")}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with tab_history:
        active_sid = run_data.get("session_id")
        if active_sid:
            st.markdown("**Export Active Run**")
            c1, c2, c3 = st.columns(3)
            for fmt, col, label in [("md", c1, "MD"), ("docx", c2, "DOCX"), ("pdf", c3, "PDF")]:
                with col:
                    try:
                        blob = api_get_bytes(api_url, f"/research/runs/{active_sid}/export", params={"fmt": fmt})
                        st.download_button(
                            label=label,
                            data=blob,
                            file_name=f"research_{active_sid[:8]}.{fmt}",
                            use_container_width=True,
                            key=f"dl_{active_sid}_{fmt}",
                        )
                    except Exception:
                        st.button(f"{label} N/A", disabled=True, use_container_width=True, key=f"dl_dis_{active_sid}_{fmt}")

        st.divider()
        st.markdown("**Recent Runs**")
        try:
            runs = api_get(api_url, "/research/runs", params={"limit": 12}, timeout=10)
            if not runs:
                st.caption("No saved runs yet.")
            else:
                for r in runs:
                    r_sid = r.get("session_id", "")
                    r_task = r.get("task", "Untitled")
                    r_status = r.get("status", "")
                    col_lbl, col_load = st.columns([3.5, 1.5])
                    with col_lbl:
                        st.caption(f"**{r_task[:48]}** (`{r_status}`)")
                    with col_load:
                        if st.button("Load", key=f"load_{r_sid}", use_container_width=True):
                            try:
                                detail = api_get(api_url, f"/research/runs/{r_sid}", timeout=15)
                                st.session_state["current_run"] = detail
                                st.rerun()
                            except Exception as exc:
                                st.error(f"Load failed: {exc}")
        except Exception as exc:
            st.caption(f"History unavailable: {exc}")


def main() -> None:
    init_session_state()
    palette = get_theme_palette(st.session_state["ui_theme"])
    apply_theme_css(palette)
    render_top_bar(palette)

    left_col, center_col, right_col = st.columns([1.15, 1.85, 1.35], gap="medium")
    with left_col:
        render_left_sources_column(st.session_state["api_url"])
    with center_col:
        render_center_studio_column(st.session_state["api_url"])
    with right_col:
        render_right_studio_column(st.session_state["api_url"])


if __name__ == "__main__":
    main()
