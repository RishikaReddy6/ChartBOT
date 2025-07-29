# ChartBOT - Smart CSV Visualizer MVP

A simple, interactive web app that turns any CSV into charts just by typing what you need. Powered by Google Gemini for natural-language parsing and Plotly for beautiful, interactive visuals.

---

## 📲 Features

-   **Natural-language prompts** Describe the chart you want (“bar chart of sales by region in 2022–2023”) and let the AI do the rest.

-   **Eight chart types** Bar, pie, line, histogram, scatter, box plot, heatmap (correlation), treemap.

-   **Automatic filtering** Ask for date or numeric ranges and the visualizations will be made on that specific range.

-   **Interactive visuals** Hover for tooltips, zoom/pan, toggle series, download as PNG—all built on Plotly.

---

## 🔧 Installation

1.  **Clone or download** this repo.
2.  **Install dependencies**:
    ```bash
    pip install streamlit pandas plotly google-generativeai
    ```
3.  **Set your Gemini API key**:  
    In `app.py`, replace the placeholder with your actual key:
    ```python
    genai.configure(api_key="<YOUR_API_KEY>")
    ```

---

## ▶️ Quick Start

1.  **Run the app**:
    ```bash
    streamlit run app.py
    ```
2.  **In your browser, you’ll see**:
    -   A file uploader to drop in your CSV.
    -   A text box to type your chart request.
    -   A `Generate` button.
3.  **Type something like**:
    > treemap of matches grouped by season and winner for 2020-2024 (from ipl matches dataset)
4.  Click **Generate**, and watch your custom chart appear.

---

## 📋 Examples

| Prompt                                                              | What It Does                                                  |
| ------------------------------------------------------------------- | ------------------------------------------------------------- |
| `bar chart of matches by city`                                      | Counts matches per city                                       |
| `histogram of target_runs`                                          | Shows distribution of target scores                           |
| `scatter plot of calories vs popularity_score`                      | Plots relationship between two numeric columns                |
| `box plot of win_by_runs grouped by venue`                          | Displays win margins per stadium                              |
| `heatmap of numeric correlations`                                   | Correlation matrix for all numeric columns                    |
| `treemap of matches by season and winner for 2021 to 2023`          | Hierarchical view of match counts by season/winner            |

---

## ⚙️ How It Works

1.  Upload CSV.
2.  Natural-language prompt is passed to Gemini.
3.  AI returns a JSON spec (chart type, columns, and filters).
4.  DataFrame is filtered (if needed).
5.  Plotly builds an interactive chart.

---

## 🛠️ Customization

-   **Add new charts**: edit `make_chart()` in `app.py`.
-   **Tweak prompts**: adjust `full_prompt` in `parse_prompt_with_gemini()` for different keys.
-   **Offline mode**: replace Gemini calls with your own rule-based parser.

---

## 🤝 Contributing

1.  Fork the repo.
2.  Create a branch (`git checkout -b feature/my-chart`).
3.  Commit your changes (`git commit -m "Add heatmap coloring"`).
4.  Push to your branch (`git push origin feature/my-chart`).
5.  Open a Pull Request.


Feel free to use, modify, and share!
