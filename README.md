# JoSAA Choice Filling Web Application

A Python-based responsive web application for tentative JoSAA college choice filling, built with Flask.

## Features

- **College & City Management**:
  - Add colleges with name and city
  - Add cities with connectivity information from Surat
  - Manage college branches with cutoff ranks

- **Choice List Management**:
  - Create multiple choice lists with colleges and branches
  - Set a main list to be displayed on the homepage
  - Reorder choices with up/down buttons
  - Import and export lists in TXT and PDF formats

- **Mobile-Friendly Design**:
  - Responsive layout works on all devices
  - Clean, minimal interface for easy use

## Technical Details

### Requirements

- Python 3.7+
- Flask
- SQLAlchemy
- pdfkit
- wkhtmltopdf (for PDF generation)

### Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd college-choice-filling-app
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Install wkhtmltopdf (required for PDF generation):
   - **Windows**: Download from [wkhtmltopdf website](https://wkhtmltopdf.org/downloads.html)
   - **macOS**: `brew install wkhtmltopdf`
   - **Linux**: `sudo apt-get install wkhtmltopdf`

5. Run the database migration script (if upgrading from a previous version):
   ```
   python migrate_db.py
   ```

### Running the Application

1. Start the Flask development server:
   ```
   python app.py
   ```

2. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

## Usage Guide

### Adding Cities and Colleges

1. First, add cities with their connectivity information from Surat
2. Then add colleges, specifying the city
3. Add branches to colleges with their cutoff ranks

### Creating Choice Lists

1. Create a new choice list with a name and creator
2. Add college-branch combinations to your list
3. Reorder them using the up/down buttons
4. Set as main list to display on the homepage

### Importing/Exporting Lists

- Export lists as PDF for printing or sharing
- Export lists as TXT for later importing
- Import previously exported TXT files to recreate lists

## License

This project is licensed under the MIT License - see the LICENSE file for details. 