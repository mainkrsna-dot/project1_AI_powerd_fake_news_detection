# AI-Assisted Fake News Detector

A full-stack web application for analyzing potentially misleading news content using AI-assisted text and media analysis.

The application provides analysis for news text, images, and videos, along with claim verification, confidence scores, explanations, and analysis history.

## Features

- **Text Analysis**
  - Analyze news articles or claims
  - AI-assisted classification
  - Confidence score and explanation

- **Image Analysis**
  - Upload news-related images
  - Analyze visible content and contextual information

- **Video Analysis**
  - Upload video files
  - Extract representative frames
  - Analyze the extracted visual content

- **Claim Verification**
  - Submit a specific claim for AI-assisted verification
  - Receive a classification, confidence score, and explanation

- **Analysis History**
  - View previous analyses
  - Filter analysis types
  - Delete stored history

- **Multilingual Input**
  - Supports analysis requests in the selected language

- **Demo Mode**
  - Local fallback mode allows the application workflow to run without a live OpenAI API call
  - Useful for development and demonstration

- **Responsive UI**
  - React-based interface
  - Dark mode support
  - Drag-and-drop file upload

## Tech Stack

### Frontend

- React
- React Router
- Axios
- CRACO
- Tailwind CSS
- JavaScript

### Backend

- Python
- FastAPI
- Uvicorn
- OpenAI API
- Pydantic
- python-dotenv

### Database

- MongoDB for persistent analysis history in normal mode
- In-memory history storage in Demo Mode

## Architecture

```text
User
  |
  v
React Frontend
  |
  | HTTP / REST API
  v
FastAPI Backend
  |
  +-- Text Analysis
  +-- Image Analysis
  +-- Video Analysis
  +-- Claim Verification
  +-- Analysis History
        |
        +-- OpenAI API
        +-- MongoDB
