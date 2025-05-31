from flo_ai.builder.agent_builder import AgentBuilder
from flo_ai.llm.openai_llm import OpenAILLM
from flo_ai.models.base_agent import ReasoningPattern

# Example YAML configuration
yaml_config = """
apiVersion: flo/alpha-v1
kind: FloAgent
name: email-summary-flo
agent:
  name: EmailSummaryAgent
  kind: llm
  role: Email communication expert
  job: >
    You are given an email thread between a customer and a support agent of a bank.
    Your job is to analyze the behavior, sentiment, and communication style from the latest email in the thread.
    Focus the data extraction based on ONLY the latest email, and use the previous emails for context of the conversation and the product.
    First, identify whether the latest email is from the customer or the support agent.
  parser:
    name: EmailSummary
    fields:
      - name: sub_category
        type: literal
        description: >
          Identifies who sent the latest email in the thread.
        values:
          - description: The latest email was sent by the customer to the bank
            value: customer
          - description: The latest email was sent by the bank's support agent to the customer
            value: agent
      - name: call_summary
        type: str
        description: >
          A comprehensive summary of the latest email in the thread, capturing all major points raised.
          Never mention customer's personal identifiable information like full name, account numbers, etc.
      - name: thread_context
        type: str
        description: >
          Brief context of the overall thread based on references in the latest email.
          This should help understand what has transpired before this email.
      - name: call_resolution
        type: literal
        description: >
          Assessment of whether the customer issue appears to be resolved based on the latest email.
        values: 
          - value: resolved
            description: The issue appears to be fully resolved and the customer seems satisfied
          - value: partial
            description: The issue appears to be partially resolved but requires further action or confirmation
          - value: unresolved
            description: The issue remains unresolved and requires further attention
          - value: open
            description: If only customer email is present in the email thread or cannot determine the resolution status
"""


async def main():
    # Initialize LLM
    llm = OpenAILLM(model='gpt-4o-mini', temperature=0)

    # Create agent builder from YAML
    builder = AgentBuilder.from_yaml(yaml_str=yaml_config, llm=llm)

    # Configure additional settings
    builder.with_reasoning(ReasoningPattern.DIRECT)
    builder.with_retries(3)

    # Build the agent
    agent = builder.build()

    # Example email thread
    email_thread = """
    From: customer@example.com
    Subject: Issue with my account
    
    Hi,
    I'm having trouble accessing my account. The login page keeps showing an error.
    Can you please help me resolve this?
    
    Best regards,
    John
    
    ---
    
    From: support@bank.com
    Subject: Re: Issue with my account
    
    Dear John,
    
    I understand you're having trouble accessing your account. I've checked your account status and everything seems to be in order.
    Let's try resetting your password. Please follow these steps:
    1. Go to our login page
    2. Click on "Forgot Password"
    3. Enter your email address
    4. Follow the instructions in the email you receive
    
    Let me know if you need any further assistance.
    
    Best regards,
    Sarah
    Support Team
    """

    # Process the email thread
    result = await agent.run(email_thread)
    print('Analysis Result:', result)


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
