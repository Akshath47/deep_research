# Deep Research Multi-Agent System - Researcher Agent Documentation

## Overview

The Researcher Agent is a sophisticated component of the Deep Research Multi-Agent System that performs parallel research execution using a map-reduce pattern. This agent is designed to efficiently gather and synthesize information from multiple sources simultaneously, significantly reducing research time compared to sequential approaches.

## System Architecture

The Researcher Agent system consists of several interconnected components:

1. **Researcher Hub** - Orchestrates parallel execution of multiple researcher agents
2. **Researcher Agent** - Individual research agent with scraper and summarizer nodes
3. **Scraper Node** - Collects raw data from web sources using Tavily tools
4. **Summarizer Node** - Processes raw data into structured summaries
5. **Web Search Tools** - Interface with Tavily API for data collection

## Researcher Hub (researcher_hub.py)

The Researcher Hub implements a map-reduce pattern for parallel research execution. This component is responsible for:

### Key Functions

1. **map_each_subquery()** - Spawns a researcher agent for each subquery, enabling parallel execution
2. **run_researcher()** - Executes individual researcher agents
3. **run_researcher_merge()** - Combines results from all parallel researcher agents
4. **create_researcher_hub()** - Sets up the researcher hub subgraph with map-reduce pattern

### How It Works

The Researcher Hub receives a list of subqueries from the Decomposer Agent and creates parallel execution paths for each one. This approach allows the system to research multiple aspects of a topic simultaneously, dramatically reducing overall research time.

The map-reduce pattern works as follows:
1. **Map Phase**: Each subquery is sent to a separate researcher agent instance
2. **Execution Phase**: All researcher agents work in parallel to gather and process information
3. **Reduce Phase**: Results from all agents are automatically merged into a unified dataset

## Researcher Agent (agents/researcher.py)

The Researcher Agent is implemented as a CustomSubAgent with a LangGraph subgraph containing two sequential nodes: scraper → summarizer.

### Key Components

1. **create_researcher_subgraph()** - Creates a subgraph with sequential scraper and summarizer nodes
2. **create_researcher_custom_agent()** - Wraps the subgraph in a CustomSubAgent for integration with the deepagents framework

### Workflow

The researcher agent follows a strict sequential workflow:
1. **Scraper Node**: Collects raw data from web sources
2. **Summarizer Node**: Processes raw data into structured summaries

This sequential approach ensures that data collection is completed before analysis begins, maintaining data integrity throughout the process.

## Scraper Node (nodes/scraper_node.py)

The Scraper Node is responsible for collecting raw data from web sources using Tavily tools. It implements a ReAct (Reasoning + Acting) agent pattern that allows the LLM to decide when to use which tool and validate outputs.

### Key Features

1. **Tavily Integration**: Uses tavily_search and tavily_extract tools to gather information
2. **ReAct Pattern**: Allows the LLM to iteratively search and extract until sufficient information is gathered
3. **Structured Output**: Returns data in a structured ScraperOutput format with validation
4. **Data Processing**: Deduplicates, filters, and reranks results based on quality and source type

### Why ReAct Pattern?

The Scraper Node uses a ReAct (Reasoning + Acting) agent pattern rather than hard-coded logic for several important reasons:

1. **Adaptive Problem Solving**: The LLM can dynamically adjust its search strategy based on result quality, rather than following a fixed sequence of steps
2. **Intelligent Retry Logic**: When initial results are poor, the LLM can determine better search terms or approaches without pre-programmed conditions
3. **Context-Aware Decision Making**: The LLM can evaluate result relevance in the context of the specific subquery, something difficult to encode in static rules
4. **Flexibility**: The system can handle unexpected situations or edge cases that weren't anticipated during development

Hard-coded fallback logic would require developers to anticipate every possible failure mode and search scenario, which is impractical. The ReAct pattern allows the system to handle novel situations gracefully through the LLM's reasoning capabilities.

### Process Flow

1. Receives a subquery from the Researcher Hub
2. Uses the SCRAPER_PROMPT to guide the LLM in gathering information
3. Executes tavily_search to find relevant sources
4. Uses tavily_extract to gather full content from selected URLs
5. Validates and structures the results
6. Processes and filters results based on quality metrics
7. Saves raw data to the virtual filesystem for downstream processing

## Summarizer Node (nodes/summarizer_node.py)

The Summarizer Node processes raw search results into structured, actionable summaries. It uses LLMs with structured output capabilities to ensure consistent, high-quality summaries.

### Key Features

1. **Structured Analysis**: Uses SummaryAnalysis schema to ensure consistent output format
2. **Per-Result Processing**: Processes each raw result individually for detailed analysis
3. **Metadata Generation**: Creates index files for easy navigation of results
4. **Citation Support**: Automatically extracts and formats citations for all sources

### Process Flow

1. Reads raw data files generated by the Scraper Node
2. Uses the LLM to analyze each raw result
3. Extracts key findings, arguments, data points, and conclusions
4. Assesses relevance and source reliability
5. Generates a concise summary text
6. Extracts URL and title for citation purposes
7. Saves structured summaries to the virtual filesystem

## Web Search Tools (tools/web_search.py)

The Web Search Tools provide a clean interface to the Tavily API, with schema enforcement and result processing capabilities.

### Key Components

1. **tavily_search()** - Performs web searches with configurable parameters
2. **tavily_extract()** - Extracts full content from specified URLs
3. **SearchResult Schema** - Normalizes search results for consistent processing
4. **Utility Functions** - Provides result filtering, reranking, and formatting capabilities

### Features

1. **Schema Enforcement**: Uses Pydantic models to ensure consistent data structures
2. **Result Normalization**: Converts Tavily responses into standardized SearchResult objects
3. **Source Classification**: Automatically classifies sources as web, news, or academic
4. **Quality Filtering**: Provides functions to filter results by score and source type

## Why This Implementation Is Superior

### Parallel Execution Advantages

1. **Time Efficiency**: Multiple subqueries are researched simultaneously, reducing total research time proportionally to the number of subqueries
2. **Resource Utilization**: Makes full use of available computational resources by running parallel processes
3. **Scalability**: Can handle any number of subqueries without significant changes to the architecture

### Sequential Processing Benefits

1. **Data Integrity**: The scraper → summarizer sequence ensures that analysis only begins after data collection is complete
2. **Error Handling**: Issues in data collection can be isolated and addressed without affecting the entire pipeline
3. **Quality Control**: Each step can implement specific quality checks appropriate to its function

### Map-Reduce Pattern Advantages

1. **Fault Tolerance**: If one researcher agent fails, others continue unaffected
2. **Load Distribution**: Work is evenly distributed across multiple agent instances
3. **Result Consolidation**: Automatic merging of results simplifies downstream processing

### Comparison to Sequential Approaches

Traditional sequential research approaches suffer from several limitations that this implementation overcomes:

1. **Linear Time Growth**: Sequential approaches require time proportional to the number of subqueries multiplied by research time per query. This system reduces that to just the time for the longest individual research task.

2. **Bottleneck Issues**: In sequential systems, a slow or problematic query can delay the entire research process. Parallel execution isolates these issues.

3. **Limited Scalability**: Sequential approaches don't scale well with increasing research complexity. This system can handle dozens of subqueries with minimal performance impact.

4. **Resource Underutilization**: Sequential systems often leave computational resources idle while waiting for single-threaded operations to complete.

5. **Inflexible Error Recovery**: If a sequential process fails midway, recovery often requires restarting the entire process. This system can retry individual failed components.

## Integration with DeepAgents Framework

The Researcher Agent integrates seamlessly with the DeepAgents framework through the CustomSubAgent interface. This allows it to:

1. **Share State**: Utilize the virtual filesystem for data sharing between agents
2. **Maintain Consistency**: Follow the same state management patterns as other agents in the system
3. **Enable Coordination**: Work in conjunction with other agents like the Clarifier, Decomposer, and Synthesizer

## Conclusion

The Researcher Agent system represents a significant advancement in automated research capabilities. By combining parallel execution with sequential processing within each agent, it achieves both speed and quality in information gathering and synthesis. The map-reduce pattern provides robustness and scalability that traditional sequential approaches cannot match, making it an ideal solution for complex research tasks that require comprehensive coverage of multiple subtopics.