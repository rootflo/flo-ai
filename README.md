# Flo: Composable AI Agents

Flo gives you a composable framework for creating agentic AI architectures. What we intent to do here is to create an easy framework for AI app developers to compose apps using pre-implemented architectural components, at the same time providing the flexibilty to create their own components.

### What is composibility ?

Composility is the ability to use smaller components to build bigger apps. In a composible architecture, you will be given smaller building blocks which you can use to build a bigger applications. It is every similar to how legos work, you are given smaller lego blocks which when put together creates a whole structure.

### What are the building blocks in Flo ?

In flo, we tried to put togther a system where we have small micro components like vector store, or simple LLM prompts, and then higher components/arhictectures made of these mico components like RAGs, Agentic Teams etc.

# Flo vs langraph/langchain

Flo is built with langraph under the stood. So everything that works in langraph still works here, including all tools and architectures. The following makes flo easy to implement:

1. Langraph needs good understanding of underlying graph and states, its more of a raw tool and asks developers to implement the required artitectures. While flo is more usecase friendly and components can be easily used by using the flo classes, which has lot of internal abstraction for ease of use.

2. In every AI component that has gone in production their are lot of nuances that needs to be implemented to get production quality output, flo inherently implements the best architecutures and gives then out of the box, you can enable and disable as you wish. This not only reduces the complexity but also improves the time to iterate solutions

3. Every component in flo is combosable meaning you can easily put them together and flo takes care of routing between the components where as in langraph the developer has to tie these up.

# How to use

Flo supports two ways to set up and run the components, first is through code. This is much more flexible. This can help you write your own tools and add them to the flo.

Second way it to use yaml. You can write an yaml to define your agentic workflow or RAG and it compiles into a application. See examples below

## Building your first agent by structured yaml
To create a small team of researcher + blogger for writing blogs

```python
# This yaml defines a team of 2 agents + 1 supervisor
yaml_data = """
apiVersion: flo/alpha-v1
kind: FloRoutedTeam
name: blogging-team
team:
    name: BloggingTeam
    router:
        name: TeamLead
        kind: supervisor
    agents:
      - name: Researcher
        prompt: Do a research on the internet and find articles of relevent to the topic asked by the user, always try to find the latest information on the same
        tools:
        - name: TavilySearchResults
      - name: Blogger
        prompt: From the documents provider by the researcher write a blog of 300 words with can be readily published, make in engaging and add reference links to original blogs
        tools:
        - name: TavilySearchResults
"""

input_prompt = """
Question: Write me an interesting blog about latest advancements in agentic AI
"""

llm = ChatOpenAI(temperature=0, model_name='gpt-4o')

# Register all the tools at some place and use everywhere in the yaml
session = FloSession(llm).register_tool(
    name="TavilySearchResults", 
    tool=TavilySearchResults()
)

# Build the final flow and run it
flo: Flo = Flo.build_with_yaml(session, yaml=yaml_data)

# call invoke or stream
for s in flo.stream(input_prompt)
```
