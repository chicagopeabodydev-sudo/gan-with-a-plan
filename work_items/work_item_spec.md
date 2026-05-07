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
	- Content is driven by the type of information to display which could include text, links, images, or videos/animation
	- Close button to dismiss the pane and return to viewing just one
- Third Pane
	- Similar to the second pane it has content that is driven by the type of information to display which could include text, links, images, or videos/animation
	- Close button to dismiss the third pane and return to viewing two panes
