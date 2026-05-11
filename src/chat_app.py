"""
Library of Things Chat Application
A Streamlit-based chat interface for querying the Wilmette Public Library's collection.
"""

import streamlit as st
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
import re

# Set page config
st.set_page_config(
    page_title="Library of Things Chat",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# DATA LOADING
# ============================================================================

@st.cache_resource
def load_library_data() -> Dict[str, Any]:
    """Load and cache library data from JSON file."""
    data_path = Path(__file__).parent.parent / "sample_data" / "library_of_things.json"
    try:
        with open(data_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Could not load library data from {data_path}")
        return {}
    except json.JSONDecodeError as e:
        st.error(f"Error parsing library data: {e}")
        return {}


# ============================================================================
# INTENT DETECTION
# ============================================================================

class IntentDetector:
    """Detects user intent from chat messages."""

    def __init__(self, categories: List[str]):
        self.categories = categories
        self.category_pattern = self._build_category_pattern()

    def _build_category_pattern(self) -> str:
        """Build regex pattern for categories (case-insensitive)."""
        escaped_categories = [re.escape(cat) for cat in self.categories]
        return "|".join(escaped_categories)

    def detect_show_category_intent(self, message: str) -> Optional[str]:
        """
        Detect 'Show me all [category]' intent.
        Returns the matched category name or None.
        """
        # Pattern: "show me all" or "show all" followed by category
        pattern = r"(?:show\s+(?:me\s+)?all\s+|all\s+)(" + self.category_pattern + r")"
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            # Return the matched category with proper casing
            matched_text = match.group(1)
            for cat in self.categories:
                if cat.lower() == matched_text.lower():
                    return cat
        return None

    def detect_count_intent(self, message: str) -> Optional[str]:
        """
        Detect 'How many [category]' intent.
        Returns the matched category name or None.
        """
        # Pattern: "how many" followed by category
        pattern = r"how\s+many\s+(?:items?\s+in\s+)?(" + self.category_pattern + r")"
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            matched_text = match.group(1)
            for cat in self.categories:
                if cat.lower() == matched_text.lower():
                    return cat
        return None


# ============================================================================
# RESPONSE GENERATION
# ============================================================================

def filter_items_by_category(library_data: Dict, category: str) -> List[Dict]:
    """Get all items in a specific category."""
    items = library_data.get("library_of_things", {}).get("items", [])
    return [item for item in items if category in item.get("categories", [])]


def format_item_list(items: List[Dict], category: str) -> str:
    """Format a list of items for display."""
    if not items:
        return f"No items found in the {category} category."

    response = f"📚 **{len(items)} items in {category}:**\n\n"
    for i, item in enumerate(items, 1):
        response += f"{i}. **{item['name']}**\n"
        response += f"   _{item['short_description']}_\n\n"

    return response


def format_count_response(category: str, count: int) -> str:
    """Format count response."""
    item_word = "item" if count == 1 else "items"
    return f"There are **{count}** {item_word} in the {category} category."


def generate_response(message: str, library_data: Dict, detector: IntentDetector) -> str:
    """Generate a response based on user message and detected intent."""

    # Check for show category intent
    category = detector.detect_show_category_intent(message)
    if category:
        items = filter_items_by_category(library_data, category)
        return format_item_list(items, category)

    # Check for count intent
    category = detector.detect_count_intent(message)
    if category:
        items = filter_items_by_category(library_data, category)
        return format_count_response(category, len(items))

    # Default response for unknown intent
    lib_info = library_data.get("library_of_things", {})
    categories = ", ".join(lib_info.get("categories", []))
    return (
        f"I can help you search the Library of Things! 🏫\n\n"
        f"Try asking:\n"
        f"- \"Show me all [category]\" to see items in a category\n"
        f"- \"How many [category]?\" to count items\n\n"
        f"Available categories: {categories}"
    )


# ============================================================================
# STREAMLIT UI
# ============================================================================

def initialize_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "library_data" not in st.session_state:
        st.session_state.library_data = load_library_data()


def get_suggested_prompts(library_data: Dict) -> List[str]:
    """Get suggested prompts for the user."""
    categories = library_data.get("library_of_things", {}).get("categories", [])
    suggestions = [
        "Show me all Games",
        f"How many Tools?",
        "Show me all STEM Kits",
    ]
    return suggestions


def render_chat_history():
    """Render the message history."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "👤"):
            st.markdown(message["content"])


def render_suggested_prompts(suggestions: List[str]):
    """Render suggested prompts that are clickable."""
    st.markdown("### 💡 Suggested prompts:")
    cols = st.columns(len(suggestions))

    for idx, (col, prompt) in enumerate(zip(cols, suggestions)):
        with col:
            if st.button(prompt, key=f"suggestion_{idx}", use_container_width=True):
                # Process the suggested prompt as if user typed it
                st.session_state.messages.append({
                    "role": "user",
                    "content": prompt
                })

                # Generate and add bot response
                detector = IntentDetector(
                    st.session_state.library_data.get("library_of_things", {}).get("categories", [])
                )
                response = generate_response(prompt, st.session_state.library_data, detector)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response
                })

                # Rerun to update chat
                st.rerun()


def main():
    """Main application."""
    initialize_session_state()

    # Header
    st.markdown("# 📚 Library of Things Chat")
    st.markdown("_Explore Wilmette Public Library's collection_")

    # Render chat history (auto-scrolls to bottom with rerun)
    render_chat_history()

    # User input
    if user_input := st.chat_input("Ask about items in the library..."):
        # Add user message to history
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        # Generate bot response
        detector = IntentDetector(
            st.session_state.library_data.get("library_of_things", {}).get("categories", [])
        )
        response = generate_response(user_input, st.session_state.library_data, detector)

        # Add bot response to history
        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })

        # Rerun to show new messages (auto-scrolls to bottom)
        st.rerun()

    # Show suggested prompts if no messages yet
    if not st.session_state.messages:
        st.divider()
        suggestions = get_suggested_prompts(st.session_state.library_data)
        render_suggested_prompts(suggestions)


if __name__ == "__main__":
    main()
