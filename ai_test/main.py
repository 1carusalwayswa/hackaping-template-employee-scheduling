from opperai import Opper, trace

from pydantic import BaseModel, Field
from typing import Any, List, Dict

import os
os.environ["OPPER_API_KEY"] = "op-2JGFB9FCGW00O3PM5X0P"


class OpperResponse(BaseModel):
    thoughts: str = Field(description="The AI's thought process while analyzing the request")
    original_query: str = Field(description="The original query text that was analyzed")
    #response: str = Field(description="The response to the question")
    category: str = Field(description="The assigned category", enum=["Change schedule", "Ask question", "Other"])

    #changes: list[ScheduleChange] = Field(description="The suggested changes to the schedule")
    #reason: str | None = Field(description="The extracted reason for the change")
    #recommendation: str = Field(
    #    description="Whether the change should be approved, denied, or needs discussion",
    #    enum=["approve", "deny", "discuss"]
    #)
    #reasoning: str = Field(description="Detailed explanation for the recommendation")


@trace
def askAI(
    opper: Opper,
    request_text: str,
    #employees: List[Dict],
    #current_schedule: List[Dict],
    #rules: Dict
) -> OpperResponse:
    """Process a natural language schedule change request."""
    
    analysis_result, _ = opper.call(
        name="categorize_request",
        instructions="""
        Categorize the given user request into an appropriate category
        """,
        input={
            "request": request_text,
            #"categories": ["Change schedule", "Ask question", "Other"],
            #"current_schedule": current_schedule,
            #"rules": rules
        },
        output_type=OpperResponse
    )

    # Make sure the original query is included in the analysis
    analysis_result.original_query = request_text
    #logger.info(f"Schedule change request analysis: {analysis_result.dict()}")

    print(analysis_result)

    return analysis_result

o = Opper(api_key="op-2JGFB9FCGW00O3PM5X0P")

askAI(o, "What color is an orange?")
askAI(o, "Hello")
askAI(o, "efian<ofiha<fiopa")
askAI(o, "I want to go on a vacation next week, could I change my schedule?")