import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import streamlit as st
import ui
import coachlib as cl

ui.setup("Sync", "🔄")
active = ui.client_picker()

ui.hero("Sheet Sync.",
        "Refresh the food database, push &amp; pull client data both ways — on "
        "the app&apos;s own credentials, nothing shared with SOLARos.",
        kicker="GOOGLE SHEETS")

st.markdown("#### 🗄 Food database  ·  sheet → app")
st.caption("Re-pull Proteins / Carbs / Fats / Fruits+Veg / Drinks / Supplements "
           "from your sheet's named ranges.")
if st.button("⬇️ Refresh food database"):
    try:
        import sync
        counts = sync.pull_fooddb()
        st.cache_data.clear() if hasattr(st, "cache_data") else None
        total = sum(counts.values())
        st.success(f"Refreshed {total} items: " +
                   ", ".join(f"{k} {v}" for k, v in counts.items()))
    except Exception as e:
        st.error(f"Sync failed: {e}")

st.divider()
st.markdown("#### 👤 Client data  ·  app ↔ sheet")
st.caption("Writes to a dedicated **'APP · <name>'** tab in your sheet "
           "(readable rows + an exact data blob for lossless pull-back) — it "
           "does not overwrite your template tabs.")

c1, c2 = st.columns(2)
with c1:
    st.markdown("**Push  ·  app → sheet**")
    if not active:
        st.info("Pick a client in the sidebar to push.")
    elif st.button(f"⬆️ Push “{active}” to sheet", type="primary",
                   use_container_width=True):
        try:
            import sync
            tab, n = sync.push_client(active)
            st.success(f"Pushed {active} → tab '{tab}' ({n} rows).")
        except Exception as e:
            st.error(f"Push failed: {e}")

with c2:
    st.markdown("**Pull  ·  sheet → app**")
    try:
        import sync
        remote = sync.list_app_clients()
    except Exception as e:
        remote = []
        st.caption(f"(couldn't list remote clients: {e})")
    if remote:
        pick = st.selectbox("Client tabs in sheet", remote,
                            label_visibility="collapsed")
        if st.button(f"⬇️ Pull “{pick}” from sheet", use_container_width=True):
            try:
                import sync
                rec = sync.pull_client(pick)
                st.session_state["client"] = pick
                st.success(f"Pulled {pick} from sheet into the app.")
                st.rerun()
            except Exception as e:
                st.error(f"Pull failed: {e}")
    else:
        st.info("No 'APP · …' client tabs in the sheet yet. Push one first.")

st.divider()
st.caption("Credentials: `~/Desktop/coaching_app/.secrets/` (this app's own copy). "
           "Local client store: `data/clients.json`.")
