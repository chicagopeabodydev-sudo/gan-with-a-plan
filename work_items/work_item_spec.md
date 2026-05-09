# Three-Panel Chat — Work Item Spec

## How it works

- By default only a single pane is displayed that is the chat interface.
- When a chat's question requires more than text for the answer, then a second pane is added to the right of the chat pane with the additional information.
- When the additional information in the second pane also has further information and the user clicks on a link (or button) to view this further information, then a third pane is added for this.

## Pane Resizing Rules

1. If only one pane is being displayed (meaning, only the chat interface) then this is positioned flush left and covers 65% of the screen.
2. If two panes are displayed, then the chat pane is resized to cover 50% of the screen and the details pane covers the other 50%.
3. If all three are opened, then the chat pane and second pane are positioned one on top of the other in the left-side 50% of the screen, and the third pane is opened in the right 50% of the screen.

## UI Components

- Chat Interface
	- One chatbot icon or avatar
	- Text area to display the chatbot's text/replies
	- Array of suggested prompts that users can click on instead of typing in a question or other text
	- Text area to receive input from the user (users do not have to enter input into this if they choose one of the suggested prompts)
	- Button to "Submit" user input
- Second Pane
	- "First Details Level" - used when the response includes lists of items (not just a simple answer)
	- Content is most likely a list of items (note: each item may have additional details, and if so then a link or button is added to see the details for each item)
	- Close button to dismiss the pane and return to viewing just the Chat Interface
- Third Pane
	- "Second Details Level" - used when the response in the Second Pane has a link for even further details about the items; when the link is clicked for a specific item in the First Details Pane, then this is where this additional information is placed 
	- Content that is driven by the type of information to display which could include text, links, images, or videos/animation
	- Close button to dismiss the third pane and return to viewing two panes

## Sample Data
There is sample data that is typical of the content the three-panel chat will be used for. The JSON file has three levels of data: top level data that only uses the Chat Interface, an array of "items" that would be appropriate for the Second Pane, and details about each item that would be appropriate for the Third Pane.
[Sample Data](./sample_data/library_of_things.json)

## Chat Interface Functionality
The Chat Interface pane should have basic funtionality to understand a question that can be answered by the sample data. It does NOT need to be a production-level chat system. It is for simple testing only, and it should be kept as minimal as possible.
