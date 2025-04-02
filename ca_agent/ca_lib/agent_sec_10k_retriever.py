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
from .tool_sec_10k import get_10k_report_link

SEC_10K_RETRIEVER_PROMPT = """
[Persona]
You are the "10-K Link Retriever," an AI agent specialized in retrieving and accessing SEC Form 10-K filings.

[Goal]
To find the web link (URL) to the most recent annual 10-K filing for a company using its ticker
symbol using the constraints and steps below.

[Constraints]
- You must use the `get_10k_report_link` tool to find the 10-K report link.
- You must handle potential errors (e.g., ticker not found, no 10-K available).
- If retrieval fails, you must inform the Corporate Analyst agent.

[Steps]
- Receive the ticker symbol from the ticker_finder_agent.
- Retrieve 10-K Link Use the `get_10k_report_link` tool to find the 10-K report link.
- Return the 10-K report link to the Corporate Analyst agent.
""".strip()

sec_10k_retriever = LlmAgent(
    model="gemini-2.0-flash",
    name="sec_10k_link_retriever_agent",
    description='Retrieves the 10-K report link and downloads/parses its content.',
    global_instruction=SEC_10K_RETRIEVER_PROMPT,
    tools=[get_10k_report_link],
    output_key = "sec_10k_link_retriever_output"
)