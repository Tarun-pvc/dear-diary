<div align="center">
  <img src="./static/images/dd_text.jpg" alt="Dear Diary Text Logo" width="400"/>
  <br>
  <!-- <img src="./static/images/dd_simple.png" alt="Dear Diary Simple Logo" width="150"/> -->
</div>

# <img src="./static/images/dd_simple.png" alt="Dear Diary Logo" width="40" style="vertical-align:middle;margin-right:8px;"> Dear Diary

Dear Diary is a **personal journaling application** that helps you keep track of your thoughts, memories, and daily experiences in a secure and organized manner; **Buddy the friendly AI** will give you company!

## Features :writing_hand:

- **Secure Journaling**: Securely store your entries locally. 
- **Rich Text Editing**: Format your entries with various styling options
- **Date Organization**: Entries automatically organized by date
- **Ease of reflection**: Quickly find and talk about past entries through Buddy!

## Installation :gear:

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Steps

1. Clone the repository:
   ```
   git clone https://github.com/Tarun-pvc/dear-diary.git
   cd dear-diary
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows:
     ```
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage :sunglasses:

1. Start the application:
   ```
   python run.py
   ```

2. Register a new account or log in with existing credentials

3. Create new journal entries by clicking the "New Entry" button

4. Use the calendar view to navigate through your past entries

5. Use Buddy (AI Assistant) to find specific content

## Configuration :thinking:

The application can be configured through the `config.json` file located in the application directory:

- `theme`: Change the visual theme (light, dark, custom)
- `font_size`: Adjust text display size
- `backup_location`: Set where your journal backups are stored

## Data Privacy :monocle_face:	

Your journal entries are stored locally on your device by default.

## Troubleshooting :grimacing:

If you encounter any issues:

1. Check the logs in the `logs` directory
2. Ensure you have the latest version
3. Try reinstalling the application
4. Start an *issue* on github. 

## License :hugs:

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments :handshake:

- Thanks to all contributors who have helped make Dear Diary better
- Special thanks to our beta testers for their valuable feedback
