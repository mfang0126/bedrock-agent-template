"""Planning tools - LLM-based plan generation using Bedrock.

These tools use Claude 3.5 Sonnet directly for intelligent plan generation.
Following the GitHub agent pattern: simple, synchronous, minimal complexity.
"""

import boto3
import json
import time
from strands import tool
from botocore.exceptions import ClientError

# Bedrock client configuration (Sydney region)
MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"
REGION = "ap-southeast-2"

# Initialize Bedrock client
bedrock_runtime = boto3.client('bedrock-runtime', region_name=REGION)


def call_bedrock_with_retry(system_prompt: str, user_message: str, max_tokens: int = 4000, temperature: float = 0.7, max_retries: int = 3) -> str:
    """Call Bedrock Converse API with exponential backoff retry.

    Args:
        system_prompt: System instructions for the model
        user_message: User's message/request
        max_tokens: Maximum tokens in response
        temperature: Model temperature (0-1)
        max_retries: Maximum retry attempts

    Returns:
        Generated text response

    Raises:
        Exception: If all retries fail
    """
    for attempt in range(max_retries):
        try:
            response = bedrock_runtime.converse(
                modelId=MODEL_ID,
                messages=[{
                    "role": "user",
                    "content": [{"text": user_message}]
                }],
                system=[{"text": system_prompt}],
                inferenceConfig={
                    "maxTokens": max_tokens,
                    "temperature": temperature
                }
            )

            # Success - extract and return text
            return response['output']['message']['content'][0]['text']

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')

            if error_code == 'ThrottlingException':
                if attempt < max_retries - 1:
                    # Exponential backoff: 2^attempt seconds (2s, 4s, 8s)
                    wait_time = 2 ** (attempt + 1)
                    print(f"⏳ Throttled. Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"Bedrock throttling - max retries exceeded. Please wait 30s before trying again.")
            else:
                # Non-throttling error - raise immediately
                raise Exception(f"Bedrock error: {str(e)}")

    raise Exception("Unexpected retry loop exit")


@tool
def generate_implementation_plan(requirement: str) -> str:
    """Generate a detailed implementation plan from a requirement.

    Args:
        requirement: The feature or requirement to plan

    Returns:
        Structured implementation plan in markdown format
    """
    print(f"🎯 Generating implementation plan for: {requirement[:100]}...")

    system_prompt = """You are an expert software architect and project planner.
Generate detailed implementation plans with:
- Clear phases and milestones
- Specific tasks with acceptance criteria
- Dependencies and prerequisites
- Risk identification
- Time estimates

Format output in markdown with clear structure."""

    user_message = f"""Create a detailed implementation plan for:

{requirement}

Provide a structured plan with phases, tasks, dependencies, and acceptance criteria."""

    try:
        # Call Bedrock with retry logic
        plan = call_bedrock_with_retry(
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=4000,
            temperature=0.7
        )

        print(f"✅ Generated plan ({len(plan)} chars)")
        return plan

    except Exception as e:
        error_msg = f"❌ Error generating plan: {str(e)}"
        print(error_msg)
        return error_msg


@tool
def parse_requirements(requirements_text: str) -> str:
    """Parse and structure requirements into clear components.

    Args:
        requirements_text: Raw requirements or user story

    Returns:
        Structured requirements breakdown
    """
    print(f"📋 Parsing requirements ({len(requirements_text)} chars)...")

    system_prompt = """You are a requirements analyst. Parse requirements and extract:
- Core objectives
- Functional requirements
- Non-functional requirements (performance, security, etc.)
- Constraints and assumptions
- Success criteria

Format as clear, structured markdown."""

    user_message = f"""Analyze and structure these requirements:

{requirements_text}

Break down into clear components with objectives, functional/non-functional requirements, constraints, and success criteria."""

    try:
        # Call Bedrock with retry logic
        parsed = call_bedrock_with_retry(
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=3000,
            temperature=0.5
        )

        print(f"✅ Requirements parsed")
        return parsed

    except Exception as e:
        error_msg = f"❌ Error parsing requirements: {str(e)}"
        print(error_msg)
        return error_msg


@tool
def validate_plan(plan_text: str) -> str:
    """Validate an implementation plan for completeness and feasibility.

    Args:
        plan_text: The plan to validate

    Returns:
        Validation report with issues and recommendations
    """
    print(f"✔️ Validating plan ({len(plan_text)} chars)...")

    system_prompt = """You are a technical reviewer validating implementation plans.
Check for:
- Completeness: All necessary phases and tasks covered
- Dependencies: Proper sequencing and prerequisites
- Risks: Identified and mitigation strategies
- Feasibility: Realistic scope and estimates
- Clarity: Clear acceptance criteria

Provide concise validation report with issues and recommendations."""

    user_message = f"""Review and validate this implementation plan:

{plan_text}

Identify gaps, risks, dependency issues, or unclear areas. Provide actionable recommendations."""

    try:
        # Call Bedrock with retry logic
        validation = call_bedrock_with_retry(
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=2000,
            temperature=0.3
        )

        print(f"✅ Plan validated")
        return validation

    except Exception as e:
        error_msg = f"❌ Error validating plan: {str(e)}"
        print(error_msg)
        return error_msg
