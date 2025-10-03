# AI Net Cafe Hunter Specification

## 1. Objective

To build an AI agent that finds the cheapest internet cafe (net cafe) in Japan for an overnight stay (8 PM to 8 AM) near a user-specified train station.

## 2. System Architecture

The agent will be a Python application running on Ubuntu 24. It will perform the following steps:
1.  Take a Japanese train station name as input.
2.  Use a search engine to find nearby net cafes.
3.  Scrape the websites of the search results for pricing and plan information.
4.  Clean and store the scraped data as Markdown.
5.  Use a Large Language Model (LLM) to analyze each cafe's data and determine the cheapest plan for the specified time frame.
6.  Consolidate the individual analyses.
7.  Use the LLM again to compare all cafes and identify the single cheapest option.

## 3. Technologies

-   **Execution Environment:** Python on Ubuntu 24
-   **Package Management:** `uv`
-   **Web Search:** SearxNG
-   **Web Scraping:** Headless Chrome (via a library like Selenium or Playwright)
-   **HTML Parsing:** BeautifulSoup
-   **AI/LLM Orchestration:** Langgraph
-   **LLM:** Google Gemini Flash (`gemini-flash-latest`)
-   **Configuration:** Python-dotenv (`.env` file)

## 4. Configuration (`.env`)

The `.env` file will store sensitive and environment-specific variables. This allows for flexible configuration without changing the code.

```ini
# .env

# --- API Keys and URLs ---
GEMINI_API_KEY="your-api-key-here"
SEARXNG_INSTANCE_URL="http://localhost:8888"

# --- Search and Scraping Parameters ---
# Maximum number of cafes to scrape from search results.
MAX_CAFES_TO_SEARCH=10

# --- Analysis Parameters ---
# The desired start and end time for the stay (HH:MM format). The script will calculate the cheapest plan for this duration.
STAY_START_TIME="20:00"
STAY_END_TIME="08:00"
# The maximum acceptable price in JPY. Cafes exceeding this will be filtered out.
MAX_PRICE_JPY=5000
# The specific Gemini model to be used for analysis.
LLM_MODEL="gemini-flash-latest"

# --- Data Management ---
# The number of days to keep scraped data before it's considered stale.
DATA_TTL_DAYS=7
```

## 5. Workflow

### Step 1: User Input
-   The script will accept a single parameter: `train_station_name`.

### Step 2: Web Search
-   The agent will construct a search query (e.g., `"{train_station_name}駅 ネットカフェ"`).
-   It will query the configured SearxNG instance to get a list of net cafe websites, respecting the `MAX_CAFES_TO_SEARCH` limit from the `.env` file.

### Step 3: Scraping and Parsing
-   For each of the top search result URLs:
    -   A headless Chrome instance will navigate to the URL.
    -   The full page content will be retrieved.
    -   BeautifulSoup will be used to parse the HTML and extract all visible text content.

### Step 4: Data Cleaning and Storage
-   The extracted text content for a single net cafe will be processed to remove links and duplicate lines.
-   This cleaned content will be saved as a Markdown file in the `data/` directory.
-   The filename will be based on the cafe name or a hash of its URL.
-   Files in the `data/` directory older than `DATA_TTL_DAYS` will be automatically deleted at the start of a new run.

### Step 5: Individual Cafe Analysis (LLM)
-   The agent will iterate through each fresh Markdown file in the `data/` directory.
-   For each file, it will use Langgraph to construct a prompt for the model specified in `LLM_MODEL`.
-   **Prompt Goal:** The prompt will be dynamically generated using `STAY_START_TIME` and `STAY_END_TIME`. For example: "Analyze the following text and calculate the cheapest possible combination of packs or plans to stay from 20:00 to 08:00. Report the plan combination and the total cost in JPY."
-   The LLM's response for each cafe will be saved as a separate Markdown file in the `llm_reports/` directory.

### Step 6: Final Report and Recommendation
-   All individual reports from `llm_reports/` will be gathered.
-   Any report where the total cost exceeds `MAX_PRICE_JPY` will be filtered out.
-   The remaining reports will be concatenated into a single file named `all_reports.md`.
-   This combined file will be sent to the LLM with a final prompt.
-   **Prompt Goal:** "From the following reports, identify the net cafe with the absolute cheapest plan and state its name and total cost."
-   The final recommendation will be printed to the console.

## 6. Folder Structure

```
/home/user/ai_cafe/
├── .env
├── .gitignore
├── data/
│   ├── (scraped_cafe_1.md)
│   └── (scraped_cafe_2.md)
├── llm_reports/
│   ├── (report_cafe_1.md)
│   └── (report_cafe_2.md)
├── all_reports.md
├── main.py
├── requirements.txt
└── spec.md
```
