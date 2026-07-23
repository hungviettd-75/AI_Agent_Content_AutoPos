"""Streamlit shell for AI Content Strategy Center.

The route remains the existing Content Planning Wizard tab, but the screen now
hosts the Strategy Center wizard shell. Most Strategy Center generation is routed
through backend services; the logistics planner can request Gemini topic calendars.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import date, datetime, timedelta
from io import BytesIO
from typing import Callable

import pandas as pd
import streamlit as st

from services.content_strategy_service import (
    ANGLE_CATEGORY_OPTIONS,
    BRAND_IDENTITY_FIELDS,
    BUSINESS_CONTEXT_FIELDS,
    BUSINESS_GOAL_OPTIONS,
    FORMAT_OPTIONS,
    FORMAT_STATUS_OPTIONS,
    FUNNEL_STAGE_OPTIONS,
    KPI_METRIC_OPTIONS,
    CALENDAR_VIEW_OPTIONS,
    DEFAULT_TIMEZONE,
    PLATFORM_OPTIONS,
    PLATFORM_PRESETS,
    PRIORITY_OPTIONS,
    PUBLISHING_SUPPORTED_PLATFORMS,
    PERSONA_FIELDS,
    RISK_LEVEL_OPTIONS,
    TREND_CLASSIFICATION_OPTIONS,
    ContentStrategyService,
    merge_subtopics,
    normalize_brand_identity,
    normalize_business_context,
    normalize_business_goal,
    normalize_business_goals,
    normalize_content_angle,
    normalize_content_angles,
    normalize_content_pillar,
    normalize_content_pillars,
    normalize_content_calendar,
    normalize_calendar_item,
    normalize_calendar_settings,
    normalize_format_variant,
    normalize_format_variants,
    normalize_persona,
    normalize_subtopic,
    normalize_subtopics,
    analyze_content_calendar,
    bulk_reschedule_calendar_items,
    delete_calendar_items,
    duplicate_calendar_item,
    generate_content_calendar,
    lock_calendar_items,
    move_calendar_item,
    recommend_format_variant,
    split_subtopic,
    validate_business_goals,
    validate_content_angles,
    validate_content_pillars,
    validate_format_variants,
    validate_persona_completeness,
    validate_subtopics,
)
from services.gemini_client import generate_weekly_plan_json
from database.repositories.content_strategy_repository import ContentStrategyRepository
from config.logistics_vertical import (
    LOGISTICS_ANGLES,
    LOGISTICS_CONTENT_MIX,
    LOGISTICS_PILLAR_BANK,
    LOGISTICS_SAMPLE_30,
    LOGISTICS_TARGETS,
)
from ui.components.empty_state import render_empty_state
from ui.components.loading import render_loading


STEP_DEFINITIONS = [
    ("business_context", "Business Context"),
    ("brand_identity", "Brand Identity"),
    ("audience_personas", "Audience Personas"),
    ("business_goals", "Business Goals"),
    ("content_pillars", "Content Pillars"),
    ("subtopics", "Subtopics"),
    ("content_angles", "Content Angles"),
    ("formats_channels", "Formats and Channels"),
    ("content_calendar", "Content Calendar"),
    ("campaigns_lead_magnets", "Campaigns and Lead Magnets"),
    ("kpi_publishing", "KPI and Publishing"),
    ("review_activate", "Review and Activate"),
]

EDIT_ROLES = {"owner", "admin", "super_admin", "ceo", "manager", "marketing", "editor"}
MANAGE_ROLES = {"owner", "admin", "super_admin"}


def _state_key(workspace_id: int | None, company_id: int | None) -> str:
    return f"content_strategy_center_state_{workspace_id or 'none'}_{company_id or 'none'}"


def _default_draft() -> dict:
    return {
        "strategy_name": "",
        "description": "",
        "start_date": None,
        "end_date": None,
        "business_context": normalize_business_context(),
        "brand_identity": normalize_brand_identity(),
        "audience_personas": [],
        "business_goals": [],
        "content_pillars": [],
        "subtopics": [],
        "content_angles": [],
        "formats_channels": [],
        "content_calendar": {"settings": {}, "items": []},
        "campaigns_lead_magnets": "",
        "kpis": [],
        "kpi_publishing": "",
        "review_notes": "",
    }


def _new_state() -> dict:
    return {
        "strategy_id": None,
        "step_index": 0,
        "draft": _default_draft(),
        "last_saved_hash": "",
        "last_saved_at": "",
        "autosave_status": "Not saved",
        "dirty": False,
        "loading": False,
        "error": "",
        "last_action_key": "",
        "opened_strategy_name": "",
    }




def clear_content_strategy_session_state():
    """Clear Content Strategy Center state after logout or tenant switch."""
    prefixes = (
        "content_strategy_center_state_",
        "current_workspace_id_for_strategy",
        "current_company_id_for_strategy",
        "current_user_id_for_strategy",
        "current_user_email_for_strategy",
    )
    for key in list(st.session_state.keys()):
        if key.startswith(prefixes):
            del st.session_state[key]


def _utc_timestamp() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _saved_caption(state: dict) -> str:
    if state.get("dirty"):
        return "Autosave: pending changes"
    if state.get("last_saved_at"):
        return f"Autosave: saved at {state['last_saved_at']}"
    if state.get("strategy_id"):
        return "Autosave: loaded from saved draft"
    return "Autosave: draft not created yet"


def _friendly_error_message(error, action: str = "Action") -> str:
    if isinstance(error, dict):
        code = str(error.get("code") or "").lower()
        message = str(error.get("message") or "")
        retryable = bool(error.get("retryable"))
    else:
        code = ""
        message = str(error or "")
        retryable = False
    lowered = message.lower()
    if "429" in lowered or "rate limit" in lowered or "quota" in lowered:
        guidance = "Gemini is rate-limited. Wait a minute, then retry this action."
    elif "503" in lowered or "unavailable" in lowered:
        guidance = "Gemini is temporarily unavailable. Retry shortly."
    elif "timeout" in lowered or "timed out" in lowered:
        guidance = "The request timed out. Retry with a smaller batch size."
    elif "json" in lowered or code in {"malformed_json", "validation_failed"}:
        guidance = "The AI response was not valid JSON. Retry, or reduce the requested batch."
    elif "locked" in lowered:
        guidance = "The database is busy. Wait a few seconds and retry."
    elif "connection" in lowered or "network" in lowered:
        guidance = "Connection was interrupted. Check connectivity, then retry."
    elif "workspace" in lowered or "company does not belong" in lowered or "not found for this workspace" in lowered:
        guidance = "This item is not available in the selected workspace. Reopen the correct workspace/company."
    elif "permission" in lowered or "denied" in lowered:
        guidance = "You do not have permission for this action. Ask a workspace admin for access."
    elif "publishing" in lowered and "configuration" in lowered:
        guidance = "Publishing configuration is missing. Configure the platform, then retry."
    elif "expired" in lowered or "session" in lowered:
        guidance = "Your session may have expired. Sign in again and retry."
    else:
        guidance = message or "Something went wrong. Retry the action."
    suffix = " This is retryable." if retryable else ""
    return f"{action} failed. {guidance}{suffix}"


def _set_error(state: dict, error, action: str = "Action"):
    state["error"] = _friendly_error_message(error, action)


def _begin_action(state: dict, action_key: str) -> bool:
    if state.get("loading"):
        state["error"] = "Another action is still running. Wait for it to finish, then retry."
        return False
    state["loading"] = True
    state["last_action_key"] = action_key
    return True


def _end_action(state: dict):
    state["loading"] = False
    state["last_action_key"] = ""


def _confirm_checkbox(label: str, key: str, disabled: bool = False) -> bool:
    return st.checkbox(label, value=False, disabled=disabled, key=key)


def _non_empty_count(value: dict) -> int:
    if not isinstance(value, dict):
        return 1 if str(value or "").strip() else 0
    count = 0
    for item in value.values():
        if isinstance(item, list):
            count += 1 if item else 0
        elif isinstance(item, dict):
            count += 1 if item else 0
        elif str(item or "").strip():
            count += 1
    return count


def business_context_complete(context: dict) -> tuple[bool, list[str]]:
    context = normalize_business_context(context)
    errors = []
    for field in ["company_name", "industry", "market", "business_model"]:
        if not str(context.get(field, "")).strip():
            errors.append(f"Business Context missing: {field.replace('_', ' ')}.")
    if not (str(context.get("products", "")).strip() or str(context.get("services", "")).strip()):
        errors.append("Business Context needs at least Products or Services.")
    return not errors, errors


def brand_identity_complete(brand: dict) -> tuple[bool, list[str]]:
    brand = normalize_brand_identity(brand)
    errors = []
    for field in ["tone_of_voice", "personality", "writing_style", "standard_cta", "communication_principles"]:
        if not str(brand.get(field, "")).strip():
            errors.append(f"Brand Identity missing: {field.replace('_', ' ')}.")
    return not errors, errors


def audience_personas_complete(personas: list) -> tuple[bool, list[str]]:
    if not personas:
        return False, ["Audience Personas needs at least one confirmed or edited persona."]
    errors = []
    for index, persona in enumerate(personas):
        missing = validate_persona_completeness(normalize_persona(persona, index))
        if missing:
            errors.append(f"Persona {index + 1} incomplete: {', '.join(missing)}.")
    return not errors, errors


def _normalize_current_draft(draft: dict, workspace_id: int | None = None, company_id: int | None = None) -> dict:
    try:
        normalized = ContentStrategyService.normalize_draft(draft, workspace_id=workspace_id, company_id=company_id)
    except Exception:
        normalized = dict(draft or {})
        normalized["business_context"] = normalize_business_context(normalized.get("business_context"))
        normalized["brand_identity"] = normalize_brand_identity(normalized.get("brand_identity"))
        normalized["audience_personas"] = [normalize_persona(p, i) for i, p in enumerate(normalized.get("audience_personas") or []) if isinstance(p, dict)]
    return normalized

def user_can_edit(role: str) -> bool:
    return (role or "viewer").lower() in EDIT_ROLES


def user_can_manage(role: str) -> bool:
    return (role or "viewer").lower() in MANAGE_ROLES


def draft_hash(draft: dict) -> str:
    return hashlib.sha256(json.dumps(draft or {}, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def validate_step(step_index: int, draft: dict) -> tuple[bool, list[str]]:
    key, label = STEP_DEFINITIONS[step_index]
    errors = []
    if step_index == 0:
        if not (draft.get("strategy_name") or "").strip():
            errors.append("Strategy name is required.")
        ok, step_errors = business_context_complete(draft.get("business_context") or {})
        errors.extend(step_errors if not ok else [])
    elif key == "brand_identity":
        ok, step_errors = brand_identity_complete(draft.get("brand_identity") or {})
        errors.extend(step_errors if not ok else [])
    elif key == "audience_personas":
        ok, step_errors = audience_personas_complete(draft.get("audience_personas") or [])
        errors.extend(step_errors if not ok else [])
    elif key == "business_goals":
        step_errors, _ = validate_business_goals(draft.get("business_goals") or [])
        errors.extend(step_errors)
    elif key == "content_pillars":
        step_errors, _ = validate_content_pillars(
            draft.get("content_pillars") or [],
            draft.get("business_goals") or [],
            draft.get("audience_personas") or [],
        )
        errors.extend(step_errors)
    elif key == "subtopics":
        step_errors, _ = validate_subtopics(draft.get("subtopics") or [], draft.get("content_pillars") or [])
        errors.extend(step_errors)
    elif key == "content_angles":
        step_errors, _ = validate_content_angles(draft.get("content_angles") or [], draft.get("subtopics") or [])
        errors.extend(step_errors)
    elif key == "formats_channels":
        step_errors, _ = validate_format_variants(draft.get("formats_channels") or [], draft.get("content_angles") or [], draft.get("brand_identity") or {})
        errors.extend(step_errors)
    elif key == "content_calendar":
        ok, step_errors = _calendar_complete(draft.get("content_calendar") or {})
        errors.extend(step_errors if not ok else [])
    elif key == "review_activate":
        for required_key, required_label in STEP_DEFINITIONS[:-1]:
            value = draft.get(required_key)
            if required_key == "business_context":
                ok, _ = business_context_complete(value or {})
            elif required_key == "brand_identity":
                ok, _ = brand_identity_complete(value or {})
            elif required_key == "audience_personas":
                ok, _ = audience_personas_complete(value or [])
            elif required_key == "business_goals":
                ok = not validate_business_goals(value or [])[0]
            elif required_key == "content_pillars":
                ok = not validate_content_pillars(value or [], draft.get("business_goals") or [], draft.get("audience_personas") or [])[0]
            elif required_key == "subtopics":
                ok = not validate_subtopics(value or [], draft.get("content_pillars") or [])[0]
            elif required_key == "content_angles":
                ok = not validate_content_angles(value or [], draft.get("subtopics") or [])[0]
            elif required_key == "formats_channels":
                ok = not validate_format_variants(value or [], draft.get("content_angles") or [], draft.get("brand_identity") or {})[0]
            elif required_key == "content_calendar":
                ok = _calendar_complete(value or {})[0]
            else:
                ok = bool(str(value or "").strip())
            if not ok:
                errors.append(f"{required_label} is incomplete.")
    elif isinstance(draft.get(key), list):
        if not draft.get(key):
            errors.append(f"{label} is required for this step.")
    elif not (draft.get(key) or "").strip():
        errors.append(f"{label} is required for this step.")
    return not errors, errors

def next_step_index(current: int, draft: dict) -> tuple[int, list[str]]:
    ok, errors = validate_step(current, draft)
    if not ok:
        return current, errors
    return min(current + 1, len(STEP_DEFINITIONS) - 1), []


def previous_step_index(current: int) -> int:
    return max(current - 1, 0)


def _draft_from_strategy(strategy: dict) -> dict:
    draft = _default_draft()
    metadata = strategy.get("metadata") or {}
    saved = metadata.get("wizard_draft") or {}
    draft.update(saved)
    draft["strategy_name"] = draft.get("strategy_name") or strategy.get("name", "")
    draft["description"] = draft.get("description") or strategy.get("description", "")
    draft["start_date"] = draft.get("start_date") or strategy.get("start_date")
    draft["end_date"] = draft.get("end_date") or strategy.get("end_date")
    return _normalize_current_draft(draft, strategy.get("workspace_id"), strategy.get("company_id"))


def _strategy_label(strategy: dict) -> str:
    status = strategy.get("status", "draft")
    version = strategy.get("version", 1)
    return f"#{strategy.get('id')} - {strategy.get('name')} ({status}, v{version})"


def _ensure_state(state_key: str) -> dict:
    if state_key not in st.session_state:
        st.session_state[state_key] = _new_state()
    return st.session_state[state_key]


def _sync_input(state: dict, field: str, value):
    if value != state["draft"].get(field):
        state["draft"][field] = value
        state["dirty"] = True


def _date_value(value):
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            return date.today()
    return date.today()

def step_completion_rows(draft: dict, current_step_index: int) -> list[dict]:
    rows = []
    for index, (_, label) in enumerate(STEP_DEFINITIONS):
        ok, errors = validate_step(index, draft)
        status = "Current" if index == current_step_index else "Complete" if ok else "Needs work"
        rows.append({
            "Step": index + 1,
            "Name": label,
            "Status": status,
            "Action": "Continue here" if index == current_step_index else "Ready" if ok else "Review required",
            "Issue": errors[0] if errors else "",
        })
    return rows


def _render_progress(step_index: int, draft: dict | None = None):
    total = len(STEP_DEFINITIONS)
    st.progress((step_index + 1) / total)
    st.caption(f"Step {step_index + 1} of {total}: {STEP_DEFINITIONS[step_index][1]}")
    if draft is not None:
        with st.expander("Step completion status", expanded=False):
            st.dataframe(pd.DataFrame(step_completion_rows(draft, step_index)), use_container_width=True, hide_index=True)


def _render_strategy_picker(service: ContentStrategyService, workspace_id: int, company_id: int, state: dict, can_edit: bool, can_manage: bool, user_id: int | None):
    page_key = f"strategy_list_page_{workspace_id}_{company_id}"
    page_size = st.selectbox("Strategies per page", [10, 25, 50], index=1, key=f"strategy_list_size_{workspace_id}_{company_id}")
    page = int(st.session_state.get(page_key, 1) or 1)
    offset = (page - 1) * int(page_size)
    result = service.list_strategies(workspace_id, company_id, include_archived=can_manage, limit=int(page_size), offset=offset)
    if not result.get("ok"):
        st.error(f"Could not load strategies: {result.get('error')}")
        return

    strategies = result.get("strategies", [])
    if result.get("pagination"):
        paging = result["pagination"]
        p1, p2, p3 = st.columns([1, 2, 1])
        with p1:
            if st.button("Previous strategies", disabled=page <= 1, use_container_width=True, key=f"strategy_prev_{workspace_id}_{company_id}"):
                st.session_state[page_key] = max(1, page - 1)
                st.rerun()
        with p2:
            st.caption(f"Showing {len(strategies)} strategy draft(s), page {page}.")
        with p3:
            if st.button("Next strategies", disabled=not paging.get("has_more"), use_container_width=True, key=f"strategy_next_{workspace_id}_{company_id}"):
                st.session_state[page_key] = page + 1
                st.rerun()

    c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
    with c1:
        if strategies:
            selected_id = st.selectbox(
                "Open Strategy",
                options=[s["id"] for s in strategies],
                format_func=lambda sid: _strategy_label(next(s for s in strategies if s["id"] == sid)),
                key=f"strategy_open_select_{workspace_id}_{company_id}",
            )
        else:
            selected_id = None
            render_empty_state("No strategies yet", "Create a new strategy draft to start the wizard shell.", icon="+")
    with c2:
        if st.button("Open", disabled=selected_id is None or state.get("loading"), use_container_width=True, key=f"strategy_open_btn_{workspace_id}_{company_id}"):
            if not _begin_action(state, f"open:{selected_id}"):
                st.rerun()
            opened = service.open_strategy(workspace_id, company_id, selected_id)
            if opened.get("ok"):
                strategy = opened["strategy"]
                state.update(_new_state())
                state["strategy_id"] = strategy["id"]
                state["draft"] = _draft_from_strategy(strategy)
                state["last_saved_hash"] = draft_hash(state["draft"])
                state["opened_strategy_name"] = strategy.get("name", "")
                state["last_saved_at"] = strategy.get("updated_at") or ""
                _end_action(state)
                st.rerun()
            _set_error(state, opened.get("error", "Open failed"), "Open strategy")
            _end_action(state)
    with c3:
        if st.button("New Strategy", disabled=not can_edit or state.get("loading"), use_container_width=True, key=f"strategy_new_btn_{workspace_id}_{company_id}"):
            state.update(_new_state())
            state["dirty"] = True
            st.rerun()
    with c4:
        if st.button("Exit Wizard", disabled=state.get("loading"), use_container_width=True, key=f"strategy_exit_btn_{workspace_id}_{company_id}"):
            state.update(_new_state())
            st.rerun()

    action_cols = st.columns(4)
    with action_cols[0]:
        if st.button("Save Draft", disabled=not can_edit or state.get("loading"), use_container_width=True, key=f"strategy_save_btn_{workspace_id}_{company_id}"):
            _save_current_draft(service, workspace_id, company_id, state, user_id, create_version=True)
    with action_cols[1]:
        if st.button("Duplicate Strategy", disabled=state.get("loading") or not (can_edit and state.get("strategy_id")), use_container_width=True, key=f"strategy_duplicate_btn_{workspace_id}_{company_id}"):
            if not _begin_action(state, f"duplicate:{state['strategy_id']}"):
                st.rerun()
            result = service.duplicate_strategy(workspace_id, company_id, state["strategy_id"], created_by=user_id)
            if result.get("ok"):
                state["strategy_id"] = result["strategy_id"]
                state["dirty"] = True
                st.success("Strategy duplicated as a new draft.")
                _end_action(state)
                st.rerun()
            _set_error(state, result.get("error", "Duplicate failed"), "Duplicate strategy")
            _end_action(state)
    with action_cols[2]:
        archive_confirmed = _confirm_checkbox("Confirm archive", f"strategy_archive_confirm_{workspace_id}_{company_id}_{state.get('strategy_id')}", disabled=not (can_manage and state.get("strategy_id")))
        if st.button("Archive Strategy", disabled=state.get("loading") or not (can_manage and state.get("strategy_id") and archive_confirmed), use_container_width=True, key=f"strategy_archive_btn_{workspace_id}_{company_id}"):
            if not _begin_action(state, f"archive:{state['strategy_id']}"):
                st.rerun()
            result = service.archive_strategy(workspace_id, company_id, state["strategy_id"], updated_by=user_id)
            if result.get("ok"):
                state.update(_new_state())
                st.success("Strategy archived.")
                _end_action(state)
                st.rerun()
            _set_error(state, result.get("error", "Archive failed"), "Archive strategy")
            _end_action(state)
    with action_cols[3]:
        _render_restore_version(service, workspace_id, company_id, state, can_manage, user_id)


def _render_restore_version(service, workspace_id, company_id, state, can_manage, user_id):
    if not state.get("strategy_id"):
        st.button("Restore Version", disabled=True, use_container_width=True)
        return
    versions = service.list_versions(workspace_id, company_id, state["strategy_id"])
    options = versions.get("versions", []) if versions.get("ok") else []
    if not options:
        st.button("Restore Version", disabled=True, use_container_width=True)
        return
    version_id = st.selectbox(
        "Version",
        options=[v["id"] for v in options],
        format_func=lambda vid: f"v{next(v for v in options if v['id'] == vid)['version']}",
        label_visibility="collapsed",
        key=f"strategy_version_select_{workspace_id}_{company_id}_{state['strategy_id']}",
    )
    restore_confirmed = _confirm_checkbox("Confirm restore selected version", f"strategy_restore_confirm_{workspace_id}_{company_id}_{state.get('strategy_id')}_{version_id}", disabled=not can_manage)
    if st.button("Restore Version", disabled=state.get("loading") or not (can_manage and restore_confirmed), use_container_width=True, key=f"strategy_restore_btn_{workspace_id}_{company_id}_{state.get('strategy_id')}"):
        if not _begin_action(state, f"restore:{state['strategy_id']}:{version_id}"):
            st.rerun()
        restored = service.restore_version(workspace_id, company_id, state["strategy_id"], version_id, updated_by=user_id)
        if restored.get("ok"):
            opened = service.open_strategy(workspace_id, company_id, state["strategy_id"])
            if opened.get("ok"):
                state["draft"] = _draft_from_strategy(opened["strategy"])
                state["last_saved_hash"] = draft_hash(state["draft"])
                state["last_saved_at"] = opened["strategy"].get("updated_at") or _utc_timestamp()
            st.success("Version restored.")
            _end_action(state)
            st.rerun()
        _set_error(state, restored.get("error", "Restore failed"), "Restore version")
        _end_action(state)


def _save_current_draft(service: ContentStrategyService, workspace_id: int, company_id: int, state: dict, user_id: int | None, create_version: bool):
    name = (state["draft"].get("strategy_name") or "").strip()
    if not name:
        state["error"] = "Save draft failed. Strategy name is required before saving."
        return
    if not _begin_action(state, f"save:{state.get('strategy_id') or 'new'}:{create_version}"):
        return
    state["autosave_status"] = "Saving"
    with st.spinner("Saving strategy draft..."):
        if state.get("strategy_id"):
            result = service.save_draft(workspace_id, company_id, state["strategy_id"], state["draft"], updated_by=user_id, create_version=create_version)
        else:
            result = service.create_draft_strategy(workspace_id, company_id, name, state["draft"], created_by=user_id)
            if result.get("ok"):
                state["strategy_id"] = result["strategy_id"]
    if result.get("ok"):
        state["last_saved_hash"] = draft_hash(state["draft"])
        state["last_saved_at"] = _utc_timestamp()
        state["autosave_status"] = "Saved"
        state["dirty"] = False
        state["error"] = ""
        if create_version:
            st.success("Draft saved.")
    else:
        state["autosave_status"] = "Save failed"
        _set_error(state, result.get("error", "Save failed"), "Save draft")
    _end_action(state)


def _autosave_if_needed(service, workspace_id, company_id, state, can_edit, user_id):
    if not (can_edit and state.get("strategy_id")):
        return
    current_hash = draft_hash(state["draft"])
    if current_hash and current_hash != state.get("last_saved_hash"):
        state["dirty"] = True
        _save_current_draft(service, workspace_id, company_id, state, user_id, create_version=False)


def _render_business_context(state: dict, disabled: bool, prefix: str):
    draft = state["draft"]
    draft["business_context"] = normalize_business_context(draft.get("business_context"))
    _sync_input(state, "strategy_name", st.text_input("Strategy name", value=draft.get("strategy_name", ""), disabled=disabled, key=f"{prefix}_name"))
    _sync_input(state, "description", st.text_area("Description", value=draft.get("description", ""), disabled=disabled, key=f"{prefix}_description"))
    c1, c2 = st.columns(2)
    with c1:
        _sync_input(state, "start_date", str(st.date_input("Start date", value=_date_value(draft.get("start_date")), disabled=disabled, key=f"{prefix}_start")))
    with c2:
        _sync_input(state, "end_date", str(st.date_input("End date", value=_date_value(draft.get("end_date")), disabled=disabled, key=f"{prefix}_end")))

    if st.button("Load from Company Brain", disabled=disabled, use_container_width=True, key=f"{prefix}_load_company"):
        state["draft"]["business_context"] = ContentStrategyService.get_business_context_seed(
            st.session_state.get("current_workspace_id_for_strategy", 0),
            st.session_state.get("current_company_id_for_strategy", 0),
        )
        state["dirty"] = True
        st.rerun()

    upload = st.file_uploader("Import business context", type=["json", "txt", "csv"], disabled=disabled, key=f"{prefix}_business_upload")
    if upload is not None and not disabled:
        raw = upload.getvalue().decode("utf-8", errors="ignore")
        imported = {}
        if upload.name.lower().endswith(".json"):
            try:
                imported = json.loads(raw)
            except Exception:
                state["error"] = "Uploaded JSON could not be parsed."
        elif upload.name.lower().endswith(".csv"):
            try:
                df = pd.read_csv(upload)
                if not df.empty:
                    imported = {str(row[0]).strip(): row[1] for _, row in df.iterrows() if len(row) >= 2}
            except Exception:
                state["error"] = "Uploaded CSV could not be parsed."
        else:
            imported = {"brand_story": raw[:5000]}
        if imported:
            merged = normalize_business_context({**draft["business_context"], **imported})
            _sync_input(state, "business_context", merged)

    labels = {
        "company_name": "Company name",
        "industry": "Industry",
        "website": "Website",
        "market": "Market",
        "business_model": "Business model",
        "products": "Products",
        "services": "Services",
        "price_range": "Price range",
        "competitive_advantages": "Competitive advantages",
        "mission": "Mission",
        "vision": "Vision",
        "brand_story": "Brand story",
        "current_marketing_challenges": "Current marketing challenges",
        "main_competitors": "Main competitors",
        "marketing_budget_range": "Marketing budget range",
        "available_resources": "Available resources",
    }
    next_context = dict(draft["business_context"])
    for index, field in enumerate(BUSINESS_CONTEXT_FIELDS):
        if index % 2 == 0:
            cols = st.columns(2)
        with cols[index % 2]:
            height = 110 if field in {"products", "services", "competitive_advantages", "brand_story", "current_marketing_challenges", "available_resources"} else None
            if height:
                next_context[field] = st.text_area(labels[field], value=str(next_context.get(field, "")), height=height, disabled=disabled, key=f"{prefix}_bc_{field}")
            else:
                next_context[field] = st.text_input(labels[field], value=str(next_context.get(field, "")), disabled=disabled, key=f"{prefix}_bc_{field}")
    _sync_input(state, "business_context", normalize_business_context(next_context))


def _render_brand_identity(state: dict, disabled: bool, prefix: str):
    draft = state["draft"]
    brand = normalize_brand_identity(draft.get("brand_identity"))
    mode = st.radio(
        "Brand source",
        options=["existing", "custom"],
        format_func=lambda value: "Use existing brand" if value == "existing" else "Customize for this strategy",
        horizontal=True,
        disabled=disabled,
        key=f"{prefix}_brand_mode",
        index=0 if brand.get("mode") != "custom" else 1,
    )
    brand["mode"] = mode
    if st.button("Load existing Brand Identity", disabled=disabled, use_container_width=True, key=f"{prefix}_load_brand"):
        brand = ContentStrategyService.get_brand_identity_seed(
            st.session_state.get("current_workspace_id_for_strategy", 0),
            st.session_state.get("current_company_id_for_strategy", 0),
        )
        brand["mode"] = mode
        _sync_input(state, "brand_identity", brand)
        st.rerun()

    labels = {
        "tone_of_voice": "Tone of voice",
        "personality": "Personality",
        "writing_style": "Writing style",
        "brand_keywords": "Brand keywords",
        "forbidden_words": "Forbidden words",
        "standard_cta": "Standard CTA",
        "mission": "Mission",
        "vision": "Vision",
        "colors": "Colors",
        "communication_principles": "Communication principles",
    }
    next_brand = dict(brand)
    for field in BRAND_IDENTITY_FIELDS:
        current = next_brand.get(field, [])
        if field in {"brand_keywords", "forbidden_words"}:
            current = ", ".join(current if isinstance(current, list) else [str(current)])
            next_brand[field] = [item.strip() for item in st.text_input(labels[field], value=current, disabled=disabled, key=f"{prefix}_brand_{field}").split(",") if item.strip()]
        elif field == "colors":
            current = json.dumps(current or {}, ensure_ascii=False) if isinstance(current, dict) else str(current or "")
            raw_colors = st.text_area(labels[field], value=current, height=80, disabled=disabled, key=f"{prefix}_brand_{field}")
            try:
                next_brand[field] = json.loads(raw_colors) if raw_colors.strip().startswith("{") else raw_colors
            except Exception:
                next_brand[field] = raw_colors
        else:
            next_brand[field] = st.text_area(labels[field], value=str(current or ""), height=90, disabled=disabled, key=f"{prefix}_brand_{field}") if field in {"writing_style", "mission", "vision", "communication_principles"} else st.text_input(labels[field], value=str(current or ""), disabled=disabled, key=f"{prefix}_brand_{field}")

    confirm = st.checkbox("Save this customization back to global Brand Identity", disabled=disabled or mode != "custom", key=f"{prefix}_brand_save_confirm")
    if st.button("Save Brand Identity Update", disabled=disabled or mode != "custom" or not confirm, use_container_width=True, key=f"{prefix}_brand_save_back"):
        result = ContentStrategyService.save_brand_identity_customization(
            st.session_state.get("current_workspace_id_for_strategy", 0),
            st.session_state.get("current_company_id_for_strategy", 0),
            next_brand,
            confirmed=confirm,
            updated_by=st.session_state.get("current_user_id_for_strategy"),
            user_email=st.session_state.get("current_user_email_for_strategy", ""),
        )
        if result.get("ok"):
            st.success("Brand Identity updated.")
        else:
            state["error"] = result.get("error", "Brand update failed")
    next_brand["save_back_confirmed"] = bool(confirm)
    _sync_input(state, "brand_identity", normalize_brand_identity(next_brand))


def _empty_persona(sort_order: int = 0) -> dict:
    return normalize_persona({"id": str(uuid.uuid4()), "sort_order": sort_order}, sort_order)


def _move_persona(personas: list, index: int, delta: int) -> list:
    target = index + delta
    if target < 0 or target >= len(personas):
        return personas
    items = list(personas)
    items[index], items[target] = items[target], items[index]
    for idx, item in enumerate(items):
        item["sort_order"] = idx
    return items


def _render_persona_editor(persona: dict, index: int, disabled: bool, prefix: str) -> dict:
    item = normalize_persona(persona, index)
    if item.get("ai_generated_draft"):
        st.caption("AI-generated draft. Review and edit before confirming.")
    c1, c2 = st.columns(2)
    with c1:
        item["name"] = st.text_input("Name", value=item.get("name", ""), disabled=disabled, key=f"{prefix}_persona_{index}_name")
        item["role"] = st.text_input("Role", value=item.get("role", ""), disabled=disabled, key=f"{prefix}_persona_{index}_role")
        item["industry"] = st.text_input("Industry", value=item.get("industry", ""), disabled=disabled, key=f"{prefix}_persona_{index}_industry")
        item["company_size"] = st.text_input("Company size", value=item.get("company_size", ""), disabled=disabled, key=f"{prefix}_persona_{index}_company_size")
        item["decision_authority"] = st.text_input("Decision authority", value=item.get("decision_authority", ""), disabled=disabled, key=f"{prefix}_persona_{index}_decision")
        item["customer_journey_stage"] = st.selectbox("Customer journey stage", ["", "awareness", "consideration", "decision", "retention", "advocacy"], index=["", "awareness", "consideration", "decision", "retention", "advocacy"].index(item.get("customer_journey_stage", "")) if item.get("customer_journey_stage", "") in ["", "awareness", "consideration", "decision", "retention", "advocacy"] else 0, disabled=disabled, key=f"{prefix}_persona_{index}_journey")
    with c2:
        item["demographics"] = st.text_area("Demographics if appropriate", value=item.get("demographics", ""), height=80, disabled=disabled, key=f"{prefix}_persona_{index}_demo")
        item["content_depth_preference"] = st.text_input("Content depth preference", value=item.get("content_depth_preference", ""), disabled=disabled, key=f"{prefix}_persona_{index}_depth")
        item["language_style"] = st.text_input("Language style", value=item.get("language_style", ""), disabled=disabled, key=f"{prefix}_persona_{index}_language")
    list_fields = ["goals", "pain_points", "fears", "desires", "objections", "buying_triggers", "preferred_channels", "preferred_content_formats"]
    for field in list_fields:
        value = "\n".join(item.get(field) or [])
        item[field] = [line.strip() for line in st.text_area(field.replace("_", " ").title(), value=value, height=85, disabled=disabled, key=f"{prefix}_persona_{index}_{field}").split("\n") if line.strip()]
    if item.get("ai_generated_draft"):
        item["status"] = "draft"
    missing = validate_persona_completeness(item)
    if missing:
        st.warning("Missing: " + ", ".join(missing))
    else:
        st.success("Persona completeness validated.")
    return item


def _render_audience_personas(state: dict, disabled: bool, prefix: str):
    personas = [normalize_persona(persona, i) for i, persona in enumerate(state["draft"].get("audience_personas") or [])]
    actions = st.columns(4)
    with actions[0]:
        if st.button("Add Persona", disabled=disabled, use_container_width=True, key=f"{prefix}_persona_add"):
            personas.append(_empty_persona(len(personas)))
            _sync_input(state, "audience_personas", personas)
            st.rerun()
    with actions[1]:
        if st.button("Import from Company Brain", disabled=disabled, use_container_width=True, key=f"{prefix}_persona_import"):
            bc = normalize_business_context(state["draft"].get("business_context"))
            if bc.get("market") or bc.get("industry"):
                personas.append(normalize_persona({
                    "id": str(uuid.uuid4()),
                    "name": "Imported audience segment",
                    "industry": bc.get("industry", ""),
                    "goals": [bc.get("current_marketing_challenges", "")],
                    "pain_points": [],
                    "preferred_channels": [],
                    "status": "draft",
                }, len(personas)))
                _sync_input(state, "audience_personas", personas)
                st.rerun()
            else:
                st.info("No supported existing customer-data source found for this company.")
    with actions[2]:
        count = st.number_input("AI drafts", min_value=1, max_value=5, value=1, disabled=disabled, key=f"{prefix}_persona_ai_count")
    with actions[3]:
        if st.button("Generate persona with AI", disabled=disabled, use_container_width=True, key=f"{prefix}_persona_ai"):
            service = ContentStrategyService(api_key=None)
            result = service.generate_persona_drafts(
                st.session_state.get("current_workspace_id_for_strategy", 0),
                st.session_state.get("current_company_id_for_strategy", 0),
                state["draft"],
                count=int(count),
                created_by=st.session_state.get("current_user_id_for_strategy"),
            )
            if result.get("ok"):
                personas.extend(result.get("personas") or [])
                _sync_input(state, "audience_personas", personas)
                st.rerun()
            else:
                _set_error(state, result.get("error"), "Generate personas")

    if not personas:
        render_empty_state("No personas yet", "Add a persona, import supported audience context, or generate AI drafts when you are ready.", icon="+")
        _sync_input(state, "audience_personas", [])
        return

    edited = []
    for index, persona in enumerate(personas):
        title = persona.get("name") or f"Persona {index + 1}"
        suffix = " (AI draft)" if persona.get("ai_generated_draft") else ""
        with st.expander(f"{index + 1}. {title}{suffix}", expanded=index == 0):
            cols = st.columns(5)
            with cols[0]:
                if st.button("Up", disabled=disabled or index == 0, key=f"{prefix}_persona_{index}_up"):
                    _sync_input(state, "audience_personas", _move_persona(personas, index, -1))
                    st.rerun()
            with cols[1]:
                if st.button("Down", disabled=disabled or index == len(personas) - 1, key=f"{prefix}_persona_{index}_down"):
                    _sync_input(state, "audience_personas", _move_persona(personas, index, 1))
                    st.rerun()
            with cols[2]:
                if st.button("Duplicate", disabled=disabled, key=f"{prefix}_persona_{index}_dup"):
                    copy_item = normalize_persona({**persona, "id": str(uuid.uuid4()), "name": f"{persona.get('name', 'Persona')} Copy"}, len(personas))
                    personas.insert(index + 1, copy_item)
                    _sync_input(state, "audience_personas", personas)
                    st.rerun()
            with cols[3]:
                confirm_delete = _confirm_checkbox("Confirm delete persona", f"{prefix}_persona_{index}_delete_confirm", disabled=disabled)
                if st.button("Delete", disabled=disabled or not confirm_delete, key=f"{prefix}_persona_{index}_delete"):
                    personas.pop(index)
                    _sync_input(state, "audience_personas", personas)
                    st.rerun()
            with cols[4]:
                if persona.get("ai_generated_draft") and st.button("Confirm Draft", disabled=disabled, key=f"{prefix}_persona_{index}_confirm"):
                    persona["ai_generated_draft"] = False
                    persona["status"] = "active"
                    _sync_input(state, "audience_personas", personas)
                    st.rerun()
            edited.append(_render_persona_editor(persona, index, disabled, prefix))
    _sync_input(state, "audience_personas", edited)


def _move_item(items: list, index: int, delta: int) -> list:
    target = index + delta
    if target < 0 or target >= len(items):
        return items
    next_items = list(items)
    next_items[index], next_items[target] = next_items[target], next_items[index]
    for idx, item in enumerate(next_items):
        item["sort_order"] = idx
    return next_items


def _render_business_goals(state: dict, disabled: bool, prefix: str):
    goals = normalize_business_goals(state["draft"].get("business_goals") or [])
    selected_names = [goal.get("name") for goal in goals if goal.get("name") in BUSINESS_GOAL_OPTIONS]
    selected = st.multiselect("Selected goals", BUSINESS_GOAL_OPTIONS, default=selected_names, disabled=disabled, key=f"{prefix}_goal_selected")
    by_name = {goal.get("name"): goal for goal in goals if goal.get("name")}
    next_goals = []
    for index, name in enumerate(selected):
        next_goals.append(normalize_business_goal({**by_name.get(name, {}), "name": name}, index))
    custom_goals = [goal for goal in goals if goal.get("name") and goal.get("name") not in BUSINESS_GOAL_OPTIONS]
    next_goals.extend(custom_goals)
    goals = next_goals

    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button("Add Custom Goal", disabled=disabled, use_container_width=True, key=f"{prefix}_goal_add"):
            goals.append(normalize_business_goal({"id": str(uuid.uuid4()), "name": "Custom Goal"}, len(goals)))
            _sync_input(state, "business_goals", goals)
            st.rerun()
    with c2:
        errors, warnings = validate_business_goals(goals)
        for message in errors:
            st.error(message)
        for message in warnings:
            st.warning(message)

    edited = []
    for index, goal in enumerate(goals):
        goal = normalize_business_goal(goal, index)
        title = goal.get("name") or f"Goal {index + 1}"
        with st.expander(f"{index + 1}. {title}", expanded=index == 0):
            actions = st.columns(3)
            with actions[0]:
                if st.button("Up", disabled=disabled or index == 0, key=f"{prefix}_goal_{index}_up"):
                    _sync_input(state, "business_goals", _move_item(goals, index, -1))
                    st.rerun()
            with actions[1]:
                if st.button("Down", disabled=disabled or index == len(goals) - 1, key=f"{prefix}_goal_{index}_down"):
                    _sync_input(state, "business_goals", _move_item(goals, index, 1))
                    st.rerun()
            with actions[2]:
                confirm_delete = _confirm_checkbox("Confirm delete goal", f"{prefix}_goal_{index}_delete_confirm", disabled=disabled)
                if st.button("Delete", disabled=disabled or not confirm_delete, key=f"{prefix}_goal_{index}_delete"):
                    goals.pop(index)
                    _sync_input(state, "business_goals", goals)
                    st.rerun()
            cols = st.columns(2)
            with cols[0]:
                goal["name"] = st.text_input("Goal", value=goal.get("name", ""), disabled=disabled, key=f"{prefix}_goal_{index}_name")
                goal["priority"] = st.selectbox("Priority", PRIORITY_OPTIONS, index=PRIORITY_OPTIONS.index(goal.get("priority", "medium")), disabled=disabled, key=f"{prefix}_goal_{index}_priority")
                goal["target_metric"] = st.text_input("Target metric", value=goal.get("target_metric", ""), disabled=disabled, key=f"{prefix}_goal_{index}_metric")
                goal["target_value"] = st.text_input("Target value", value=str(goal.get("target_value", "")), disabled=disabled, key=f"{prefix}_goal_{index}_value")
                goal["time_period"] = st.text_input("Time period", value=goal.get("time_period", ""), disabled=disabled, key=f"{prefix}_goal_{index}_period")
            with cols[1]:
                persona_options = [p.get("name") for p in state["draft"].get("audience_personas") or [] if p.get("name")]
                goal["target_personas"] = st.multiselect("Target personas", persona_options, default=[p for p in goal.get("target_personas", []) if p in persona_options], disabled=disabled, key=f"{prefix}_goal_{index}_personas")
                goal["preferred_platforms"] = st.multiselect("Preferred platforms", PLATFORM_OPTIONS, default=[p for p in goal.get("preferred_platforms", []) if p in PLATFORM_OPTIONS], disabled=disabled, key=f"{prefix}_goal_{index}_platforms")
            goal["description"] = st.text_area("Description", value=goal.get("description", ""), height=90, disabled=disabled, key=f"{prefix}_goal_{index}_description")
            edited.append(normalize_business_goal(goal, index))
    _sync_input(state, "business_goals", edited)


def _empty_pillar(sort_order: int = 0) -> dict:
    return normalize_content_pillar({"id": str(uuid.uuid4()), "name": "New Pillar", "content_ratio": 0}, sort_order)


def _merge_pillars(items: list, index: int) -> list:
    if index <= 0 or index >= len(items):
        return items
    previous = normalize_content_pillar(items[index - 1], index - 1)
    current = normalize_content_pillar(items[index], index)
    previous["name"] = previous.get("name") or current.get("name")
    previous["description"] = "\n".join([x for x in [previous.get("description"), current.get("description")] if x]).strip()
    previous["strategic_purpose"] = previous.get("strategic_purpose") or current.get("strategic_purpose")
    for field in ["business_goals", "target_personas", "recommended_channels", "do_guidance", "dont_guidance"]:
        previous[field] = list(dict.fromkeys((previous.get(field) or []) + (current.get(field) or [])))
    previous["content_ratio"] = int(previous.get("content_ratio") or 0) + int(current.get("content_ratio") or 0)
    previous["differentiation_angle"] = previous.get("differentiation_angle") or current.get("differentiation_angle")
    merged = list(items)
    merged[index - 1] = previous
    merged.pop(index)
    for idx, item in enumerate(merged):
        item["sort_order"] = idx
    return merged


def _render_content_pillars(state: dict, disabled: bool, prefix: str):
    pillars = normalize_content_pillars(state["draft"].get("content_pillars") or [])
    actions = st.columns(4)
    with actions[0]:
        count = st.number_input("AI pillar count", min_value=1, max_value=20, value=10, disabled=disabled, key=f"{prefix}_pillar_ai_count")
    with actions[1]:
        if st.button("Generate Pillars with AI", disabled=disabled, use_container_width=True, key=f"{prefix}_pillar_ai"):
            service = ContentStrategyService(api_key=None)
            result = service.generate_pillar_drafts(
                st.session_state.get("current_workspace_id_for_strategy", 0),
                st.session_state.get("current_company_id_for_strategy", 0),
                state["draft"],
                count=int(count),
                created_by=st.session_state.get("current_user_id_for_strategy"),
            )
            if result.get("ok"):
                _sync_input(state, "content_pillars", result.get("pillars") or [])
                st.rerun()
            _set_error(state, result.get("error"), "Generate pillars")
    with actions[2]:
        if st.button("Add Manually", disabled=disabled, use_container_width=True, key=f"{prefix}_pillar_add"):
            pillars.append(_empty_pillar(len(pillars)))
            _sync_input(state, "content_pillars", pillars)
            st.rerun()
    with actions[3]:
        active_ratio = sum(int(p.get("content_ratio") or 0) for p in pillars if p.get("status") == "active")
        st.metric("Active ratio", f"{active_ratio}%")

    errors, warnings = validate_content_pillars(pillars, state["draft"].get("business_goals") or [], state["draft"].get("audience_personas") or [])
    for message in errors:
        st.error(message)
    for message in warnings:
        st.warning(message)
    if not pillars:
        render_empty_state("No content pillars yet", "Generate pillars with AI or add a manual pillar.", icon="+")
        _sync_input(state, "content_pillars", [])
        return

    goal_options = [g.get("name") for g in normalize_business_goals(state["draft"].get("business_goals") or []) if g.get("name")]
    persona_options = [p.get("name") for p in state["draft"].get("audience_personas") or [] if p.get("name")]
    edited = []
    for index, pillar in enumerate(pillars):
        pillar = normalize_content_pillar(pillar, index)
        status_label = "active" if pillar.get("status") == "active" else "inactive"
        with st.expander(f"{index + 1}. {pillar.get('name') or 'Untitled Pillar'} ({status_label})", expanded=index == 0):
            controls = st.columns(7)
            with controls[0]:
                if st.button("Up", disabled=disabled or index == 0, key=f"{prefix}_pillar_{index}_up"):
                    _sync_input(state, "content_pillars", _move_item(pillars, index, -1))
                    st.rerun()
            with controls[1]:
                if st.button("Down", disabled=disabled or index == len(pillars) - 1, key=f"{prefix}_pillar_{index}_down"):
                    _sync_input(state, "content_pillars", _move_item(pillars, index, 1))
                    st.rerun()
            with controls[2]:
                if st.button("Duplicate", disabled=disabled, key=f"{prefix}_pillar_{index}_dup"):
                    copy_item = normalize_content_pillar({**pillar, "id": str(uuid.uuid4()), "name": f"{pillar.get('name', 'Pillar')} Copy"}, len(pillars))
                    pillars.insert(index + 1, copy_item)
                    _sync_input(state, "content_pillars", pillars)
                    st.rerun()
            with controls[3]:
                if st.button("Merge", disabled=disabled or index == 0, key=f"{prefix}_pillar_{index}_merge"):
                    _sync_input(state, "content_pillars", _merge_pillars(pillars, index))
                    st.rerun()
            with controls[4]:
                new_status = "inactive" if pillar.get("status") == "active" else "active"
                if st.button("Deactivate" if pillar.get("status") == "active" else "Activate", disabled=disabled, key=f"{prefix}_pillar_{index}_toggle"):
                    pillars[index]["status"] = new_status
                    _sync_input(state, "content_pillars", pillars)
                    st.rerun()
            with controls[5]:
                if st.button("Regenerate", disabled=disabled, key=f"{prefix}_pillar_{index}_regen"):
                    service = ContentStrategyService(api_key=None)
                    result = service.generate_pillar_drafts(
                        st.session_state.get("current_workspace_id_for_strategy", 0),
                        st.session_state.get("current_company_id_for_strategy", 0),
                        state["draft"],
                        count=1,
                        regenerate_index=index,
                        created_by=st.session_state.get("current_user_id_for_strategy"),
                    )
                    if result.get("ok"):
                        pillars[index] = normalize_content_pillar((result.get("pillars") or [pillar])[0], index)
                        _sync_input(state, "content_pillars", pillars)
                        st.rerun()
                    error = result.get("error") or {}
                    state["error"] = error.get("message") if isinstance(error, dict) else str(error)
            with controls[6]:
                confirm_delete = _confirm_checkbox("Confirm delete pillar", f"{prefix}_pillar_{index}_delete_confirm", disabled=disabled)
                if st.button("Delete", disabled=disabled or not confirm_delete, key=f"{prefix}_pillar_{index}_delete"):
                    pillars.pop(index)
                    _sync_input(state, "content_pillars", pillars)
                    st.rerun()

            cols = st.columns(2)
            with cols[0]:
                pillar["name"] = st.text_input("Name", value=pillar.get("name", ""), disabled=disabled, key=f"{prefix}_pillar_{index}_name")
                pillar["strategic_purpose"] = st.text_input("Strategic purpose", value=pillar.get("strategic_purpose", ""), disabled=disabled, key=f"{prefix}_pillar_{index}_purpose")
                pillar["priority"] = st.selectbox("Priority", PRIORITY_OPTIONS, index=PRIORITY_OPTIONS.index(pillar.get("priority", "medium")), disabled=disabled, key=f"{prefix}_pillar_{index}_priority")
                pillar["content_ratio"] = st.number_input("Content ratio", min_value=0, max_value=100, value=int(pillar.get("content_ratio") or 0), disabled=disabled, key=f"{prefix}_pillar_{index}_ratio")
                pillar["business_goals"] = st.multiselect("Business goals", goal_options, default=[g for g in pillar.get("business_goals", []) if g in goal_options], disabled=disabled, key=f"{prefix}_pillar_{index}_goals")
            with cols[1]:
                pillar["target_personas"] = st.multiselect("Target personas", persona_options, default=[p for p in pillar.get("target_personas", []) if p in persona_options], disabled=disabled, key=f"{prefix}_pillar_{index}_personas")
                pillar["recommended_channels"] = st.multiselect("Recommended channels", PLATFORM_OPTIONS, default=[p for p in pillar.get("recommended_channels", []) if p in PLATFORM_OPTIONS], disabled=disabled, key=f"{prefix}_pillar_{index}_channels")
                pillar["differentiation_angle"] = st.text_area("Differentiation angle", value=pillar.get("differentiation_angle", ""), height=90, disabled=disabled, key=f"{prefix}_pillar_{index}_diff")
            pillar["description"] = st.text_area("Description", value=pillar.get("description", ""), height=100, disabled=disabled, key=f"{prefix}_pillar_{index}_description")
            guidance = st.columns(2)
            with guidance[0]:
                pillar["do_guidance"] = [line.strip() for line in st.text_area("Do guidance", value="\n".join(pillar.get("do_guidance") or []), height=100, disabled=disabled, key=f"{prefix}_pillar_{index}_do").split("\n") if line.strip()]
            with guidance[1]:
                pillar["dont_guidance"] = [line.strip() for line in st.text_area("Don't guidance", value="\n".join(pillar.get("dont_guidance") or []), height=100, disabled=disabled, key=f"{prefix}_pillar_{index}_dont").split("\n") if line.strip()]
            edited.append(normalize_content_pillar(pillar, index))
    _sync_input(state, "content_pillars", edited)

def _empty_subtopic(pillar_id: str = "", sort_order: int = 0) -> dict:
    return normalize_subtopic({"id": str(uuid.uuid4()), "pillar_id": pillar_id, "name": "New Subtopic", "source": "manual", "manual_edits": True}, sort_order)


def _empty_angle(subtopic_id: str = "", sort_order: int = 0) -> dict:
    return normalize_content_angle({"id": str(uuid.uuid4()), "subtopic_id": subtopic_id, "working_title": "New Angle", "source": "manual", "manual_edits": True}, sort_order)


def _bulk_approve(items: list, selected_ids: list) -> list:
    selected = {str(x) for x in selected_ids or []}
    next_items = []
    for item in items:
        if str(item.get("id")) in selected:
            item = dict(item)
            item["status"] = "approved"
            item["approved"] = True
        next_items.append(item)
    return next_items


def _render_batch_summary(state: dict, key: str):
    meta = state.setdefault("draft", {}).get("generation_state", {}).get(key) or {}
    batches = meta.get("batches") or []
    progress = meta.get("progress") or {}
    if progress:
        total = progress.get("total_batches") or 0
        done = progress.get("completed_batches") or 0
        st.progress((done / total) if total else 0)
        st.caption(f"Batch progress: {done}/{total}")
    failed = [b for b in batches if b.get("status") == "failed"]
    if failed:
        st.warning("Failed batches: " + ", ".join(str(b.get("index")) for b in failed))


def _render_subtopics(state: dict, disabled: bool, prefix: str):
    draft = state["draft"]
    pillars = normalize_content_pillars(draft.get("content_pillars") or [])
    subtopics = normalize_subtopics(draft.get("subtopics") or [])
    pillar_options = {p.get("id"): p.get("name") for p in pillars if p.get("id")}
    selected_key = f"{prefix}_subtopic_selected_ids"

    controls = st.columns(5)
    with controls[0]:
        per_pillar = st.number_input("Subtopics per Pillar", min_value=1, max_value=20, value=3, disabled=disabled, key=f"{prefix}_subtopic_per")
    with controls[1]:
        batch_size = st.number_input("Generation batch size", min_value=1, max_value=25, value=3, disabled=disabled, key=f"{prefix}_subtopic_batch")
    with controls[2]:
        estimate = ContentStrategyService.estimate_generation_cost(len(pillars) * int(per_pillar), "subtopics")
        st.metric("Est. cost", f"${estimate['estimated_cost']:.6f}")
    with controls[3]:
        if st.button("Generate by AI", disabled=disabled or not pillars, use_container_width=True, key=f"{prefix}_subtopic_ai"):
            service = ContentStrategyService(api_key=None)
            result = service.generate_subtopic_batches(
                st.session_state.get("current_workspace_id_for_strategy", 0),
                st.session_state.get("current_company_id_for_strategy", 0),
                draft,
                subtopics_per_pillar=int(per_pillar),
                batch_size=int(batch_size),
                created_by=st.session_state.get("current_user_id_for_strategy"),
            )
            if result.get("ok"):
                draft.setdefault("generation_state", {})["subtopics"] = {"batches": result.get("batches", []), "progress": result.get("progress", {})}
                _sync_input(state, "subtopics", result.get("subtopics") or subtopics)
                st.rerun()
            _set_error(state, result.get("error"), "Generate pillars")
    with controls[4]:
        if st.button("Add manually", disabled=disabled or not pillars, use_container_width=True, key=f"{prefix}_subtopic_add"):
            subtopics.append(_empty_subtopic(next(iter(pillar_options.keys()), ""), len(subtopics)))
            _sync_input(state, "subtopics", subtopics)
            st.rerun()

    _render_batch_summary(state, "subtopics")
    selected_ids = st.multiselect("Bulk select", [s.get("id") for s in subtopics], format_func=lambda sid: next((s.get("name") for s in subtopics if s.get("id") == sid), sid), key=selected_key, disabled=disabled)
    bulk_cols = st.columns(3)
    with bulk_cols[0]:
        if st.button("Bulk approve", disabled=disabled or not selected_ids, key=f"{prefix}_subtopic_bulk_approve"):
            _sync_input(state, "subtopics", _bulk_approve(subtopics, selected_ids))
            st.rerun()
    with bulk_cols[1]:
        failed = [b.get("index") for b in (draft.get("generation_state", {}).get("subtopics", {}).get("batches") or []) if b.get("status") == "failed"]
        if st.button("Retry selected batch", disabled=disabled or not failed, key=f"{prefix}_subtopic_retry"):
            service = ContentStrategyService(api_key=None)
            result = service.generate_subtopic_batches(st.session_state.get("current_workspace_id_for_strategy", 0), st.session_state.get("current_company_id_for_strategy", 0), draft, int(per_pillar), int(batch_size), retry_batch_indexes=failed, created_by=st.session_state.get("current_user_id_for_strategy"))
            if result.get("ok"):
                draft.setdefault("generation_state", {})["subtopics"] = {"batches": result.get("batches", []), "progress": result.get("progress", {})}
                _sync_input(state, "subtopics", result.get("subtopics") or subtopics)
                st.rerun()
    with bulk_cols[2]:
        if st.button("Cancel", disabled=disabled, key=f"{prefix}_subtopic_cancel"):
            draft.setdefault("generation_state", {})["subtopics"] = {"cancelled": True, "batches": [], "progress": {"completed_batches": 0, "total_batches": 0}}
            state["dirty"] = True
            st.rerun()

    errors, warnings = validate_subtopics(subtopics, pillars)
    for message in errors:
        st.error(message)
    for message in warnings:
        st.warning(message)
    if not subtopics:
        render_empty_state("No subtopics yet", "Generate by AI or add a manual subtopic under a Pillar.", icon="+")
        _sync_input(state, "subtopics", [])
        return

    edited = []
    for index, item in enumerate(subtopics):
        item = normalize_subtopic(item, index)
        with st.expander(f"{index + 1}. {item.get('name') or 'Untitled'} ({item.get('source')}, {item.get('status')})", expanded=index == 0):
            actions = st.columns(8)
            with actions[0]:
                if st.button("Up", disabled=disabled or index == 0, key=f"{prefix}_subtopic_{index}_up"):
                    _sync_input(state, "subtopics", _move_item(subtopics, index, -1)); st.rerun()
            with actions[1]:
                if st.button("Down", disabled=disabled or index == len(subtopics) - 1, key=f"{prefix}_subtopic_{index}_down"):
                    _sync_input(state, "subtopics", _move_item(subtopics, index, 1)); st.rerun()
            with actions[2]:
                if st.button("Merge", disabled=disabled or index == 0, key=f"{prefix}_subtopic_{index}_merge"):
                    _sync_input(state, "subtopics", merge_subtopics(subtopics, index)); st.rerun()
            with actions[3]:
                if st.button("Split", disabled=disabled, key=f"{prefix}_subtopic_{index}_split"):
                    subtopics[index:index + 1] = split_subtopic(item); _sync_input(state, "subtopics", subtopics); st.rerun()
            with actions[4]:
                if st.button("Regenerate", disabled=disabled or item.get("source") == "manual" or item.get("manual_edits"), key=f"{prefix}_subtopic_{index}_regen"):
                    service = ContentStrategyService(api_key=None)
                    result = service.generate_subtopic_batches(st.session_state.get("current_workspace_id_for_strategy", 0), st.session_state.get("current_company_id_for_strategy", 0), draft, 1, 1, selected_pillar_ids=[item.get("pillar_id")], created_by=st.session_state.get("current_user_id_for_strategy"))
                    if result.get("ok") and result.get("subtopics"):
                        replacement = [s for s in result["subtopics"] if s.get("id") not in {x.get("id") for x in subtopics}]
                        if replacement:
                            subtopics[index] = normalize_subtopic(replacement[0], index, source="ai_generated")
                            _sync_input(state, "subtopics", subtopics); st.rerun()
            with actions[5]:
                if st.button("Approve", disabled=disabled, key=f"{prefix}_subtopic_{index}_approve"):
                    item["status"] = "approved"; item["approved"] = True
            with actions[6]:
                confirm_delete = _confirm_checkbox("Confirm delete subtopic", f"{prefix}_subtopic_{index}_delete_confirm", disabled=disabled)
                if st.button("Delete", disabled=disabled or not confirm_delete, key=f"{prefix}_subtopic_{index}_delete"):
                    subtopics.pop(index); _sync_input(state, "subtopics", subtopics); st.rerun()
            with actions[7]:
                st.caption(item.get("source"))
            cols = st.columns(2)
            with cols[0]:
                item["name"] = st.text_input("Name", value=item.get("name", ""), disabled=disabled, key=f"{prefix}_subtopic_{index}_name")
                item["pillar_id"] = st.selectbox("Pillar", list(pillar_options.keys()), index=max(0, list(pillar_options.keys()).index(item.get("pillar_id"))) if item.get("pillar_id") in pillar_options else 0, format_func=lambda pid: pillar_options.get(pid, pid), disabled=disabled or not pillar_options, key=f"{prefix}_subtopic_{index}_pillar")
                item["target_persona"] = st.text_input("Target persona", value=item.get("target_persona", ""), disabled=disabled, key=f"{prefix}_subtopic_{index}_persona")
                item["business_goal"] = st.text_input("Business goal", value=item.get("business_goal", ""), disabled=disabled, key=f"{prefix}_subtopic_{index}_goal")
                item["intent"] = st.text_input("Search or audience intent", value=item.get("intent", ""), disabled=disabled, key=f"{prefix}_subtopic_{index}_intent")
            with cols[1]:
                item["funnel_stage"] = st.selectbox("Funnel stage", FUNNEL_STAGE_OPTIONS, index=FUNNEL_STAGE_OPTIONS.index(item.get("funnel_stage", "awareness")), disabled=disabled, key=f"{prefix}_subtopic_{index}_funnel")
                item["priority"] = st.selectbox("Priority", PRIORITY_OPTIONS, index=PRIORITY_OPTIONS.index(item.get("priority", "medium")), disabled=disabled, key=f"{prefix}_subtopic_{index}_priority")
                item["trend_classification"] = st.selectbox("Evergreen/trending", TREND_CLASSIFICATION_OPTIONS, index=TREND_CLASSIFICATION_OPTIONS.index(item.get("trend_classification", "evergreen")), disabled=disabled, key=f"{prefix}_subtopic_{index}_trend")
                item["suggested_channels"] = st.multiselect("Suggested channels", PLATFORM_OPTIONS, default=[c for c in item.get("suggested_channels", []) if c in PLATFORM_OPTIONS], disabled=disabled, key=f"{prefix}_subtopic_{index}_channels")
                item["status"] = st.selectbox("Status", ["draft", "active", "approved", "archived"], index=["draft", "active", "approved", "archived"].index(item.get("status", "draft")) if item.get("status") in ["draft", "active", "approved", "archived"] else 0, disabled=disabled, key=f"{prefix}_subtopic_{index}_status")
            item["description"] = st.text_area("Description", value=item.get("description", ""), height=90, disabled=disabled, key=f"{prefix}_subtopic_{index}_description")
            edited.append(normalize_subtopic(item, index))
    _sync_input(state, "subtopics", edited)


def _render_content_angles(state: dict, disabled: bool, prefix: str):
    draft = state["draft"]
    subtopics = normalize_subtopics(draft.get("subtopics") or [])
    angles = normalize_content_angles(draft.get("content_angles") or [])
    subtopic_options = {s.get("id"): s.get("name") for s in subtopics if s.get("id")}
    controls = st.columns(5)
    with controls[0]:
        per_subtopic = st.number_input("Angles per Subtopic", min_value=1, max_value=20, value=5, disabled=disabled, key=f"{prefix}_angle_per")
    with controls[1]:
        batch_size = st.number_input("Generation batch size", min_value=1, max_value=25, value=5, disabled=disabled, key=f"{prefix}_angle_batch")
    with controls[2]:
        estimate = ContentStrategyService.estimate_generation_cost(len(subtopics) * int(per_subtopic), "angles")
        st.metric("Est. cost", f"${estimate['estimated_cost']:.6f}")
    with controls[3]:
        if st.button("Generate by AI", disabled=disabled or not subtopics, use_container_width=True, key=f"{prefix}_angle_ai"):
            service = ContentStrategyService(api_key=None)
            result = service.generate_angle_batches(st.session_state.get("current_workspace_id_for_strategy", 0), st.session_state.get("current_company_id_for_strategy", 0), draft, int(per_subtopic), int(batch_size), created_by=st.session_state.get("current_user_id_for_strategy"))
            if result.get("ok"):
                draft.setdefault("generation_state", {})["content_angles"] = {"batches": result.get("batches", []), "progress": result.get("progress", {})}
                _sync_input(state, "content_angles", result.get("content_angles") or angles)
                st.rerun()
            _set_error(state, result.get("error"), "Generate pillars")
    with controls[4]:
        if st.button("Add manually", disabled=disabled or not subtopics, use_container_width=True, key=f"{prefix}_angle_add"):
            angles.append(_empty_angle(next(iter(subtopic_options.keys()), ""), len(angles)))
            _sync_input(state, "content_angles", angles)
            st.rerun()

    _render_batch_summary(state, "content_angles")
    selected_ids = st.multiselect("Bulk select", [a.get("id") for a in angles], format_func=lambda aid: next((a.get("working_title") for a in angles if a.get("id") == aid), aid), key=f"{prefix}_angle_selected_ids", disabled=disabled)
    if st.button("Bulk approve", disabled=disabled or not selected_ids, key=f"{prefix}_angle_bulk_approve"):
        _sync_input(state, "content_angles", _bulk_approve(angles, selected_ids)); st.rerun()

    errors, warnings = validate_content_angles(angles, subtopics)
    for message in errors:
        st.error(message)
    for message in warnings:
        st.warning(message)
    if not angles:
        render_empty_state("No content angles yet", "Generate by AI or add a manual angle under a Subtopic.", icon="+")
        _sync_input(state, "content_angles", [])
        return

    edited = []
    for index, item in enumerate(angles):
        item = normalize_content_angle(item, index)
        with st.expander(f"{index + 1}. {item.get('working_title') or 'Untitled'} ({item.get('category')}, {item.get('status')})", expanded=index == 0):
            actions = st.columns(6)
            with actions[0]:
                if st.button("Up", disabled=disabled or index == 0, key=f"{prefix}_angle_{index}_up"):
                    _sync_input(state, "content_angles", _move_item(angles, index, -1)); st.rerun()
            with actions[1]:
                if st.button("Down", disabled=disabled or index == len(angles) - 1, key=f"{prefix}_angle_{index}_down"):
                    _sync_input(state, "content_angles", _move_item(angles, index, 1)); st.rerun()
            with actions[2]:
                if st.button("Regenerate", disabled=disabled or item.get("source") == "manual" or item.get("manual_edits"), key=f"{prefix}_angle_{index}_regen"):
                    service = ContentStrategyService(api_key=None)
                    result = service.generate_angle_batches(st.session_state.get("current_workspace_id_for_strategy", 0), st.session_state.get("current_company_id_for_strategy", 0), draft, 1, 1, selected_subtopic_ids=[item.get("subtopic_id")], created_by=st.session_state.get("current_user_id_for_strategy"))
                    if result.get("ok"):
                        replacement = [a for a in result.get("content_angles", []) if a.get("id") not in {x.get("id") for x in angles}]
                        if replacement:
                            angles[index] = normalize_content_angle(replacement[0], index, source="ai_generated")
                            _sync_input(state, "content_angles", angles); st.rerun()
            with actions[3]:
                if st.button("Approve", disabled=disabled, key=f"{prefix}_angle_{index}_approve"):
                    item["status"] = "approved"; item["approved"] = True
            with actions[4]:
                confirm_delete = _confirm_checkbox("Confirm delete angle", f"{prefix}_angle_{index}_delete_confirm", disabled=disabled)
                if st.button("Delete", disabled=disabled or not confirm_delete, key=f"{prefix}_angle_{index}_delete"):
                    angles.pop(index); _sync_input(state, "content_angles", angles); st.rerun()
            with actions[5]:
                st.caption(item.get("source"))
            cols = st.columns(2)
            with cols[0]:
                item["working_title"] = st.text_input("Working title", value=item.get("working_title", ""), disabled=disabled, key=f"{prefix}_angle_{index}_title")
                item["subtopic_id"] = st.selectbox("Subtopic", list(subtopic_options.keys()), index=max(0, list(subtopic_options.keys()).index(item.get("subtopic_id"))) if item.get("subtopic_id") in subtopic_options else 0, format_func=lambda sid: subtopic_options.get(sid, sid), disabled=disabled or not subtopic_options, key=f"{prefix}_angle_{index}_subtopic")
                item["category"] = st.selectbox("Category", ANGLE_CATEGORY_OPTIONS, index=ANGLE_CATEGORY_OPTIONS.index(item.get("category", "How-to")), disabled=disabled, key=f"{prefix}_angle_{index}_category")
                item["hook_idea"] = st.text_area("Hook idea", value=item.get("hook_idea", ""), height=80, disabled=disabled, key=f"{prefix}_angle_{index}_hook")
                item["core_insight"] = st.text_area("Core insight", value=item.get("core_insight", ""), height=90, disabled=disabled, key=f"{prefix}_angle_{index}_insight")
            with cols[1]:
                item["intended_emotion"] = st.text_input("Intended emotion", value=item.get("intended_emotion", ""), disabled=disabled, key=f"{prefix}_angle_{index}_emotion")
                item["target_persona"] = st.text_input("Target persona", value=item.get("target_persona", ""), disabled=disabled, key=f"{prefix}_angle_{index}_persona")
                item["funnel_stage"] = st.selectbox("Funnel stage", FUNNEL_STAGE_OPTIONS, index=FUNNEL_STAGE_OPTIONS.index(item.get("funnel_stage", "awareness")), disabled=disabled, key=f"{prefix}_angle_{index}_funnel")
                item["cta_type"] = st.text_input("CTA type", value=item.get("cta_type", ""), disabled=disabled, key=f"{prefix}_angle_{index}_cta")
                item["evidence_requirement"] = st.text_area("Evidence requirement", value=item.get("evidence_requirement", ""), height=80, disabled=disabled, key=f"{prefix}_angle_{index}_evidence")
                item["trend_classification"] = st.selectbox("Evergreen/trending", TREND_CLASSIFICATION_OPTIONS, index=TREND_CLASSIFICATION_OPTIONS.index(item.get("trend_classification", "evergreen")), disabled=disabled, key=f"{prefix}_angle_{index}_trend")
                item["priority"] = st.selectbox("Priority", PRIORITY_OPTIONS, index=PRIORITY_OPTIONS.index(item.get("priority", "medium")), disabled=disabled, key=f"{prefix}_angle_{index}_priority")
                item["risk_level"] = st.selectbox("Risk level", RISK_LEVEL_OPTIONS, index=RISK_LEVEL_OPTIONS.index(item.get("risk_level", "low")), disabled=disabled, key=f"{prefix}_angle_{index}_risk")
                item["status"] = st.selectbox("Status", ["draft", "active", "approved", "archived"], index=["draft", "active", "approved", "archived"].index(item.get("status", "draft")) if item.get("status") in ["draft", "active", "approved", "archived"] else 0, disabled=disabled, key=f"{prefix}_angle_{index}_status")
            edited.append(normalize_content_angle(item, index))
    _sync_input(state, "content_angles", edited)
def _platform_label(platform: str) -> str:
    labels = {
        "facebook": "Facebook",
        "linkedin": "LinkedIn",
        "zalo_oa": "Zalo OA",
        "tiktok": "TikTok",
        "youtube_shorts": "YouTube Shorts",
        "blog": "Blog",
        "email_newsletter": "Email Newsletter",
    }
    return labels.get(platform, platform)


def _variant_label(item: dict, angles: list) -> str:
    angle_title = next((a.get("working_title") for a in angles if str(a.get("id")) == str(item.get("angle_id"))), "Unlinked angle")
    return f"{_platform_label(item.get('platform'))} - {item.get('format')} - {angle_title}"


def _render_formats_channels(state: dict, disabled: bool, prefix: str):
    draft = state["draft"]
    angles = normalize_content_angles(draft.get("content_angles") or [])
    brand = draft.get("brand_identity") or {}
    variants = normalize_format_variants(draft.get("formats_channels") or [], brand=brand)

    if not angles:
        render_empty_state("No approved angles yet", "Create Content Angles before planning formats and channels.", icon="+")
        _sync_input(state, "formats_channels", [])
        return

    supported = ", ".join(_platform_label(p) for p in sorted(PUBLISHING_SUPPORTED_PLATFORMS))
    st.caption(f"Direct publishing is available only for: {supported}. Other destinations are managed as brief/export plans.")

    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        selected_angle_ids = st.multiselect(
            "Create from angles",
            [a.get("id") for a in angles],
            format_func=lambda aid: next((a.get("working_title") for a in angles if a.get("id") == aid), aid),
            disabled=disabled,
            key=f"{prefix}_fmt_angles",
        )
    with c2:
        selected_platforms = st.multiselect(
            "Platforms",
            PLATFORM_OPTIONS,
            default=["facebook", "linkedin"],
            format_func=_platform_label,
            disabled=disabled,
            key=f"{prefix}_fmt_platforms",
        )
    with c3:
        bulk_format = st.selectbox("Bulk format", FORMAT_OPTIONS, disabled=disabled, key=f"{prefix}_fmt_bulk")

    if st.button("Create variants", disabled=disabled or not selected_angle_ids or not selected_platforms, use_container_width=True, key=f"{prefix}_fmt_create"):
        selected_angles = [a for a in angles if a.get("id") in selected_angle_ids]
        existing_keys = {(v.get("angle_id"), v.get("platform"), v.get("format")) for v in variants}
        for angle in selected_angles:
            for platform in selected_platforms:
                candidate = recommend_format_variant(angle, platform, bulk_format, brand, len(variants))
                key = (candidate.get("angle_id"), candidate.get("platform"), candidate.get("format"))
                if key not in existing_keys:
                    variants.append(candidate)
                    existing_keys.add(key)
        _sync_input(state, "formats_channels", variants)
        st.rerun()

    c4, c5 = st.columns([1, 1])
    with c4:
        apply_ids = st.multiselect("Bulk select variants", [v.get("id") for v in variants], format_func=lambda vid: _variant_label(next((v for v in variants if v.get("id") == vid), {}), angles), disabled=disabled, key=f"{prefix}_fmt_selected")
    with c5:
        apply_format = st.selectbox("Apply format", FORMAT_OPTIONS, index=0, disabled=disabled, key=f"{prefix}_fmt_apply_format")
    if st.button("Bulk apply format", disabled=disabled or not apply_ids, key=f"{prefix}_fmt_apply"):
        for idx, item in enumerate(variants):
            if item.get("id") in apply_ids:
                item = normalize_format_variant({**item, "format": apply_format}, idx, brand=brand)
                item["production_effort"] = item.get("production_effort")
                variants[idx] = item
        _sync_input(state, "formats_channels", variants)
        st.rerun()

    errors, warnings = validate_format_variants(variants, angles, brand)
    for warning in warnings:
        st.warning(warning)
    if errors:
        st.error(" ".join(errors))

    if not variants:
        render_empty_state("No format variants yet", "Select one or more angles and platforms to create brief-level format plans.", icon="+")
        _sync_input(state, "formats_channels", [])
        return

    edited = []
    for index, item in enumerate(variants):
        item = normalize_format_variant(item, index, brand=brand)
        with st.expander(_variant_label(item, angles), expanded=index == 0):
            left, right = st.columns([1, 1])
            with left:
                item["angle_id"] = st.selectbox("Content Angle", [a.get("id") for a in angles], index=max(0, [a.get("id") for a in angles].index(item.get("angle_id"))) if item.get("angle_id") in [a.get("id") for a in angles] else 0, format_func=lambda aid: next((a.get("working_title") for a in angles if a.get("id") == aid), aid), disabled=disabled, key=f"{prefix}_fmt_{index}_angle")
                item["platform"] = st.selectbox("Platform", PLATFORM_OPTIONS, index=PLATFORM_OPTIONS.index(item.get("platform")) if item.get("platform") in PLATFORM_OPTIONS else 0, format_func=_platform_label, disabled=disabled, key=f"{prefix}_fmt_{index}_platform")
                item["format"] = st.selectbox("Format", FORMAT_OPTIONS, index=FORMAT_OPTIONS.index(item.get("format")) if item.get("format") in FORMAT_OPTIONS else 0, disabled=disabled, key=f"{prefix}_fmt_{index}_format")
                preset = PLATFORM_PRESETS.get(item["platform"], {})
                if st.button("Regenerate recommendation", disabled=disabled, key=f"{prefix}_fmt_{index}_regen"):
                    angle = next((a for a in angles if a.get("id") == item.get("angle_id")), angles[0])
                    item = recommend_format_variant(angle, item["platform"], item["format"], brand, index)
                    variants[index] = item
                    _sync_input(state, "formats_channels", variants)
                    st.rerun()
                item["target_length"] = st.text_input("Target length", value=item.get("target_length", preset.get("target_length", "")), disabled=disabled, key=f"{prefix}_fmt_{index}_length")
                item["tone_override"] = st.text_input("Tone override", value=item.get("tone_override", ""), disabled=disabled, key=f"{prefix}_fmt_{index}_tone")
                item["cta"] = st.text_input("CTA", value=item.get("cta", ""), disabled=disabled, key=f"{prefix}_fmt_{index}_cta")
            with right:
                item["hook_style"] = st.text_input("Hook style", value=item.get("hook_style", preset.get("hook_style", "")), disabled=disabled, key=f"{prefix}_fmt_{index}_hook")
                item["publishing_objective"] = st.text_input("Publishing objective", value=item.get("publishing_objective", preset.get("publishing_objective", "")), disabled=disabled, key=f"{prefix}_fmt_{index}_objective")
                item["repurposing_source"] = st.text_input("Repurposing source", value=item.get("repurposing_source", item.get("angle_id", "")), disabled=disabled, key=f"{prefix}_fmt_{index}_source")
                item["priority"] = st.selectbox("Priority", PRIORITY_OPTIONS, index=PRIORITY_OPTIONS.index(item.get("priority", "medium")), disabled=disabled, key=f"{prefix}_fmt_{index}_priority")
                status_options = FORMAT_STATUS_OPTIONS
                item["status"] = st.selectbox("Status", status_options, index=status_options.index(item.get("status")) if item.get("status") in status_options else 0, disabled=disabled, key=f"{prefix}_fmt_{index}_status")
                can_publish = item.get("platform") in PUBLISHING_SUPPORTED_PLATFORMS
                item["publishing_enabled"] = st.checkbox("Direct publishing enabled", value=bool(item.get("publishing_enabled") and can_publish), disabled=disabled or not can_publish, key=f"{prefix}_fmt_{index}_publish")
                if not can_publish:
                    st.caption("Publishing destination unsupported: this variant is plan/export only.")
            item["visual_requirement"] = st.text_area("Visual requirement", value=item.get("visual_requirement", ""), height=70, disabled=disabled, key=f"{prefix}_fmt_{index}_visual")
            item["adaptation_guidance"] = st.text_area("Platform adaptation guidance", value=item.get("adaptation_guidance", ""), height=80, disabled=disabled, key=f"{prefix}_fmt_{index}_adapt")
            item["brief"] = st.text_area("Content brief preview", value=item.get("brief", ""), height=130, disabled=disabled, key=f"{prefix}_fmt_{index}_brief")
            item = normalize_format_variant(item, index, brand=brand)
            st.caption(f"Estimated production effort: {item.get('production_effort', 'medium')}")
            confirm_delete = _confirm_checkbox("Confirm delete variant", f"{prefix}_fmt_{index}_delete_confirm", disabled=disabled)
            if st.button("Delete variant", disabled=disabled or not confirm_delete, key=f"{prefix}_fmt_{index}_delete"):
                variants.pop(index)
                _sync_input(state, "formats_channels", variants)
                st.rerun()
            edited.append(item)
    _sync_input(state, "formats_channels", edited)


def _split_multiline_input(value: str) -> list:
    items = []
    for chunk in str(value or "").replace(",", "\n").split("\n"):
        item = chunk.strip()
        if item:
            items.append(item)
    return items


def _calendar_items_dataframe(items: list) -> pd.DataFrame:
    columns = [
        "id", "date", "time", "timezone", "platform", "format", "pillar", "subtopic",
        "angle", "persona", "business_goal", "funnel_stage", "working_title", "hook",
        "cta", "campaign", "lead_magnet", "production_owner", "approval_status",
        "publishing_status", "locked", "notes", "content_mix", "promotion_type",
    ]
    rows = []
    for index, item in enumerate(items or []):
        normalized = normalize_calendar_item(item, index)
        rows.append({column: normalized.get(column, "") for column in columns})
    return pd.DataFrame(rows, columns=columns)


def _coerce_calendar_items_from_editor(df: pd.DataFrame, fallback_items: list) -> list:
    if df is None:
        return fallback_items
    records = df.fillna("").to_dict("records")
    return [normalize_calendar_item(record, index) for index, record in enumerate(records)]


def _calendar_complete(value) -> tuple[bool, list[str]]:
    calendar = normalize_content_calendar(value or {})
    items = calendar.get("items") or []
    errors = []
    if not items:
        errors.append("Content Calendar needs at least one planned item.")
    diagnostics = analyze_content_calendar(items, calendar.get("settings") or {})
    if diagnostics.get("conflicts"):
        errors.append("Content Calendar has scheduling conflicts to resolve.")
    return not errors, errors


def _render_calendar_summary(items: list, settings: dict, view: str):
    df = _calendar_items_dataframe(items)
    if df.empty:
        render_empty_state("No calendar items yet", "Generate a calendar or add rows in the editable table.", icon="+")
        return
    df["date_dt"] = pd.to_datetime(df["date"], errors="coerce")
    if view == "weekly":
        weekly = df.groupby([df["date_dt"].dt.strftime("%G-W%V"), "platform"], dropna=False).size().reset_index(name="items")
        weekly.columns = ["Week", "Platform", "Items"]
        st.dataframe(weekly, use_container_width=True, hide_index=True)
    elif view == "monthly":
        monthly = df.groupby([df["date_dt"].dt.strftime("%Y-%m"), "pillar"], dropna=False).size().reset_index(name="items")
        monthly.columns = ["Month", "Pillar", "Items"]
        st.dataframe(monthly, use_container_width=True, hide_index=True)
    elif view == "quarterly":
        quarter = df["date_dt"].dt.to_period("Q").astype(str)
        summary = df.groupby([quarter, "business_goal"], dropna=False).agg(
            Items=("id", "count"),
            Lead_Capture=("lead_magnet", lambda s: int(sum(bool(str(x).strip()) for x in s))),
            Promotional=("promotion_type", lambda s: int(sum(x == "promotional" for x in s))),
        ).reset_index()
        summary.columns = ["Quarter", "Business Goal", "Items", "Lead Capture", "Promotional"]
        st.dataframe(summary, use_container_width=True, hide_index=True)
    else:
        preview_cols = ["date", "time", "platform", "format", "pillar", "subtopic", "working_title", "approval_status", "publishing_status", "locked"]
        st.dataframe(df[preview_cols], use_container_width=True, hide_index=True)


def _render_content_calendar(state: dict, disabled: bool, prefix: str):
    draft = state["draft"]
    calendar = normalize_content_calendar(draft.get("content_calendar") or {}, draft=draft)
    settings = calendar["settings"]
    items = calendar["items"]

    st.caption("Calendar uses stable editable tables and batch actions. AI providers are not called from this screen.")
    config_cols = st.columns([1, 1, 1, 1])
    with config_cols[0]:
        start_value = st.date_input("Start date", value=_date_value(settings.get("start_date")), disabled=disabled, key=f"{prefix}_cal_start")
    with config_cols[1]:
        end_value = st.date_input("End date", value=_date_value(settings.get("end_date")), disabled=disabled, key=f"{prefix}_cal_end")
    with config_cols[2]:
        posting_frequency = st.number_input("Posts per week", min_value=1, max_value=50, value=int(settings.get("posting_frequency") or 3), disabled=disabled, key=f"{prefix}_cal_freq")
    with config_cols[3]:
        timezone = st.text_input("Timezone", value=settings.get("timezone") or DEFAULT_TIMEZONE, disabled=disabled, key=f"{prefix}_cal_tz")

    platform_default = [p for p in settings.get("platforms", []) if p in PLATFORM_OPTIONS] or ["facebook"]
    day_labels = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_default = [day_labels[i] for i in settings.get("preferred_days", [0, 1, 2, 3, 4]) if 0 <= i <= 6]
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        platforms = st.multiselect("Platforms", PLATFORM_OPTIONS, default=platform_default, format_func=_platform_label, disabled=disabled, key=f"{prefix}_cal_platforms")
    with c2:
        preferred_days = st.multiselect("Preferred posting days", day_labels, default=day_default, disabled=disabled, key=f"{prefix}_cal_days")
    with c3:
        time_slots = _split_multiline_input(st.text_area("Preferred time slots", value="\n".join(settings.get("time_slots") or ["09:00"]), height=96, disabled=disabled, key=f"{prefix}_cal_times"))

    c4, c5, c6 = st.columns([1, 1, 1])
    with c4:
        production_capacity = st.number_input("Production capacity / week", min_value=1, max_value=200, value=int(settings.get("available_production_capacity") or 20), disabled=disabled, key=f"{prefix}_cal_capacity")
    with c5:
        evergreen_ratio = st.slider("Evergreen ratio", min_value=0, max_value=100, value=int(settings.get("evergreen_ratio") or 70), disabled=disabled, key=f"{prefix}_cal_evergreen")
    with c6:
        promotional_ratio = st.slider("Promotional ratio", min_value=0, max_value=100, value=int(settings.get("promotional_ratio") or 20), disabled=disabled, key=f"{prefix}_cal_promo")

    with st.expander("Campaigns, important events, blackout dates, and pillar ratios", expanded=False):
        blackout_text = st.text_area("Blackout dates", value="\n".join(settings.get("blackout_dates") or []), height=80, disabled=disabled, key=f"{prefix}_cal_blackout")
        campaigns_text = st.text_area("Campaign periods", value=json.dumps(settings.get("campaign_periods") or [], ensure_ascii=False, indent=2), height=110, disabled=disabled, key=f"{prefix}_cal_campaigns")
        events_text = st.text_area("Important events", value=json.dumps(settings.get("important_events") or [], ensure_ascii=False, indent=2), height=110, disabled=disabled, key=f"{prefix}_cal_events")
        pillar_ratios = {}
        pillars = normalize_content_pillars(draft.get("content_pillars") or [])
        if pillars:
            ratio_cols = st.columns(min(4, max(1, len(pillars))))
            for index, pillar in enumerate(pillars):
                with ratio_cols[index % len(ratio_cols)]:
                    pillar_ratios[pillar.get("id") or pillar.get("name")] = st.number_input(
                        pillar.get("name") or f"Pillar {index + 1}",
                        min_value=0,
                        max_value=100,
                        value=int((settings.get("pillar_ratios") or {}).get(pillar.get("id"), pillar.get("content_ratio") or 0)),
                        disabled=disabled,
                        key=f"{prefix}_cal_ratio_{pillar.get('id')}",
                    )

    try:
        campaign_periods = json.loads(campaigns_text or "[]")
    except json.JSONDecodeError:
        campaign_periods = []
        st.warning("Campaign periods must be valid JSON list data.")
    try:
        important_events = json.loads(events_text or "[]")
    except json.JSONDecodeError:
        important_events = []
        st.warning("Important events must be valid JSON list data.")

    new_settings = normalize_calendar_settings({
        "start_date": str(start_value),
        "end_date": str(end_value),
        "posting_frequency": int(posting_frequency),
        "platforms": platforms,
        "preferred_days": preferred_days,
        "time_slots": time_slots,
        "timezone": timezone,
        "pillar_ratios": pillar_ratios,
        "campaign_periods": campaign_periods,
        "important_events": important_events,
        "blackout_dates": _split_multiline_input(blackout_text),
        "available_production_capacity": int(production_capacity),
        "evergreen_ratio": int(evergreen_ratio),
        "promotional_ratio": int(promotional_ratio),
        "view": settings.get("view", "list"),
        "page_size": settings.get("page_size", 50),
    }, draft=draft)

    actions = st.columns([1, 1, 1, 1])
    with actions[0]:
        if st.button("Generate Calendar", disabled=disabled, use_container_width=True, key=f"{prefix}_cal_generate"):
            generated = generate_content_calendar(draft, new_settings, existing_items=[], regenerate_unlocked=False)
            _sync_input(state, "content_calendar", generated)
            st.rerun()
    with actions[1]:
        if st.button("Auto-fill empty dates", disabled=disabled, use_container_width=True, key=f"{prefix}_cal_autofill"):
            generated = generate_content_calendar(draft, new_settings, existing_items=items, regenerate_unlocked=True)
            existing_keys = {(item["date"], item["time"], item["platform"]) for item in items}
            filled = list(items) + [item for item in generated["items"] if (item["date"], item["time"], item["platform"]) not in existing_keys]
            _sync_input(state, "content_calendar", {"settings": new_settings, "items": filled, "diagnostics": analyze_content_calendar(filled, new_settings)})
            st.rerun()
    with actions[2]:
        if st.button("Regenerate unlocked", disabled=disabled, use_container_width=True, key=f"{prefix}_cal_regen_unlocked"):
            generated = generate_content_calendar(draft, new_settings, existing_items=items, regenerate_unlocked=True)
            _sync_input(state, "content_calendar", generated)
            st.rerun()
    with actions[3]:
        view = st.selectbox("View", CALENDAR_VIEW_OPTIONS, index=CALENDAR_VIEW_OPTIONS.index(settings.get("view", "list")) if settings.get("view") in CALENDAR_VIEW_OPTIONS else 0, disabled=disabled, key=f"{prefix}_cal_view")

    diagnostics = analyze_content_calendar(items, new_settings)
    metric_cols = st.columns(4)
    metric_cols[0].metric("Items", diagnostics["total_items"])
    metric_cols[1].metric("Locked", diagnostics["locked_count"])
    metric_cols[2].metric("Conflicts", len(diagnostics["conflicts"]))
    metric_cols[3].metric("Promo %", diagnostics["promotional_ratio"])
    for conflict in diagnostics.get("conflicts", [])[:5]:
        st.error(conflict["message"])
    for repetition in diagnostics.get("repetition", [])[:5]:
        st.warning(repetition["message"])

    filter_cols = st.columns([1, 1, 2])
    with filter_cols[0]:
        filter_platform = st.selectbox("Filter platform", ["all", *PLATFORM_OPTIONS], format_func=lambda p: "All" if p == "all" else _platform_label(p), key=f"{prefix}_cal_filter_platform")
    with filter_cols[1]:
        page_size = st.number_input("Page size", min_value=10, max_value=100, value=int(new_settings.get("page_size") or 50), key=f"{prefix}_cal_page_size")
    with filter_cols[2]:
        search = st.text_input("Search", value="", key=f"{prefix}_cal_search")

    filtered = items
    if filter_platform != "all":
        filtered = [item for item in filtered if item.get("platform") == filter_platform]
    if search.strip():
        needle = search.strip().lower()
        filtered = [item for item in filtered if needle in json.dumps(item, ensure_ascii=False).lower()]
    total_pages = max(1, (len(filtered) + int(page_size) - 1) // int(page_size))
    page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, key=f"{prefix}_cal_page")
    start_idx = (int(page) - 1) * int(page_size)
    page_items = filtered[start_idx:start_idx + int(page_size)]

    selected_ids = st.multiselect(
        "Selected items",
        [item.get("id") for item in filtered],
        format_func=lambda item_id: next((f"{item.get('date')} {item.get('time')} - {item.get('working_title')}" for item in filtered if item.get("id") == item_id), item_id),
        disabled=disabled or not filtered,
        key=f"{prefix}_cal_selected",
    )
    bulk_cols = st.columns([1, 1, 1, 1, 1])
    with bulk_cols[0]:
        move_date = st.date_input("Move date", value=_date_value(new_settings.get("start_date")), disabled=disabled, key=f"{prefix}_cal_move_date")
        if st.button("Move", disabled=disabled or len(selected_ids) != 1, key=f"{prefix}_cal_move"):
            updated = move_calendar_item(items, selected_ids[0], str(move_date))
            _sync_input(state, "content_calendar", {"settings": new_settings, "items": updated, "diagnostics": analyze_content_calendar(updated, new_settings)})
            st.rerun()
    with bulk_cols[1]:
        delta_days = st.number_input("Shift days", min_value=-365, max_value=365, value=7, disabled=disabled, key=f"{prefix}_cal_delta")
        if st.button("Bulk reschedule", disabled=disabled or not selected_ids, key=f"{prefix}_cal_bulk_reschedule"):
            updated = bulk_reschedule_calendar_items(items, selected_ids, int(delta_days), timezone)
            _sync_input(state, "content_calendar", {"settings": new_settings, "items": updated, "diagnostics": analyze_content_calendar(updated, new_settings)})
            st.rerun()
    with bulk_cols[2]:
        if st.button("Duplicate", disabled=disabled or len(selected_ids) != 1, key=f"{prefix}_cal_duplicate"):
            updated = duplicate_calendar_item(items, selected_ids[0])
            _sync_input(state, "content_calendar", {"settings": new_settings, "items": updated, "diagnostics": analyze_content_calendar(updated, new_settings)})
            st.rerun()
    with bulk_cols[3]:
        if st.button("Lock selected", disabled=disabled or not selected_ids, key=f"{prefix}_cal_lock"):
            updated = lock_calendar_items(items, selected_ids, True)
            _sync_input(state, "content_calendar", {"settings": new_settings, "items": updated, "diagnostics": analyze_content_calendar(updated, new_settings)})
            st.rerun()
    with bulk_cols[4]:
        confirm_delete = _confirm_checkbox("Confirm delete selected calendar items", f"{prefix}_cal_delete_confirm", disabled=disabled or not selected_ids)
        if st.button("Delete", disabled=disabled or not selected_ids or not confirm_delete, key=f"{prefix}_cal_delete"):
            updated = delete_calendar_items(items, selected_ids)
            _sync_input(state, "content_calendar", {"settings": new_settings, "items": updated, "diagnostics": analyze_content_calendar(updated, new_settings)})
            st.rerun()

    _render_calendar_summary(filtered, new_settings, view)
    edited_df = st.data_editor(
        _calendar_items_dataframe(page_items),
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        disabled=disabled,
        key=f"{prefix}_cal_editor_{page}_{filter_platform}_{len(page_items)}",
    )
    edited_page_items = _coerce_calendar_items_from_editor(edited_df, page_items)
    if not disabled:
        page_ids = [item.get("id") for item in page_items]
        merged = []
        edited_map = {item.get("id"): item for item in edited_page_items}
        for item in items:
            merged.append(edited_map.get(item.get("id"), item) if item.get("id") in page_ids else item)
        new_ids = [item for item in edited_page_items if item.get("id") not in page_ids]
        merged.extend(new_ids)
        _sync_input(state, "content_calendar", {"settings": {**new_settings, "view": view, "page_size": int(page_size)}, "items": merged, "diagnostics": analyze_content_calendar(merged, new_settings)})

    export_df = _calendar_items_dataframe(items)
    if not export_df.empty:
        st.download_button("Export CSV", data=export_df.to_csv(index=False).encode("utf-8-sig"), file_name="content_calendar.csv", mime="text/csv", key=f"{prefix}_cal_csv")
        try:
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer) as writer:
                export_df.to_excel(writer, index=False, sheet_name="Content Calendar")
            st.download_button(
                "Export Excel",
                data=excel_buffer.getvalue(),
                file_name="content_calendar.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"{prefix}_cal_xlsx",
            )
        except Exception:
            st.caption("Excel export is unavailable because no spreadsheet writer engine is installed.")


def _kpi_dataframe(kpis: list) -> pd.DataFrame:
    columns = ["scope_level", "metric", "baseline", "target", "period", "data_source", "owner", "status", "campaign_id", "calendar_item_id", "platform"]
    rows = []
    for item in kpis or []:
        if not isinstance(item, dict):
            continue
        row = {column: item.get(column, "") for column in columns}
        if not row.get("scope_level"):
            row["scope_level"] = "strategy"
        if not row.get("status"):
            row["status"] = "tracking"
        rows.append(row)
    return pd.DataFrame(rows, columns=columns)


def _render_kpi_publishing(state: dict, disabled: bool, prefix: str):
    draft = state["draft"]
    service = ContentStrategyService(api_key=None)
    st.caption("Plan KPI and hand off planned calendar items to Content Studio. Publishing still runs only through Approval and Publishing modules.")

    kpis = draft.get("kpis") or []
    if not kpis:
        kpis = [{"scope_level": "strategy", "metric": "Reach", "baseline": 0, "target": 0, "period": "Monthly", "data_source": "Native analytics", "owner": "Marketing", "status": "tracking"}]
    edited_kpis = st.data_editor(
        _kpi_dataframe(kpis),
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        disabled=disabled,
        key=f"{prefix}_kpi_editor",
        column_config={
            "scope_level": st.column_config.SelectboxColumn("Scope", options=["strategy", "campaign", "calendar_item", "platform"]),
            "metric": st.column_config.SelectboxColumn("Metric", options=KPI_METRIC_OPTIONS),
            "status": st.column_config.SelectboxColumn("Status", options=["tracking", "at_risk", "met", "missed", "paused"]),
            "platform": st.column_config.SelectboxColumn("Platform", options=["", *PLATFORM_OPTIONS]),
        },
    )
    if not disabled:
        records = []
        for row in edited_kpis.fillna("").to_dict("records"):
            if str(row.get("metric") or "").strip():
                records.append(row)
        _sync_input(state, "kpis", records)

    strategy_id = state.get("strategy_id")
    if not strategy_id:
        st.info("Save or open a strategy before sending calendar items to Content Studio.")
        return

    try:
        calendar_items = ContentStrategyRepository.list_calendar_items(
            st.session_state.get("current_workspace_id_for_strategy"),
            st.session_state.get("current_company_id_for_strategy"),
            strategy_id,
        )
    except Exception as exc:
        st.warning(f"Could not load persisted calendar items: {exc}")
        calendar_items = []

    st.markdown("##### Publishing handoff")
    if not calendar_items:
        st.caption("No persisted calendar items are available for handoff yet.")
        return

    readiness = service.check_publishing_readiness(
        st.session_state.get("current_workspace_id_for_strategy"),
        st.session_state.get("current_company_id_for_strategy"),
        strategy_id,
    )
    status_rows = readiness.get("items", []) if readiness.get("ok") else []
    if status_rows:
        st.dataframe(pd.DataFrame(status_rows), use_container_width=True, hide_index=True)
    for issue in readiness.get("issues", []):
        st.warning(f"{issue.get('platform', '')}: {issue.get('message', '')}")

    item_options = {item["id"]: f"#{item['id']} - [{item.get('platform', '').upper()}] {item.get('title', '')[:70]}" for item in calendar_items}
    selected_ids = st.multiselect("Send selected items", list(item_options.keys()), format_func=lambda item_id: item_options[item_id], disabled=disabled, key=f"{prefix}_send_selected")
    handoff_cols = st.columns([1, 1, 1])
    with handoff_cols[0]:
        approval_required = st.checkbox("Require approval flow", value=True, disabled=disabled, key=f"{prefix}_approval_required")
    with handoff_cols[1]:
        if st.button("Send selected items", disabled=disabled or not selected_ids, use_container_width=True, key=f"{prefix}_send_btn"):
            result = service.send_selected_calendar_items_to_content_studio(
                st.session_state.get("current_workspace_id_for_strategy"),
                st.session_state.get("current_company_id_for_strategy"),
                strategy_id,
                selected_ids,
                confirmed=True,
                created_by=st.session_state.get("current_user_id_for_strategy"),
                approval_required=approval_required,
            )
            st.success(f"Created {result.get('created', 0)} draft(s); skipped {result.get('duplicates', 0)} duplicate(s).") if result.get("ok") else st.error(result.get("error") or "Handoff failed")
            st.rerun()
    with handoff_cols[2]:
        campaign_ids = sorted({item.get("campaign_id") for item in calendar_items if item.get("campaign_id")})
        if campaign_ids:
            campaign_id = st.selectbox("Campaign batch", campaign_ids, key=f"{prefix}_campaign_batch")
            if st.button("Send campaign batch", disabled=disabled, use_container_width=True, key=f"{prefix}_campaign_send"):
                result = service.send_campaign_batch_to_content_studio(
                    st.session_state.get("current_workspace_id_for_strategy"),
                    st.session_state.get("current_company_id_for_strategy"),
                    strategy_id,
                    campaign_id,
                    confirmed=True,
                    created_by=st.session_state.get("current_user_id_for_strategy"),
                    approval_required=approval_required,
                )
                st.success(f"Created {result.get('created', 0)} draft(s); skipped {result.get('duplicates', 0)} duplicate(s).") if result.get("ok") else st.error(result.get("error") or "Campaign handoff failed")
                st.rerun()

    if st.button("Check publishing readiness", use_container_width=True, key=f"{prefix}_readiness_btn"):
        st.session_state[f"{prefix}_readiness_result"] = readiness
    cached = st.session_state.get(f"{prefix}_readiness_result")
    if cached:
        if cached.get("ready"):
            st.success("Configured platforms are ready for Publishing module scheduling.")
        else:
            st.info("Configuration issues must be resolved in Publishing before scheduling or retrying.")


def _render_text_step(state: dict, field: str, label: str, helper: str, disabled: bool, prefix: str):
    value = state["draft"].get(field, "")
    if not value:
        render_empty_state(f"No {label.lower()} yet", helper, icon="+")
    _sync_input(state, field, st.text_area(label, value=value, height=220, disabled=disabled, key=f"{prefix}_{field}"))


def _render_review(state: dict, disabled: bool, prefix: str):
    draft = state["draft"]
    rows = []
    for key, label in STEP_DEFINITIONS[:-1]:
        value = draft.get(key, "")
        rows.append({"Step": label, "Status": "Complete" if value and str(value).strip() not in {"[]", "{}"} else "Empty"})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    _sync_input(state, "review_notes", st.text_area("Review notes", value=draft.get("review_notes", ""), height=160, disabled=disabled, key=f"{prefix}_review_notes"))


def _step_renderers() -> dict[str, Callable]:
    return {
        "business_context": _render_business_context,
        "brand_identity": _render_brand_identity,
        "audience_personas": _render_audience_personas,
        "business_goals": _render_business_goals,
        "content_pillars": _render_content_pillars,
        "subtopics": _render_subtopics,
        "content_angles": _render_content_angles,
        "formats_channels": _render_formats_channels,
        "content_calendar": _render_content_calendar,
        "campaigns_lead_magnets": lambda s, d, p: _render_text_step(s, "campaigns_lead_magnets", "Campaigns and Lead Magnets", "Capture offers, lead magnets, and campaign packaging notes.", d, p),
        "kpi_publishing": _render_kpi_publishing,
        "review_activate": _render_review,
    }


def _render_navigation(state: dict, service, workspace_id, company_id, can_edit, can_manage, user_id):
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        if st.button("Previous", disabled=state["step_index"] == 0, use_container_width=True):
            state["step_index"] = previous_step_index(state["step_index"])
            st.rerun()
    with c2:
        ok, errors = validate_step(state["step_index"], state["draft"])
        if errors:
            st.warning(" ".join(errors))
        elif state.get("dirty") and can_edit:
            st.info("Unsaved changes detected. Autosave will run when a strategy is open; use Save Draft to create a restore point.")
    with c3:
        if state["step_index"] < len(STEP_DEFINITIONS) - 1:
            if st.button("Next", use_container_width=True):
                next_index, errors = next_step_index(state["step_index"], state["draft"])
                if errors:
                    state["error"] = " ".join(errors)
                else:
                    state["step_index"] = next_index
                    state["error"] = ""
                st.rerun()
        else:
            if st.button("Activate", disabled=not (can_manage and state.get("strategy_id")), use_container_width=True):
                ok, errors = validate_step(state["step_index"], state["draft"])
                if not ok:
                    state["error"] = " ".join(errors)
                else:
                    result = service.activate_strategy(workspace_id, company_id, state["strategy_id"], updated_by=user_id)
                    if result.get("ok"):
                        st.success("Strategy activated.")
                    else:
                        state["error"] = result.get("error", "Activation failed")


def render_tab_content_planning_wizard(gemini_key=None, workspace_id: int = None, role="editor", user_id: int = None, user_email: str = ""):
    """Render a 365-day content planning engine based on D:\1.docx."""
    del user_email
    role = (role or "viewer").lower()
    can_edit = user_can_edit(role)
    planner_key = f"content_365_planner_{workspace_id or 'none'}"

    content_mix = [
        {"group": "Chủ đề gây tranh luận", "ratio": 25, "pillars": ["Tranh luận", "Góc nhìn CEO"]},
        {"group": "Kiến thức AI thực chiến", "ratio": 25, "pillars": ["AI Agent", "Prompt", "Chuyển đổi số", "Công cụ AI"]},
        {"group": "Case Study doanh nghiệp", "ratio": 20, "pillars": ["Case Study", "ROI"]},
        {"group": "Công cụ AI", "ratio": 15, "pillars": ["Công cụ AI", "So sánh AI"]},
        {"group": "Dự đoán xu hướng AI", "ratio": 10, "pillars": ["AI đang thay đổi doanh nghiệp", "Tin nóng AI"]},
        {"group": "Cá nhân / Hậu trường", "ratio": 5, "pillars": ["Góc nhìn CEO", "Sai lầm khi dùng AI"]},
    ]
    pillar_bank = {
        "AI đang thay đổi doanh nghiệp": ["AI thay đổi CEO", "10 vị trí AI sẽ thay đổi trước năm 2027", "Doanh nghiệp không dùng AI sẽ mất gì", "AI làm việc 24/7 có thật sự hiệu quả", "Bộ phận nào nên dùng AI đầu tiên"],
        "Tranh luận": ["CEO nên học AI hay thuê chuyên gia", "AI có tạo ra nhân viên lười suy nghĩ", "Doanh nghiệp nhỏ có nên đầu tư AI ngay", "AI thay phòng Marketing trước hay Kế toán", "AI Agent có thể thay chăm sóc khách hàng không"],
        "Sai lầm khi dùng AI": ["90% doanh nghiệp dùng ChatGPT sai cách", "Sai lầm khiến AI trả lời vô dụng", "Vì sao AI càng dùng càng kém", "Những prompt làm mất tiền API", "Sai lầm khi giao dữ liệu cho AI"],
        "Case Study": ["Tiết kiệm 500 giờ làm việc", "Sales tăng 40% nhờ AI", "Marketing giảm 70% chi phí", "CEO xem dashboard trong 5 giây", "Tự động hóa báo cáo vận hành"],
        "AI Agent": ["AI Sales Agent", "AI HR Agent", "AI Marketing Agent", "AI CEO Agent", "AI Customer Service", "AI Finance Agent", "AI Legal Agent", "AI Procurement Agent"],
        "Công cụ AI": ["10 AI miễn phí đáng dùng", "AI tạo video", "AI lập trình", "AI thiết kế", "AI phân tích dữ liệu", "AI tạo website", "AI tạo nội dung đa kênh"],
        "So sánh AI": ["ChatGPT vs Gemini", "Claude vs ChatGPT", "DeepSeek vs GPT", "Open Source AI vs Closed AI", "AI giá rẻ có đáng dùng", "Tự xây AI hay dùng SaaS"],
        "ROI": ["AI tiết kiệm bao nhiêu tiền", "Bao lâu hoàn vốn AI", "Chi phí thật của AI Agent", "Thuê nhân viên hay dùng AI", "ROI của tự động hóa quy trình"],
        "Prompt": ["10 prompt CEO", "10 prompt Sales", "10 prompt Marketing", "Prompt Excel", "Prompt Email", "Prompt phân tích doanh nghiệp", "Prompt họp giao ban"],
        "Chuyển đổi số": ["Doanh nghiệp nên bắt đầu từ đâu", "AI trước hay ERP trước", "Có nên số hóa toàn bộ", "Quy trình nào nên AI hóa trước", "Dữ liệu nào cần chuẩn hóa trước AI"],
        "Tin nóng AI": ["GPT mới giúp doanh nghiệp tiết kiệm gì", "Mô hình AI mới thay đổi cuộc chơi thế nào", "Doanh nghiệp Việt nên học gì từ xu hướng AI", "Tin AI tuần này ảnh hưởng gì đến vận hành", "Xu hướng AI nào đáng theo dõi"],
        "Góc nhìn CEO": ["Điều CEO nên giao cho AI", "Điều CEO không bao giờ nên giao AI", "Một ngày làm việc với AI", "CEO nên học Prompt hay xây AI Agent", "CEO đo hiệu quả AI bằng chỉ số nào"],
    }
    industry_options = [
        "Logistics", "AI / Automation", "Bán lẻ", "Bất động sản", "Giáo dục", "Tài chính", "Y tế", "Sản xuất", "Du lịch", "Nhà hàng / F&B", "Thương mại điện tử", "Dịch vụ chuyên nghiệp", "Khác",
    ]
    formats = ["Bài viết ngắn", "Carousel", "Reels/video ngắn", "Infographic", "Case study"]
    platforms = ["Facebook", "LinkedIn", "Zalo"]
    angle_templates = [
        "Sai lầm phổ biến", "Câu chuyện thực tế", "Trải nghiệm cá nhân", "Tranh luận", "Xu hướng", "Hướng dẫn", "Case study", "Checklist", "So sánh", "ROI", "Dự đoán", "Phản biện",
        "Before-After", "Framework", "Myth vs Fact", "Câu hỏi CEO", "Tình huống vận hành", "Bóc tách chi phí", "Quy trình 5 bước", "Bài học triển khai", "Tín hiệu thị trường", "Lỗi dữ liệu", "Use case phòng ban", "Kịch bản 24 giờ", "Thước đo KPI",
    ]
    sample_30 = [
        "AI thay đổi CEO", "Công cụ AI", "Case Study", "Tranh luận", "Prompt", "AI Agent", "ROI", "AI Marketing", "AI Sales", "AI HR", "AI Finance", "Tin AI + góc nhìn doanh nghiệp", "Sai lầm khi dùng AI", "Case Study", "AI Automation", "AI Customer Service", "Prompt CEO", "AI và nhân sự", "Tranh luận", "AI tạo video", "AI lập trình", "Chuyển đổi số", "ROI", "AI Agent", "AI trong sản xuất", "AI trong Logistics", "AI trong tài chính", "AI trong Marketing", "AI trong quản trị", "Dự đoán AI",
    ]


    def _json_compact(value) -> str:
        return json.dumps(value, ensure_ascii=False, default=str)

    def _build_ai_calendar_prompt(days: int, start: date, industry: str, target: str, selected_platforms: list[str], distribution: str, posts_per_day: int) -> str:
        total_posts = max(1, days * posts_per_day)
        platform_rule = "Dùng một chủ đề cho tất cả nền tảng trong cùng ngày." if distribution == "Một chủ đề dùng cho tất cả nền tảng" else "Luân phiên nền tảng giữa các bài."
        return f"""
Bạn là AI Content Strategist chuyên lập lịch nội dung B2B bằng tiếng Việt.

Hãy tạo lịch chủ đề nội dung bằng AI cho doanh nghiệp/ngành sau:
- Ngành: {industry}
- Đối tượng mục tiêu: {target}
- Ngày bắt đầu: {start.isoformat()}
- Số ngày: {days}
- Số bài/ngày: {posts_per_day}
- Tổng số bài cần tạo: {total_posts}
- Nền tảng: {", ".join(selected_platforms or platforms)}
- Cách phân phối: {distribution}. {platform_rule}

Ngữ cảnh định hướng, có thể dùng để tham khảo nhưng không được sao chép máy móc:
- Tỷ lệ nhóm nội dung: {_json_compact(active_content_mix)}
- Pillar/subtopic gợi ý: {_json_compact(active_pillar_bank)}
- Góc khai thác gợi ý: {_json_compact(active_angles)}
- Định dạng hợp lệ: {_json_compact(formats)}

Yêu cầu chất lượng:
- Mỗi bài phải có chủ đề cụ thể, không trùng ý trực diện.
- Chủ đề phải phù hợp ngành, đối tượng mục tiêu, nền tảng và có tính ứng dụng.
- Nếu tạo nhiều ngày, hãy phân bổ cân bằng giữa giáo dục, case study, ROI, tranh luận, hướng dẫn và niềm tin thương hiệu.
- Không bịa số liệu cụ thể nếu không có ngữ cảnh; nếu cần số liệu, dùng cách diễn đạt như "giảm chi phí", "tăng tỷ lệ", "rút ngắn thời gian".

Chỉ trả về JSON Array thuần túy, không markdown, không giải thích.
Mỗi object bắt buộc có đúng các field:
"day", "date", "platform", "industry", "group", "pillar", "format", "topic", "target", "angle", "hook", "problem", "solution", "cta".
"""

    def _build_calendar_from_ai(items: list, days: int, start: date, industry: str, target: str, selected_platforms: list[str], distribution: str, posts_per_day: int) -> pd.DataFrame:
        selected_platforms = selected_platforms or platforms
        rows = []
        used_topics = set()
        total_posts = max(1, days * posts_per_day)
        default_pillar = next(iter(active_pillar_bank.keys()), "Content")
        for index in range(total_posts):
            raw = items[index] if index < len(items) and isinstance(items[index], dict) else {}
            day_number = index // max(1, posts_per_day)
            publish_date = start + timedelta(days=day_number)
            if distribution == "Một chủ đề dùng cho tất cả nền tảng":
                platform = " + ".join(selected_platforms)
                platform_slug = "all"
            else:
                platform = str(raw.get("platform") or selected_platforms[index % len(selected_platforms)])
                platform_slug = platform.lower()
            group = str(raw.get("group") or active_content_mix[index % len(active_content_mix)]["group"])
            pillar = str(raw.get("pillar") or default_pillar)
            angle = str(raw.get("angle") or active_angles[index % len(active_angles)])
            fmt = str(raw.get("format") or formats[index % len(formats)])
            topic = str(raw.get("topic") or f"{pillar} trong ngành {industry}: {angle}").strip()
            guard = 1
            unique_topic = topic
            while unique_topic.lower() in used_topics:
                guard += 1
                unique_topic = f"{topic} - góc {guard}"
            used_topics.add(unique_topic.lower())
            rows.append({
                "Ngày": publish_date.isoformat(),
                "Tuần": int(((publish_date - start).days // 7) + 1),
                "Tháng": publish_date.strftime("%Y-%m"),
                "Nền tảng": platform,
                "platform_slug": platform_slug,
                "Ngành": str(raw.get("industry") or industry),
                "Nhóm nội dung": group,
                "Pillar": pillar,
                "Định dạng": fmt,
                "Chủ đề": unique_topic,
                "Hook 3 dòng đầu": str(raw.get("hook") or f"Nếu {target} bỏ qua {pillar.lower()}, điều gì sẽ xảy ra trong 90 ngày tới?"),
                "Vấn đề": str(raw.get("problem") or f"{target} cần một cách nhìn thực tế về {pillar.lower()} thay vì chỉ chạy theo xu hướng."),
                "Giải pháp AI": str(raw.get("solution") or f"Biến {pillar.lower()} thành quy trình AI có mục tiêu, dữ liệu đầu vào, người chịu trách nhiệm và KPI rõ ràng."),
                "Góc khác biệt": angle,
                "CTA": str(raw.get("cta") or "Doanh nghiệp của bạn đang gặp điểm nghẽn nào nhất ở chủ đề này?"),
                "Trạng thái": "planned",
                "Nguồn": "AI/Gemini",
            })
        return pd.DataFrame(rows)


    def build_ai_calendar(days: int, start: date, industry: str, target: str, selected_platforms: list[str], distribution: str, posts_per_day: int) -> pd.DataFrame:
        batch_days = max(1, 30 // max(1, posts_per_day))
        frames = []
        generated_days = 0
        while generated_days < days:
            current_days = min(batch_days, days - generated_days)
            current_start = start + timedelta(days=generated_days)
            prompt = _build_ai_calendar_prompt(current_days, current_start, industry, target, selected_platforms, distribution, posts_per_day)
            items = generate_weekly_plan_json(prompt, api_key=gemini_key)
            frames.append(_build_calendar_from_ai(items, current_days, current_start, industry, target, selected_platforms, distribution, posts_per_day))
            generated_days += current_days
        df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        used_topics = set()
        for index, topic in enumerate(df.get("Chủ đề", [])):
            base_topic = str(topic or "").strip() or "Chủ đề AI"
            unique_topic = base_topic
            guard = 1
            while unique_topic.lower() in used_topics:
                guard += 1
                unique_topic = f"{base_topic} - góc {guard}"
            used_topics.add(unique_topic.lower())
            df.at[index, "Chủ đề"] = unique_topic
        return df

    st.markdown("### Logistics Content & Marketing Planning Engine")
    st.caption("Tạo lịch chủ đề tuần, tháng hoặc 365 ngày cho doanh nghiệp Logistics: SLA, chi phí vận chuyển, fulfillment, kho bãi, case study, ROI và chăm sóc khách hàng trên Facebook, LinkedIn, Zalo.")

    if not can_edit:
        st.info("Viewer mode: bạn có thể xem và xuất kế hoạch, nhưng không thể lưu draft bài viết.")

    tabs = st.tabs(["Thiết lập kế hoạch", "12 nhóm chủ đề", "Lịch nội dung", "Chống lặp ý tưởng"])

    with tabs[0]:
        c1, c2, c3 = st.columns(3)
        with c1:
            plan_mode = st.selectbox("Chu kỳ lập lịch", ["Lịch tuần", "Lịch tháng", "Kế hoạch 365 ngày", "Tùy chỉnh"], key=f"{planner_key}_mode")
            start_date = st.date_input("Ngày bắt đầu", value=date.today(), key=f"{planner_key}_start")
            posts_per_day = st.number_input("Số bài/ngày", min_value=1, max_value=3, value=1, help="Tài liệu gốc khuyến nghị 1 bài/ngày để giữ tương tác và uy tín lâu dài.", key=f"{planner_key}_ppd")
        with c2:
            industry = st.selectbox("Ngành nghề", industry_options, key=f"{planner_key}_industry")
            if industry == "Khác":
                industry = st.text_input("Nhập ngành nghề", value="Doanh nghiệp dịch vụ", key=f"{planner_key}_industry_other")
            target_options = LOGISTICS_TARGETS if industry == "Logistics" else ["CEO", "Chủ doanh nghiệp", "Marketing Manager", "Sales Manager", "HR Manager", "Founder", "Khách hàng tiềm năng"]
            target = st.selectbox("Đối tượng mục tiêu", target_options, key=f"{planner_key}_target_{industry}")
        with c3:
            selected_platforms = st.multiselect("Nền tảng", platforms, default=platforms, key=f"{planner_key}_platforms")
            distribution = st.radio("Cách phân phối", ["Luân phiên nền tảng", "Một chủ đề dùng cho tất cả nền tảng"], horizontal=False, key=f"{planner_key}_distribution")
            custom_days = st.number_input("Số ngày tùy chỉnh", min_value=1, max_value=365, value=90, disabled=plan_mode != "Tùy chỉnh", key=f"{planner_key}_custom_days")

        active_content_mix = LOGISTICS_CONTENT_MIX if industry == "Logistics" else content_mix
        active_pillar_bank = LOGISTICS_PILLAR_BANK if industry == "Logistics" else pillar_bank
        active_angles = LOGISTICS_ANGLES + angle_templates if industry == "Logistics" else angle_templates
        days = {"Lịch tuần": 7, "Lịch tháng": 30, "Kế hoạch 365 ngày": 365}.get(plan_mode, int(custom_days))
        st.markdown("##### Tỷ lệ nội dung khuyến nghị")
        st.dataframe(pd.DataFrame(active_content_mix)[["group", "ratio"]].rename(columns={"group": "Nhóm", "ratio": "Tỷ lệ %"}), use_container_width=True, hide_index=True)

        gen_cols = st.columns([2, 1, 1])
        with gen_cols[0]:
            generate_clicked = st.button("Tạo lịch chủ đề", type="primary", use_container_width=True, key=f"{planner_key}_generate")
        with gen_cols[1]:
            st.metric("Số ngày", days)
        with gen_cols[2]:
            st.metric("Dự kiến bài", days * int(posts_per_day))
        if generate_clicked:
            try:
                with st.spinner("Gemini đang tạo lịch chủ đề..."):
                    df = build_ai_calendar(days, start_date, industry, target, selected_platforms, distribution, int(posts_per_day))
                st.session_state[planner_key] = df
                st.session_state[f"{planner_key}_last_message"] = f"Gemini đã tạo {len(df)} chủ đề không lặp cho {plan_mode.lower()}."
                st.session_state[f"{planner_key}_generated_at"] = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
                st.success(st.session_state[f"{planner_key}_last_message"])
                st.info("Lịch đã sẵn sàng ở tab Lịch nội dung. Bạn cũng có thể xem nhanh 10 dòng đầu ngay bên dưới.")
            except Exception as exc:
                st.error(f"Gemini chưa tạo được lịch chủ đề: {exc}")
                st.info("Vui lòng kiểm tra Gemini API key hoặc thử giảm số ngày nếu phản hồi AI quá dài.")

        generated_df = st.session_state.get(planner_key)
        last_message = st.session_state.get(f"{planner_key}_last_message")
        if last_message and generated_df is not None and not generated_df.empty:
            st.success(f"{last_message} Cập nhật lúc {st.session_state.get(f'{planner_key}_generated_at', 'vừa xong')}.")
            preview_cols = [col for col in ["Ngày", "Nền tảng", "Ngành", "Pillar", "Định dạng", "Chủ đề", "CTA"] if col in generated_df.columns]
            st.dataframe(generated_df[preview_cols].head(10), use_container_width=True, hide_index=True)
            st.caption("Mở tab Lịch nội dung để lọc theo tháng, nền tảng, nhóm nội dung, tải CSV hoặc lưu vào Draft Posts.")

    with tabs[1]:
        st.markdown("##### 12 nhóm chủ đề lớn từ tài liệu gốc")
        rows = []
        current_pillars = LOGISTICS_PILLAR_BANK if st.session_state.get(f"{planner_key}_industry", "Logistics") == "Logistics" else pillar_bank
        for idx, (pillar, examples) in enumerate(current_pillars.items(), start=1):
            rows.append({"Nhóm": idx, "Pillar": pillar, "Ví dụ góc khai thác": "; ".join(examples[:5])})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.markdown("##### Lịch 30 ngày mẫu")
        current_sample = LOGISTICS_SAMPLE_30 if st.session_state.get(f"{planner_key}_industry", "Logistics") == "Logistics" else sample_30
        st.dataframe(pd.DataFrame({"Ngày": list(range(1, 31)), "Chủ đề": current_sample}), use_container_width=True, hide_index=True)

    with tabs[2]:
        df = st.session_state.get(planner_key)
        if df is None or df.empty:
            render_empty_state("Chưa có lịch nội dung", "Chọn thiết lập và bấm Tạo lịch chủ đề để sinh kế hoạch tuần, tháng hoặc 365 ngày.", icon="calendar")
        else:
            filters = st.columns(4)
            with filters[0]:
                month_filter = st.selectbox("Lọc tháng", ["Tất cả", *sorted(df["Tháng"].unique().tolist())], key=f"{planner_key}_month_filter")
            with filters[1]:
                platform_filter = st.selectbox("Lọc nền tảng", ["Tất cả", *sorted(df["Nền tảng"].unique().tolist())], key=f"{planner_key}_platform_filter")
            with filters[2]:
                group_filter = st.selectbox("Lọc nhóm", ["Tất cả", *sorted(df["Nhóm nội dung"].unique().tolist())], key=f"{planner_key}_group_filter")
            with filters[3]:
                max_rows = st.number_input("Số dòng xem", min_value=10, max_value=365, value=60, key=f"{planner_key}_max_rows")
            view_df = df.copy()
            if month_filter != "Tất cả":
                view_df = view_df[view_df["Tháng"] == month_filter]
            if platform_filter != "Tất cả":
                view_df = view_df[view_df["Nền tảng"] == platform_filter]
            if group_filter != "Tất cả":
                view_df = view_df[view_df["Nhóm nội dung"] == group_filter]
            visible_cols = ["Ngày", "Tuần", "Nền tảng", "Ngành", "Nhóm nội dung", "Pillar", "Định dạng", "Chủ đề", "Hook 3 dòng đầu", "CTA", "Trạng thái"]
            st.dataframe(view_df[visible_cols].head(int(max_rows)), use_container_width=True, hide_index=True)

            csv_bytes = df.drop(columns=["platform_slug"], errors="ignore").to_csv(index=False).encode("utf-8-sig")
            action_cols = st.columns(3)
            with action_cols[0]:
                st.download_button("Tải CSV kế hoạch", data=csv_bytes, file_name="content_plan_365.csv", mime="text/csv", use_container_width=True, key=f"{planner_key}_download")
            with action_cols[1]:
                save_limit = st.number_input("Số draft muốn lưu", min_value=1, max_value=min(60, len(df)), value=min(7, len(df)), key=f"{planner_key}_save_limit")
            with action_cols[2]:
                confirm_save = st.checkbox("Xác nhận lưu draft", key=f"{planner_key}_confirm_save")
                if st.button("Lưu vào Draft Posts", disabled=not (can_edit and confirm_save), use_container_width=True, key=f"{planner_key}_save_posts"):
                    from database.models.posts import PostModel
                    created = 0
                    for _, row in df.head(int(save_limit)).iterrows():
                        content = "\n".join([
                            f"Chủ đề: {row['Chủ đề']}",
                            f"Hook: {row['Hook 3 dòng đầu']}",
                            f"Vấn đề: {row['Vấn đề']}",
                            f"Giải pháp AI: {row['Giải pháp AI']}",
                            f"Góc khác biệt: {row['Góc khác biệt']}",
                            f"CTA: {row['CTA']}",
                        ])
                        PostModel.create(
                            content=content,
                            platform=row.get("platform_slug") if row.get("platform_slug") in {"facebook", "linkedin", "zalo", "all"} else "all",
                            content_type="marketing_viral",
                            topic=row["Chủ đề"],
                            title=str(row["Chủ đề"])[:80],
                            status="draft",
                            workspace_id=workspace_id,
                            created_by=user_id,
                            ai_metadata={"source": "content_planning_365", "scheduled_date": row["Ngày"], "pillar": row["Pillar"], "format": row["Định dạng"]},
                        )
                        created += 1
                    st.success(f"Đã lưu {created} draft posts.")

    with tabs[3]:
        df = st.session_state.get(planner_key)
        if df is None or df.empty:
            st.info("Sau khi tạo lịch, hệ thống sẽ kiểm tra trùng chủ đề tại đây.")
        else:
            total = len(df)
            duplicate_topics = int(df["Chủ đề"].duplicated().sum())
            unique_pillars = int(df["Pillar"].nunique())
            unique_formats = int(df["Định dạng"].nunique())
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Tổng chủ đề", total)
            m2.metric("Chủ đề trùng", duplicate_topics)
            m3.metric("Pillar sử dụng", unique_pillars)
            m4.metric("Định dạng", unique_formats)
            st.markdown("##### Công thức duy trì 365 ngày")
            st.write("12 chủ đề lớn x khoảng 25 góc khai thác x 5 định dạng = khoảng 1.500 biến thể nội dung. Cách này giúp duy trì đăng đều mà không lặp ý tưởng trực diện.")
            st.markdown("##### Công thức tạo tương tác cho từng bài")
            st.markdown("- Hook gây tò mò trong 3 dòng đầu\n- Một vấn đề thực tế doanh nghiệp đang gặp\n- Phân tích nguyên nhân\n- Giải pháp bằng AI\n- Một góc nhìn khác biệt\n- Câu hỏi mở để khuyến khích bình luận")



