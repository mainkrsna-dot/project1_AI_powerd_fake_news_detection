\# AI-Assisted Fake News Detector



A full-stack web application for analyzing potentially misleading news content using AI-assisted text and media analysis.



The application provides analysis for news text, images, and videos, along with claim verification, confidence scores, explanations, and analysis history.



\## Features



\- \*\*Text Analysis\*\*

&#x20; - Analyze news articles or claims

&#x20; - AI-assisted classification

&#x20; - Confidence score and explanation



\- \*\*Image Analysis\*\*

&#x20; - Upload news-related images

&#x20; - Analyze visible content and contextual information



\- \*\*Video Analysis\*\*

&#x20; - Upload video files

&#x20; - Extract representative frames

&#x20; - Analyze the extracted visual content



\- \*\*Claim Verification\*\*

&#x20; - Submit a specific claim for AI-assisted verification

&#x20; - Receive a classification, confidence score, and explanation



\- \*\*Analysis History\*\*

&#x20; - View previous analyses

&#x20; - Filter analysis types

&#x20; - Delete stored history



\- \*\*Multilingual Input\*\*

&#x20; - Supports analysis requests in the selected language



\- \*\*Demo Mode\*\*

&#x20; - Local fallback mode allows the application interface and analysis workflow to run without a live OpenAI API call

&#x20; - Useful for development and demonstration



\- \*\*Responsive UI\*\*

&#x20; - React-based interface

&#x20; - Dark mode support

&#x20; - Drag-and-drop file upload



\## Tech Stack



\### Frontend



\- React

\- React Router

\- Axios

\- CRACO

\- Tailwind CSS

\- JavaScript



\### Backend



\- Python

\- FastAPI

\- Uvicorn

\- OpenAI API

\- Pydantic

\- python-dotenv



\### Database



\- MongoDB for persistent analysis history in normal mode

\- In-memory history storage in Demo Mode



\## Architecture



```text

User

&#x20; |

&#x20; v

React Frontend

&#x20; |

&#x20; | HTTP / REST API

&#x20; v

FastAPI Backend

&#x20; |

&#x20; +-- Text Analysis

&#x20; +-- Image Analysis

&#x20; +-- Video Analysis

&#x20; +-- Claim Verification

&#x20; +-- Analysis History

&#x20;       |

&#x20;       +-- OpenAI API

&#x20;       +-- MongoDB

