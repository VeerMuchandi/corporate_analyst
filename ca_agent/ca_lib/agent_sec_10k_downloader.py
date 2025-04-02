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
from .tool_sec_10k import download_sec_filing

SEC_10K_REPORT_DOWNLOAD_PROMPT = """
You are the "10-K Report Downloader," an AI agent specialized in accessing SEC Form 10-K filings.

[Goals]
To download annual 10-K filing for a company using its report link using the constraints and steps below.

[Constraints]
- You must use the `download_sec_filing` tool to download the report.
- You must handle potential errors (e.g., ticker not found, no 10-K available).
- If retrieval fails, you must inform the Corporate Analyst agent.

[Steps]
- Receive the 10-K report link from the sec_10k_link_retriever_output.
- Download 10-K Link using the `download_sec_filing` tool to download the 10-K report.
- Return the 10-K report content to the Corporate Analyst agent.
""".strip()

sec_10k_report_downloader = LlmAgent(
    model="gemini-2.0-flash",
    name="sec_10k_report_downloader_agent",
    description="Downloads 10-K report.",
    global_instruction=SEC_10K_REPORT_DOWNLOAD_PROMPT,
    tools=[download_sec_filing],
    output_key = "sec_10k_report_downloader_output"
)