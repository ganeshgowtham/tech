"""
LangGraph demonstration with Gemini integration
This example shows how to create nodes and edges in a graph and use Gemini for processing
"""

from typing import Dict, List, Annotated
from langgraph.graph import Graph, MessageGraph
from google.generativeai import GenerativeModel
import google.generativeai as genai
import os
from pydantic import BaseModel, Field
from metrics import NodeMetrics

# Configure Gemini API
GOOGLE_API_KEY = "YOUR_GOOGLE_API_KEY"  # Replace with your actual API key
genai.configure(api_key=GOOGLE_API_KEY)

# Define node states
class AgentState(BaseModel):
    messages: List[str] = Field(default_factory=list)
    current_step: str = Field(default="start")
    context: Dict = Field(default_factory=dict)

# Initialize Gemini model and metrics
model = GenerativeModel('gemini-pro')
metrics = NodeMetrics()

# Define node functions
async def research_node(state: AgentState) -> AgentState:
    """Node for research and information gathering"""
    with metrics.measure_node("research"):
        prompt = "\n".join(state.messages[-3:]) if state.messages else "Start research"
        response = model.generate_content(prompt)
        state.messages.append(f"Research: {response.text}")
        state.current_step = "analysis"
        return state

async def analysis_node(state: AgentState) -> AgentState:
    """Node for analyzing gathered information"""
    with metrics.measure_node("analysis"):
        context = "\n".join(state.messages)
        prompt = f"Analyze this information and provide insights:\n{context}"
        response = model.generate_content(prompt)
        state.messages.append(f"Analysis: {response.text}")
        state.current_step = "conclusion"
        return state

async def conclusion_node(state: AgentState) -> AgentState:
    """Node for drawing conclusions"""
    with metrics.measure_node("conclusion"):
        context = "\n".join(state.messages)
        prompt = f"Provide a final conclusion based on this analysis:\n{context}"
        response = model.generate_content(prompt)
        state.messages.append(f"Conclusion: {response.text}")
        state.current_step = "end"
        return state

# Create the graph
workflow = Graph()

# Add nodes
workflow.add_node("research", research_node)
workflow.add_node("analysis", analysis_node)
workflow.add_node("conclusion", conclusion_node)

# Define edges
workflow.add_edge("research", "analysis")
workflow.add_edge("analysis", "conclusion")

# Compile the graph
chain = workflow.compile()

async def main():
    # Start timing the workflow
    metrics.start_workflow()
    
    # Initialize state
    initial_state = AgentState(
        messages=["Begin research on AI technologies"],
        current_step="start",
        context={}
    )
    
    # Run the graph
    final_state = await chain.invoke(initial_state)
    
    # End timing and print metrics
    metrics.end_workflow()
    metrics.print_metrics()
    
    # Print results
    print("\nFinal Results:")
    for message in final_state.messages:
        print(f"\n{message}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())