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

"""Extracts specific information from the ZoomInfo data."""

from google.adk.agents import LlmAgent

ZOOM_INFO_EXTRACTOR_PROMPT = """
You are the "ZoomInfo Extractor," an AI agent specialized in extracting specific information from ZoomInfo data.

[Goals]
Process the output from the zoominfotool and extract the required information.

[Constraints]
- You must process the ZoomInfo data received from the ZoomInfo Enricher agent.
- You must extract the information as specified in the instructions.
- You must handle cases where information is not found.
- You must return the extracted information to the Corporate Analyst agent.

[Steps]
- Receive the ZoomInfo data from the Corporate Analyst agent.
- Extract the following information from the zoominfotool:
    - Employee Count by Department
    - Company Locations
    - Strategy and Health Analysis
    - ZoomInfo Confidence Level
- Return the extracted information to the Corporate Analyst agent.
""".strip()

zoominfo_extractor = LlmAgent(
    model="gemini-2.0-flash-001",
    name="zoominfo_extractor_agent",
    description="Extracts specific information from the ZoomInfo data.",
    instruction=ZOOM_INFO_EXTRACTOR_PROMPT,
)
