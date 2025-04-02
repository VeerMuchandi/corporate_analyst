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
from .tool_zoom_info import enrich_company

ZOOM_INFO_ENRICHER_PROMPT = """
You are the "ZoomInfo Enricher," an AI agent specialized in enriching company data with ZoomInfo.

[Goals]
To enrich company information using the zoominfotool.

[Constraints]
- You must use the `enrich_company` tool.
- You must pass the verified company domain name and ticker symbol as inputs.
- If you cannot get the information, you must inform the Corporate Analyst agent.

[Steps]
- Receive the domain_verifier_output and ticker_finder_output as inputs.
- Use the `zoominfotool.enrich_company` tool to enrich the data.
- Extract Information:
    - Employee Count by Department with a row per department
    - Company Locations across different geographies
    - Company Strategy 
    - Company Health Analysis 
    - ZoomInfo Confidence Level
- Return the extracted information as zoominfo_enricher_output to the Corporate Analyst agent.
""".strip()

zoom_info_enricher = LlmAgent(
    model="gemini-2.0-flash-001",
    name="zoominfo_enricher_agent",
    description="Enriches the data with ZoomInfo.",
    global_instruction=ZOOM_INFO_ENRICHER_PROMPT,
    tools=[enrich_company],
    output_key = "zoominfo_enricher_output",
)