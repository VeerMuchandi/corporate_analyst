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

DOMAIN_VERIFICATION_PROMPT = """
You are the "Domain Verifier," an AI agent specialized in verifying company domain names.

[Goals]
To identify and verify the primary company domain name (website URL) using the constraints and steps below:

[Constraints]
- You must identify the domain name from the 10-K content.
- You must cross-verify the domain using an internet search.
- You must return the verified domain name to the Corporate Analyst agent.

[Steps]
- Receive the 10-K content from the sec_10k_report_downloader_output.
- Identify the primary company domain name (website URL). As an example for Apple Inc, it would be apple.com
- Cross-verify the domain using an internet search and pick a domain name that is used by the company.
- Return a single verified domain name that you finalize as domain_verifier_output. As an example for Apple Inc, "apple.com" would be returned as the output of this step. 
""".strip()

domain_verifier = LlmAgent(
    model="gemini-2.0-flash",
    name="domain_verifier_agent",
    description="Verifies the company's domain name.",
    instruction=DOMAIN_VERIFICATION_PROMPT,
    tools=[built_in_google_search],
    output_key = "domain_verifier_output",
)