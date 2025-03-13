import asyncio
import pandas as pd
from autogen_agentchat.agents import FileSurfer
from autogen_agentchat.teams import Orchestrator
from autogen_ext.models.openai import OpenAIChatCompletionClient

async def main():
    # Initialize the model client
    model_client = OpenAIChatCompletionClient(model="gpt-4o", api_key="your_openai_api_key")

    # Define the FileSurfer agent
    file_surfer_agent = FileSurfer(
        name="FileReader",
        model_client=model_client,
        system_message="Read and process CSV files."
    )

    # Define the Orchestrator
    orchestrator = Orchestrator(
        agents=[file_surfer_agent],
        model_client=model_client
    )

    # Task: Read the CSV file and match values
    file_path = "path/to/your/file.csv"  # Replace with your file path
    search_id = "desired_id_value"  # Replace with your desired ID value
    task = (
        f"Read the CSV file at {file_path}. It has two columns: 'id' and 'value'. "
        f"Return all 'value' entries where 'id' matches '{search_id}'."
    )

    # Execute the task through the orchestrator
    result = await orchestrator.run(task)

    # Process and display the result (assuming it returns a dictionary)
    matching_values = result.get("matching_values", [])
    print(f"Matching values for ID '{search_id}': {matching_values}")

# Run the async function
asyncio.run(main())
