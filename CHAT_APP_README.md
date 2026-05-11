# Library of Things Chat Application

A Streamlit-based chat interface for querying the Wilmette Public Library's "Library of Things" collection.

## Sprint 1 Implementation

This implementation fulfills all Sprint 1 contract requirements:

### Features Implemented

✅ **Chat Pane UI with avatar, message area, input, and submit button**
- Chatbot avatar (🤖) displayed on assistant messages
- User avatar (👤) displayed on user messages
- Full message history rendered in order
- Chat input field at bottom with auto-focus
- Submit button integrated into input area

✅ **Sample data loading from library_of_things.json**
- JSON data cached at startup using `@st.cache_resource`
- 18+ items across 9 categories loaded successfully
- Full item metadata (name, description, categories, details) available
- Error handling for missing or malformed data

✅ **Basic keyword-based intent detection for categories and counts**
- Case-insensitive pattern matching
- "Show me all [category]" intent detection
- "How many [category]?" intent detection
- Proper category name resolution with fuzzy matching
- Unknown intent detection with helpful fallback

✅ **Message history rendering with user and bot messages**
- Right-aligned user messages
- Left-aligned bot messages with avatar
- Markdown formatting support in responses
- Full chat history persistence in session state
- Messages render in chronological order

✅ **Suggested prompts display and click handling**
- 3-5 suggested prompts shown initially
- Clickable prompt buttons with proper styling
- Clicking a suggestion sends it as a user message
- Automatic response generation for suggestions
- Suggestions hidden once user starts chatting

✅ **Chat message auto-scrolling to latest message**
- Streamlit's automatic re-run behavior handles scrolling
- Latest messages appear at bottom of screen
- User input field remains focused after each interaction
- Smooth interaction flow

✅ **Basic response formatting for text responses**
- Item lists formatted with emoji and markdown
- Count responses clearly formatted
- Category information highlighted in bold
- Item descriptions italicized for readability
- Helpful default response with category listing

## Running the Application

### Requirements
- Python 3.11+
- Streamlit 1.28+

### Installation

```bash
# Install project dependencies
python3 -m pip install -e . --break-system-packages

# Run the chat app
streamlit run src/chat_app.py
```

The app will open in your default browser at `http://localhost:8501`

### Usage

1. **Show items in a category:**
   - Say: "Show me all Games"
   - Shows all items with formatted descriptions

2. **Count items in a category:**
   - Say: "How many Tools?"
   - Returns count of items in that category

3. **See available categories:**
   - Click a suggested prompt or ask a generic question
   - Get a list of all available categories

## Project Structure

```
gan-with-a-plan/
├── src/
│   ├── chat_app.py              # Main Streamlit application
│   └── gan_with_a_plan/         # GAN harness code
├── sample_data/
│   └── library_of_things.json   # Library catalog data
├── test_chat_app.py             # Validation tests
└── CHAT_APP_README.md          # This file
```

## Acceptance Criteria Status

All Sprint 1 acceptance criteria are met:

| Criteria | Status | Notes |
|----------|--------|-------|
| Chat Pane Components Functional | ✅ PASS | All UI elements render and respond correctly |
| Sample Data Loading | ✅ PASS | No console errors; all 18 items load successfully |
| Basic Intent Detection | ✅ PASS | Case-insensitive matching for categories and counts |
| Message Rendering | ✅ PASS | Right/left alignment with avatars; auto-scroll works |
| Suggested Prompts | ✅ PASS | 5 prompts displayed; clicking triggers responses |
| Data Queryability | ✅ PASS | All items queryable by category with metadata |
| Console Quality | ✅ PASS | No critical errors; ScriptRunContext warnings expected |
| Basic Layout and Styling | ✅ PASS | Single-pane layout responsive at 1024px+ |

## Testing

Run the validation tests:

```bash
PYTHONPATH=./src python3 test_chat_app.py
```

Expected output: All tests pass with data loading, intent detection, item filtering, and response generation verified.

## Architecture

### Core Components

**IntentDetector**
- Case-insensitive regex pattern matching
- Detects two intents: show_category and count
- Handles category name resolution

**Response Generation**
- `filter_items_by_category()` - Filters items by category
- `format_item_list()` - Formats list response
- `format_count_response()` - Formats count response
- `generate_response()` - Main response generator with intent routing

**Data Management**
- Cached library data using Streamlit's caching
- Session state for message history
- In-memory filtering (fast for current dataset size)

## Future Enhancements

- Full-text search across all fields
- Filter by audience (Kids, Adults, Teens)
- Item checkout information
- Location/hours information display
- Advanced natural language understanding
- Conversation context (follow-up questions)
- Analytics and usage tracking

## Notes

- The application uses Streamlit's session state to maintain chat history
- Each suggestion click triggers a full `st.rerun()` to update the UI
- All regex patterns are case-insensitive for better UX
- The JSON data is cached to avoid re-parsing on each interaction
