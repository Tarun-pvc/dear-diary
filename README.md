<div align="center">
  <img src="dd_text.jpg" alt="Dear Diary Text Logo" width="400"/>
  <br>
  <img src="dd_simple.png" alt="Dear Diary Simple Logo" width="150"/>
</div>

# Dear Diary

Dear Diary is a personal journaling application that helps you keep track of your thoughts, memories, and daily experiences in a secure and organized manner.

## Features

- **Secure Journaling**: Keep your personal thoughts protected with authentication
- **Rich Text Editing**: Format your entries with various styling options
- **Date Organization**: Entries automatically organized by date
- **Search Capability**: Quickly find past entries
- **Customizable Themes**: Personalize your journaling experience
- **Cross-Platform**: Available on desktop and mobile devices

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Steps

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/dear_diary.git
   cd dear_diary
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

## Usage

1. Start the application:
   ```
   python main.py
   ```

2. Register a new account or log in with existing credentials

3. Create new journal entries by clicking the "New Entry" button

4. Use the calendar view to navigate through your past entries

5. Use the search functionality to find specific content

## Configuration

The application can be configured through the `config.json` file located in the application directory:

- `theme`: Change the visual theme (light, dark, custom)
- `font_size`: Adjust text display size
- `backup_location`: Set where your journal backups are stored

## Data Privacy

Your journal entries are stored locally on your device by default. If you enable cloud sync, data will be encrypted before being transferred to ensure your privacy.

## Troubleshooting

If you encounter any issues:

1. Check the logs in the `logs` directory
2. Ensure you have the latest version
3. Try reinstalling the application
4. Contact support at support@deardiaryapp.com

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Thanks to all contributors who have helped make Dear Diary better
- Special thanks to our beta testers for their valuable feedback
