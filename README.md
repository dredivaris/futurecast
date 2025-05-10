# FutureCast

A prediction app that recursively makes LLM calls to project the cascading impacts of real-world scenarios.

## Overview

FutureCast is a tool that helps you explore the potential cascading effects of events. Using an initial scenario as input, it uses the Gemini AI model to:

1. Generate immediate (first-order) effects
2. For each of those effects, generate second-order effects
3. Continue this recursive process to the specified depth
4. Provide a comprehensive summary of the projected outcomes

## Features

- Recursive prediction of effects up to 5 levels deep
- Configurable number of effects per level
- Interactive web interface built with Streamlit
- Caching to improve performance and reduce API costs
- Parallel API calls for faster generation
- Comprehensive summaries that integrate all predicted effects

## Installation

### Prerequisites

- Python 3.8 or higher
- uv package manager

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/futurecast-augment.git
   cd futurecast-augment
   ```

2. Create a virtual environment and install dependencies:
   ```
   uv venv
   uv pip install -e .
   ```

3. Create a `.env` file in the project root with your Gemini API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

## Usage

### Running the Web Interface

```
streamlit run src/main.py
```

This will start the Streamlit web interface, which you can access in your browser.

### Configuration

You can configure the following parameters in the web interface:

- **Effects per level**: The number of effects to generate at each level (default: 5)
- **Maximum depth**: The maximum depth of the prediction tree (default: 3)
- **Model**: The Gemini model to use (default: gemini-2.0-flash)
- **Temperature**: Controls randomness in generation (default: 0.7)
- **Top-p**: Controls diversity in generation (default: 0.95)
- **Caching**: Enable/disable caching of API responses (default: enabled)


## License

MIT

