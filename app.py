"""
eCom Agency AI Operations Dashboard
Demonstrates AI-powered order triage, client request handling, and ops automation.
"""

import streamlit as st
import anthropic
import json
import os
from datetime import datetime

# ── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="eCom Ops AI — Agency Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Styles ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# ── Sample Data ────────────────────────────────────────────────────────────
INITIAL_ORDERS = [
    {
        "id": "ORD-1042", "client": "StyleHaus", "type": "Bulk Restock",
        "items": 240, "value": 8400, "status": "Unreviewed",
        "priority": None, "next_action": None, "auto_handled": False,
        "created": "2026-04-13 08:12",
    },
    {
        "id": "ORD-1043", "client": "GearPeak", "type": "Rush Order",
        "items": 12, "value": 1850, "status": "Unreviewed",
        "priority": None, "next_action": None, "auto_handled": False,
        "created": "2026-04-13 09:31",
    },
    {
        "id": "ORD-1044", "client": "HomeNest Co.", "type": "Standard",
        "items": 65, "value": 3200, "status": "Unreviewed",
        "priority": None, "next_action": None, "auto_handled": False,
        "created": "2026-04-13 10:05",
    },
    {
        "id": "ORD-1045", "client": "PetPlus", "type": "Return / Refund",
        "items": 8, "value": 420, "status": "Unreviewed",
        "priority": None, "next_action": None, "auto_handled": False,
        "created": "2026-04-13 10:44",
    },
    {
        "id": "ORD-1046", "client": "FreshBrew", "type": "Delayed Shipment",
        "items": 120, "value": 5600, "status": "Unreviewed",
        "priority": None, "next_action": None, "auto_handled": False,
        "created": "2026-04-13 11:15",
    },
]

INITIAL_REQUESTS = [
    {
        "id": "REQ-201", "client": "StyleHaus", "linked_order": "ORD-1042",
        "message": "Hey, our spring collection launch is Friday and we need confirmation the bulk order ORD-1042 will arrive by Thursday. What's the ETA?",
        "status": "Open", "priority": None, "draft": None,
    },
    {
        "id": "REQ-202", "client": "GearPeak", "linked_order": "ORD-1043",
        "message": "We marked ORD-1043 as rush but haven't seen any movement. Can someone check this today?",
        "status": "Open", "priority": None, "draft": None,
    },
    {
        "id": "REQ-203", "client": "PetPlus", "linked_order": "ORD-1045",
        "message": "Some items from ORD-1045 arrived damaged. We need a replacement or refund processed ASAP.",
        "status": "Open", "priority": None, "draft": None,
    },
    {
        "id": "REQ-204", "client": "HomeNest Co.", "linked_order": "ORD-1044",
        "message": "Can you send us an updated invoice for ORD-1044 with our new billing address? The old one has an error.",
        "status": "Open", "priority": None, "draft": None,
    },
]

# ── Session State Init ─────────────────────────────────────────────────────
if "orders" not in st.session_state:
    st.session_state.orders = [o.copy() for o in INITIAL_ORDERS]
if "requests" not in st.session_state:
    st.session_state.requests = [r.copy() for r in INITIAL_REQUESTS]
if "log" not in st.session_state:
    st.session_state.log = []

# ── Claude Client ──────────────────────────────────────────────────────────
api_key = os.environ.get("ANTHROPIC_API_KEY", "")
ai_client = anthropic.Anthropic(api_key=api_key) if api_key else None


# ── Helpers ────────────────────────────────────────────────────────────────
def log_action(action: str, item_id: str, details: str):
    st.session_state.log.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "action": action,
        "item": item_id,
        "details": details,
    })


def triage_order(order: dict) -> dict:
    if not ai_client:
        return {
            "priority": "Medium",
            "reason": "No API key — add ANTHROPIC_API_KEY to run AI triage",
            "next_action": "Review manually",
            "auto_handle": False,
        }
    response = ai_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": (
                f"You are an AI ops assistant for an e-commerce agency. Triage this order:\n\n"
                f"ID: {order['id']} | Client: {order['client']} | Type: {order['type']} "
                f"| Items: {order['items']} | Value: ${order['value']}\n\n"
                "Respond with JSON only (no markdown):\n"
                '{"priority":"High|Medium|Low","reason":"one sentence","next_action":"under 12 words","auto_handle":true|false}'
            ),
        }],
    )
    try:
        return json.loads(response.content[0].text)
    except Exception:
        return {"priority": "Medium", "reason": "Parse error", "next_action": "Review manually", "auto_handle": False}


def draft_response(request: dict) -> str:
    if not ai_client:
        return "Add ANTHROPIC_API_KEY to generate AI-drafted responses."
    response = ai_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": (
                f"You are an ops coordinator at an e-commerce agency. Draft a professional reply.\n\n"
                f"Client: {request['client']}\n"
                f"Linked Order: {request['linked_order']}\n"
                f"Message: {request['message']}\n\n"
                "Write 2-3 sentences. Acknowledge the issue, give a concrete next step or ETA, close confidently. "
                "No filler phrases. Direct and professional."
            ),
        }],
    )
    return response.content[0].text


def priority_badge(p: str) -> str:
    return {"High": "🔴 High", "Medium": "🟡 Medium", "Low": "🟢 Low"}.get(p, "⬜ Pending")


# ── Header ─────────────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.title("⚡ eCom Agency — AI Operations Dashboard")
    st.caption(f"Live demo · {datetime.now().strftime('%A, %B %d, %Y %H:%M')}")
with col_h2:
    if st.button("↺ Reset Demo", type="secondary"):
        st.session_state.orders = [o.copy() for o in INITIAL_ORDERS]
        st.session_state.requests = [r.copy() for r in INITIAL_REQUESTS]
        st.session_state.log = []
        st.rerun()

st.divider()

# ── Metrics ────────────────────────────────────────────────────────────────
orders = st.session_state.orders
requests = st.session_state.requests
triaged_count = sum(1 for o in orders if o["priority"] is not None)
auto_count = sum(1 for o in orders if o["auto_handled"])
open_req_count = sum(1 for r in requests if r["status"] == "Open")
pipeline_value = sum(o["value"] for o in orders)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Orders in Queue", len(orders), f"{triaged_count} triaged")
m2.metric("Auto-Handled by AI", auto_count, f"of {len(orders)} total")
m3.metric("Open Client Requests", open_req_count)
m4.metric("Pipeline Value", f"${pipeline_value:,.0f}")

st.divider()

# ── Tabs ───────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📦  Order Queue", "💬  Client Requests", "📋  Automation Log"])

# ── Tab 1: Orders ──────────────────────────────────────────────────────────
with tab1:
    col_title, col_action = st.columns([3, 1])
    with col_title:
        st.subheader("Incoming Orders")
        st.caption("AI classifies priority and assigns next action. Low-priority standard orders are auto-handled.")
    with col_action:
        st.write("")
        if st.button("⚡ Triage All with AI", type="primary", key="triage_all"):
            with st.spinner("Running AI triage on all orders..."):
                for i, order in enumerate(st.session_state.orders):
                    if order["priority"] is None:
                        result = triage_order(order)
                        st.session_state.orders[i]["priority"] = result["priority"]
                        st.session_state.orders[i]["next_action"] = result["next_action"]
                        if result.get("auto_handle"):
                            st.session_state.orders[i]["status"] = "Auto-Handled"
                            st.session_state.orders[i]["auto_handled"] = True
                        else:
                            st.session_state.orders[i]["status"] = "Needs Review"
                        log_action(
                            "AI Triage", order["id"],
                            f"{result['priority']} priority — {result['next_action']}"
                        )
            st.rerun()

    st.write("")
    for i, order in enumerate(st.session_state.orders):
        with st.container(border=True):
            c1, c2, c3, c4, c5, c6 = st.columns([1.2, 2, 2, 1, 1.5, 2])
            c1.write(f"**{order['id']}**")
            c2.write(order["client"])
            c3.write(order["type"])
            c4.write(f"**${order['value']:,}**")

            if order["priority"]:
                c5.write(priority_badge(order["priority"]))
                c6.write(f"_{order['status']}_")
            else:
                c5.write("⬜ Pending")
                if c6.button("Triage", key=f"t_{order['id']}", type="secondary"):
                    with st.spinner(f"Triaging {order['id']}..."):
                        result = triage_order(order)
                        st.session_state.orders[i]["priority"] = result["priority"]
                        st.session_state.orders[i]["next_action"] = result["next_action"]
                        if result.get("auto_handle"):
                            st.session_state.orders[i]["status"] = "Auto-Handled"
                            st.session_state.orders[i]["auto_handled"] = True
                        else:
                            st.session_state.orders[i]["status"] = "Needs Review"
                        log_action("AI Triage", order["id"],
                                   f"{result['priority']} priority — {result['next_action']}")
                    st.rerun()

            if order.get("next_action"):
                st.caption(f"→ **Next action:** {order['next_action']}")

# ── Tab 2: Client Requests ─────────────────────────────────────────────────
with tab2:
    col_title2, col_action2 = st.columns([3, 1])
    with col_title2:
        st.subheader("Client Requests")
        st.caption("Claude drafts responses based on order context. Review and approve before sending.")
    with col_action2:
        st.write("")
        if st.button("⚡ Draft All Responses", type="primary", key="draft_all"):
            with st.spinner("Generating AI responses..."):
                for i, req in enumerate(st.session_state.requests):
                    if req["draft"] is None and req["status"] == "Open":
                        draft = draft_response(req)
                        st.session_state.requests[i]["draft"] = draft
                        log_action("AI Draft", req["id"], f"Draft generated for {req['client']}")
            st.rerun()

    st.write("")
    for i, req in enumerate(st.session_state.requests):
        status_icon = "✅" if req["status"] == "Sent" else "🔵" if req["draft"] else "⚪"
        with st.container(border=True):
            c1, c2, c3 = st.columns([2.5, 5, 1.5])
            c1.write(f"**{req['id']}** — {req['client']}")
            c1.caption(f"Re: {req['linked_order']}")
            msg = req["message"]
            c2.write(f"_{msg[:100]}{'...' if len(msg) > 100 else ''}_")

            if req["status"] == "Sent":
                c3.write("✅ Sent")
            elif req["draft"] is None:
                if c3.button("Draft Reply", key=f"d_{req['id']}"):
                    with st.spinner("Drafting..."):
                        draft = draft_response(req)
                        st.session_state.requests[i]["draft"] = draft
                        log_action("AI Draft", req["id"], f"Draft generated for {req['client']}")
                    st.rerun()
            else:
                c3.write("📝 Review draft")

            if req["draft"] and req["status"] != "Sent":
                st.info(f"**AI Draft:** {req['draft']}")
                col_a, col_b, _ = st.columns([1.2, 1.2, 4])
                if col_a.button("✓ Approve & Send", key=f"a_{req['id']}", type="primary"):
                    st.session_state.requests[i]["status"] = "Sent"
                    log_action("Response Sent", req["id"], f"Approved and sent to {req['client']}")
                    st.rerun()
                if col_b.button("✗ Discard", key=f"dis_{req['id']}"):
                    st.session_state.requests[i]["draft"] = None
                    st.rerun()

# ── Tab 3: Automation Log ──────────────────────────────────────────────────
with tab3:
    st.subheader("Automation Log")
    st.caption("Every AI action is logged here. In production this feeds into your reporting and audit trail.")

    log = st.session_state.log
    if not log:
        st.info(
            "No actions logged yet. "
            "Click 'Triage All with AI' on the Orders tab or 'Draft All Responses' on Client Requests to see the log populate."
        )
    else:
        total_actions = len(log)
        ai_actions = sum(1 for e in log if e["action"] in ("AI Triage", "AI Draft"))
        auto_handled_log = sum(1 for e in log if "Auto-Handled" in e.get("details", ""))

        lm1, lm2, lm3 = st.columns(3)
        lm1.metric("Total Actions", total_actions)
        lm2.metric("AI-Powered", ai_actions)
        lm3.metric("Auto-Handled", auto_handled_log)

        st.write("")
        for entry in reversed(log):
            action_icon = {"AI Triage": "🤖", "AI Draft": "✍️", "Response Sent": "📤"}.get(entry["action"], "•")
            st.write(f"`{entry['time']}` {action_icon} **{entry['action']}** · `{entry['item']}` — {entry['details']}")
