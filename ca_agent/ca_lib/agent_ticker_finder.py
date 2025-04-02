# Copyright 2025 Google, LLC
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     https://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from google.adk.agents import LlmAgent
from google.adk.tools import built_in_google_search

TICKER_FINDER_PROMPT = """
You are the "Ticker Finder," an AI agent specialized in finding stock ticker symbols for public companies.

[Goals]
Identify the official stock ticker symbol using the constraints and steps below:

Constraints:
- You must use a search tool to find the ticker symbol.
- You must verify the match.
- If you cannot find a ticker symbol, you must return an error message.

Execution Flow:
- Receive the company name.
- Use a search tool to find the official stock ticker symbol. Retrieve the ticker symbol from the results. 
- Verify that the ticker symbol matches the company name. 
- Return the ticker symbol only. Example: for the company name Apple Inc, return AAPL 
""".strip()

ticker_finder = LlmAgent(
    model="gemini-2.0-flash",
    name="ticker_finder_agent",
    description='Finds the stock ticker symbol for a given company name.',
    instruction=TICKER_FINDER_PROMPT,
    tools=[built_in_google_search],
    output_key = "ticker_finder_output",
)
