import streamlit as st


# Helper function for running async functions
def run_async(coro):
    """Run an async function within the stored event loop."""
    return st.session_state.loop.run_until_complete(coro)
