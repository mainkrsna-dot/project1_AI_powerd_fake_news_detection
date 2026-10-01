# AI-Assisted Fake News Detector

A full-stack web application for analyzing potentially misleading news content using AI-assisted text and media analysis.

The application supports text, image, and video analysis, claim verification, confidence scores, explanations, multilingual input, and analysis history. A Demo Mode is also included so the complete application workflow can be demonstrated without a live OpenAI API call.

## Live Demo

**Frontend:** https://mainkrsna-dot.github.io/project1_AI_powerd_fake_news_detection/

**Backend API:** https://project1-ai-powerd-fake-news-detection.onrender.com/api/

> **Deployment:** The React frontend is hosted on GitHub Pages and the FastAPI backend is deployed on Render. The public deployment currently runs in Demo Mode, so the complete application workflow is available without requiring paid OpenAI API credits.

## Screenshots

### Home / Hero

![Home / Hero](screenshots/home.png)

### Text Analysis

![Text Analysis](screenshots/text-analysis.png)

### Text Analysis Result

![Text Analysis Result](screenshots/text-analysis-result.png)

### Image Analysis

![Image Analysis](screenshots/image-analysis.png)

### Video Analysis

![Video Analysis](screenshots/video-analysis.png)

### Analysis History

![Analysis History](screenshots/history.png)

## Features

- **Text Analysis** — Analyze news articles or claims with AI-assisted classification, confidence scores, and explanations.
- **Image Analysis** — Upload news-related images and analyze visible and contextual information.
- **Video Analysis** — Upload videos, extract representative frames, and analyze the extracted visual content.
- **Claim Verification** — Submit a specific claim for AI-assisted verification.
- **Analysis History** — View, filter, and delete previous analyses.
- **Multilingual Input** — Supports English, Hindi, Marathi, Tamil, and Hinglish workflows.
- **Demo Mode** — Fallback analysis when a live OpenAI API call is unavailable.
- **Responsive UI** — React-based interface with dark mode and drag-and-drop file upload.

## How It Works

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
       +-- OpenAI API (normal mode)
       +-- MongoDB (normal mode)
       +-- In-memory history (Demo Mode)
