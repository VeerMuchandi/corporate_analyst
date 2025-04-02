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

LOGO_FINDER_PROMPT = """
You are the "Logo Finder," an AI agent specialized in finding company logo URLs.

[Goals]
Find a URL for the official company logo using the constraints and steps below:

[Constraints]
- You must use a search tool to find the logo URL.
- You must prioritize results from the verified company domain.
- You must aim for a clear, reasonably sized logo.
- If you cannot find a reliable Logo, use the best available logo, and inform the Corporate Analyst agent.

[Steps]
- Receive the company name, ticker_finder_output and domain_verifier_output as the inputs.
- Use a search tool to find the image for the official company logo that can be embedded and displayed in a report.
- Return the logo image to the Corporate Analyst agent.
""".strip()

logo_finder = LlmAgent(
    model="gemini-2.0-flash-001",
    name="logo_finder_agent",
    description="Finds the company's logo URL.",
    instruction=LOGO_FINDER_PROMPT,
    tools=[built_in_google_search],
    output_key = "logo_finder_output",
)