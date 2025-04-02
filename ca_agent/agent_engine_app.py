import collections
import logging
import os
import random
from typing import Any, Dict, List, Optional
from fastapi import HTTPException

from dotenv import load_dotenv
load_dotenv() 


from google.genai import types
import pydantic

class SparkAssistantArtifactVersion(pydantic.BaseModel):
  """Artifact version."""

  model_config = pydantic.ConfigDict(extra="ignore")

  version: int
  # The artifact version

  data: types.Part
  # The data of the artifact.

class SparkAssistantArtifact(pydantic.BaseModel):
  """Artifact."""

  model_config = pydantic.ConfigDict(extra="ignore")

  file_name: str
  # The file name of the artifact.

  versions: List[SparkAssistantArtifactVersion]
  # The data versions of the artifact, it may not be sorted by version.


class SparkAuthorization(pydantic.BaseModel):
  """Authorization."""

  model_config = pydantic.ConfigDict(
      extra="ignore", alias_generator=pydantic.alias_generators.to_camel
  )

  access_token: str
  # The access token of the user.

from agents.events import Event

class SparkAssistantRunRequest(pydantic.BaseModel):
  """Request object for `agent_run_with_events` method."""

  model_config = pydantic.ConfigDict(extra="ignore")
  
  message: types.Content
  # The new message to be processed by the agent.

  events: Optional[List[Event]] = None
  # List of preceding events happened in the same session.

  artifacts: Optional[List[SparkAssistantArtifact]] = None
  # List of artifacts belonging to the session.

  authorizations: dict[str, SparkAuthorization] = {}
  # The authorizations of the user, keyed by authorization ID.


class SparkAssistantRunResponse(pydantic.BaseModel):
  """Response object for `agent_run_with_events` method.

  It contains the generated events together with the belonging artifacts.
  """

  model_config = pydantic.ConfigDict(extra="ignore")

  events: List[Event]
  # List of generated events.

  artifacts: List[SparkAssistantArtifact]
  # List of artifacts belonging to the session.



class App:
  def __init__(self):
    # load environment variables to local
    self.GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
    self.GOOGLE_GENAI_USE_VERTEXAI=os.environ["GOOGLE_GENAI_USE_VERTEXAI"]
    self.GOOGLE_CLOUD_PROJECT=os.environ["GOOGLE_CLOUD_PROJECT"]
    self.GOOGLE_CLOUD_LOCATION=os.environ["GOOGLE_CLOUD_LOCATION"]
    self.SEC_API_KEY=os.environ["SEC_API_KEY"]
    self.ZOOMINFO_USERNAME=os.environ["ZOOMINFO_USERNAME"]
    self.ZOOMINFO_PASSWORD=os.environ["ZOOMINFO_PASSWORD"]
    self.DB_USER=os.environ["DB_USER"]
    self.DB_PASS=os.environ["DB_PASS"]
    self.DB_NAME=os.environ["DB_NAME"]
    #self.DB_HOST=os.environ["DB_HOST"]
    self.DB_CONNECTION_NAME=os.environ["DB_CONNECTION_NAME"]
    #self.SEC_10K_API_URL=os.environ["SEC_10K_API_URL"]
    

    
    

  def set_up(self) -> None:
    # load environment variables to remote from local
    os.environ["GOOGLE_API_KEY"]=self.GOOGLE_API_KEY
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"]=self.GOOGLE_GENAI_USE_VERTEXAI
    os.environ["GOOGLE_CLOUD_PROJECT"]=self.GOOGLE_CLOUD_PROJECT
    os.environ["GOOGLE_CLOUD_LOCATION"]=self.GOOGLE_CLOUD_LOCATION
    os.environ["SEC_API_KEY"]=self.SEC_API_KEY
    os.environ["ZOOMINFO_USERNAME"]=self.ZOOMINFO_USERNAME
    os.environ["ZOOMINFO_PASSWORD"]=self.ZOOMINFO_PASSWORD
    os.environ["DB_USER"]=self.DB_USER
    os.environ["DB_PASS"]=self.DB_PASS
    os.environ["DB_NAME"]=self.DB_NAME
    os.environ["DB_CONNECTION_NAME"]=self.DB_CONNECTION_NAME
    #os.environ["DB_HOST"]=self.DB_HOST
    #os.environ["SEC_10K_API_URL"]=self.SEC_10K_API_URL
    
    

    from agent import corporate_analyst_agent
    from agents.artifacts import InMemoryArtifactService
    from agents.sessions import InMemorySessionService
    from agents import Runner
     
    self.agent = corporate_analyst_agent
    self.artifact_service = InMemoryArtifactService()
    self.session_service = InMemorySessionService()
    self.app_name = "Corporate Analyst Agent"
    self.user_id = "user"
    self.runner = Runner(
        app_name=self.app_name,
        agent=self.agent,
        artifact_service=self.artifact_service,
        session_service=self.session_service,
    )

  from agents.sessions import Session
  def get_session(self, session_id: str) -> Session:
    session = self.session_service.get_session(self.app_name, self.user_id, session_id)
    if not session:
      raise HTTPException(status_code=404, detail="Session not found")
    return session

  def list_sessions(self) -> list[str]:
    return self.session_service.list_sessions(self.app_name, self.user_id)

  def create_session(
      self, session_id: str, context: Optional[dict[str, Any]] = None
  ) -> Session:
    return self.session_service.create_session(
        self.app_name, self.user_id, context, session_id=session_id
    )

  def delete_session(self, session_id: str):
    self.session_service.delete_session(self.app_name, self.user_id, session_id)

  from agents.events import Event
  def agent_run(self, session_id: str, message: str) -> list[Event]:
    from google.genai import types
    session = self.get_session(session_id)
    if not session:
      raise HTTPException(status_code=404, detail="Session not found")

    return list(
        self.runner.run(
            session=session,
            new_message=types.Content.model_validate_json(message),
        )
    )
  

  from agents.sessions import Session
  
  def _init_session(self, request: SparkAssistantRunRequest) -> Session:
    """Initializes the session, and returns the session id."""
    session_id = f"temp_session_{random.randbytes(8).hex()}"
    logging.debug("Creating temporary session %s", session_id)
    session = self.session_service.create_session(
        self.app_name, self.user_id, state=None, session_id=session_id
    )
    if not session:
      raise HTTPException(status_code=404, detail="Create session failed.")

    if request.events:
      for event in request.events:
        self.session_service.append_event(session, event)

    if request.artifacts:
      for artifact in request.artifacts:
        for version_data in sorted(artifact.versions, key=lambda x: x.version):
          saved_version = self.artifact_service.save_artifact(
              app_name=self.app_name,
              user_id=self.user_id,
              session_id=session_id,
              filename=artifact.file_name,
              artifact=version_data.data,
          )
          if saved_version != version_data.version:
            logging.debug(
                "Artifact '%s' saved at version %s instead of %s",
                artifact.file_name,
                saved_version,
                version_data.version,
            )

    # Add access tokens to the session state.
    for auth_id, auth in request.authorizations.items():
      session.state[f"temp:{auth_id}"] = auth.access_token

    logging.debug("Session initialized.")
    return session

  def _convert_response_events(
      self, session_id: str, events: list[Event]
  ) -> SparkAssistantRunResponse:
    """Converts the framework events to SparkAssistantRunResponse object."""
    result = SparkAssistantRunResponse(events=events, artifacts=[])

    # Save the generated artifacts into the result object.
    artifact_versions = collections.defaultdict(list)
    for event in events:
      if event.actions and event.actions.artifact_delta:
        for key, version in event.actions.artifact_delta.items():
          artifact_versions[key].append(version)

    for key, versions in artifact_versions.items():
      result.artifacts.append(
          SparkAssistantArtifact(
              file_name=key,
              versions=[
                  SparkAssistantArtifactVersion(
                      version=version,
                      data=self.artifact_service.load_artifact(
                          self.app_name,
                          self.user_id,
                          session_id=session_id,
                          filename=key,
                          version=version,
                      ),
                  )
                  for version in versions
              ],
          )
      )

    return result

  def agent_run_with_events(
      self, request_json: str
  ) -> SparkAssistantRunResponse:
    """Runs the agent with a list of events and returns the generated events and artifacts."""
    request = SparkAssistantRunRequest.model_validate_json(request_json)
    # Prepare the in-memory session.
    session = self._init_session(request)
    if not session:
      raise HTTPException(
          status_code=404, detail="Session initialization failed."
      )

    # Run the agent.
    events = list(
        self.runner.run(
            user_id=session.user_id,
            session_id=session.id,
            new_message=request.message,
        )
    )

    # Convert the events to SparkAssistantRunResponse object.
    result = self._convert_response_events(session.id, events)

    # Clean up the in-memory session.
    logging.debug("Deleting temporary session %s", session.id)
    self.session_service.delete_session(self.app_name, self.user_id, session.id)

    return result

  from collections.abc import Iterator
  def streaming_agent_run_with_events(
      self, request_json: str
  ) -> Iterator[SparkAssistantRunResponse]:
    """Runs the agent with a list of events and returns the generated events and artifacts."""
    request = SparkAssistantRunRequest.model_validate_json(request_json)
    # Prepare the in-memory session.
    session = self._init_session(request)
    if not session:
      raise HTTPException(
          status_code=404, detail="Session initialization failed."
      )

    # Run the agent.
    for event in self.runner.run(
        session=session,
        new_message=request.message,
    ):
      yield self._convert_response_events(session_id=session.id, events=[event])

    # Clean up the in-memory session.
    logging.debug("Deleting temporary session %s", session.id)
    self.session_service.delete_session(self.app_name, self.user_id, session.id)

  def register_operations(self) -> Dict[str, List[str]]:
    return {
        "": [
            "get_session",
            "list_sessions",
            "create_session",
            "delete_session",
            "agent_run",
            "agent_run_with_events",
        ],
        "stream": ["streaming_agent_run_with_events"],
    }

def deploy_agent_engine_app():
    """Deploy the agent engine app to Vertex AI."""
    
    import vertexai
    from vertexai.preview import reasoning_engines
    GOOGLE_CLOUD_PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
    GOOGLE_CLOUD_LOCATION = os.environ["GOOGLE_CLOUD_LOCATION"]


    staging_bucket = f"gs://{GOOGLE_CLOUD_PROJECT}-agent-engine-deploy"
    sts = True
    try:
      from google.cloud import storage
      storage_client = storage.Client(project=GOOGLE_CLOUD_PROJECT)
      bucket = storage_client.get_bucket(staging_bucket.replace("gs://", ""))
    except Exception as e:
      print(f"Bucket {staging_bucket} does not exist. Creating it now.")
      from google.cloud import storage
      storage_client = storage.Client(project=GOOGLE_CLOUD_PROJECT)
      bucket = storage_client.create_bucket(staging_bucket.replace("gs://", ""), location=GOOGLE_CLOUD_LOCATION)
      print(f"Bucket {bucket.name} created.")
      sts = False
    if sts:
      print(f"Bucket {staging_bucket} already exists.")

    vertexai.init(
      project=GOOGLE_CLOUD_PROJECT,
      location=GOOGLE_CLOUD_LOCATION,
      #api_endpoint=api_endpoint,
      staging_bucket=staging_bucket,
    )

    with open('requirements.txt', 'r') as file:
      reqs = file.read().splitlines()

    agent_config =  {
        "reasoning_engine" : App(),
        "display_name" : "Corporate Analyst",
        "requirements" : reqs+[
            "google_genai_agents-0.0.2.dev20250304+733376416-py3-none-any.whl",
            "google_cloud_aiplatform",
            "google_genai",
            "cloudpickle==3.1.1",
            "pydantic==2.10.6",
            "pytest",
            "overrides",
        ],
        "extra_packages" : [
            "google_genai_agents-0.0.2.dev20250304+733376416-py3-none-any.whl",
            "agent.py",
            "sec10ktool.py",
            "zoominfotool.py"
        ],
    }
  

    existing_agents=reasoning_engines.ReasoningEngine.list(filter='display_name="Corporate Analyst"')

    if existing_agents:
      #update the existing agent
      remote_app = existing_agents[0].update(**agent_config)
    else:
      #create a new agent
      remote_app = reasoning_engines.ReasoningEngine.create(**agent_config)
      
    return remote_app


if __name__ == "__main__":
    deploy_agent_engine_app()

