# 🤖 CFO Copilot

A Streamlit web app where a CFO can ask questions about monthly financials and get back answers with charts. This project demonstrates a simple AI agent that can interpret questions, run data functions, and return concise, board-ready answers.

## 🚀 How to Run

### 1. Setup

First, clone the repository and navigate into the project directory:

```bash
git clone <your-repo-url>
cd cfo-copilot
```

Place your `data.xlsx` file inside the `fixtures/` directory.

It's recommended to use a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

### 2. Install Dependencies

Install the required packages from `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 3. Run the Streamlit App

Launch the application by running:

```bash
streamlit run app.py
```

The app should now be open and running in your web browser!

### 4. Run Tests

To verify that the data processing logic is working correctly, you can run the included tests using `pytest`:

```bash
pytest
```

You should see all tests passing.

## 🤖 Project Structure

```
.
├── README.md
├── app.py              # Main Streamlit application
├── requirements.txt
├── agent/
│   ├── __init__.py
│   ├── planner.py      # Interprets user query and calls the right tool
│   └── tools.py        # Functions for data loading and financial calculations
├── fixtures/
│   └── data.xlsx       # All financial data (actuals, budget, cash, fx)
└── tests/
    ├── __init__.py
    └── test_tools.py   # Unit tests for the data functions
```

---

### A Note on Collaboration

This project was completed as a learning exercise with the assistance of an AI agent. It serves as a demonstration of my ability to learn new concepts and leverage modern tools to solve problems and achieve complex goals, even from a starting point of unfamiliarity. The process of building this application involved a partnership where I guided the development and learned from the AI's insights. Therefore, this project is not presented as proof of my unassisted capabilities, but as evidence of my ability to learn effectively and accomplish any task by using the resources and tools available to me.
