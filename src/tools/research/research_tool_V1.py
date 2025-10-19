import sys
from pathlib import Path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.append(str(project_root))

import asyncio
from tavily import AsyncTavilyClient
from config import API_KEY_TAVILY
from models import ResearchResult, InputQuery 
from strands import tool


tavily_client = AsyncTavilyClient(api_key=API_KEY_TAVILY )

@tool
async def research_tool(queries: list[str]) -> list[dict]:
    """
    Performs concurrent research using Tavily's advanced search to get concise chunks.
    It returns a list of dictionaries, each containing the original query and the
    aggregated chunked content.
    """
    print(f"--- Research Tool (Chunk Mode) started with queries: {queries} ---")

    # We still need to convert the input strings to Pydantic models to include
    # our default parameters like chunks_per_source.
    input_queries = [InputQuery(query=q) for q in queries]
    
    print("--- Stage 1: Starting concurrent searches to get chunks... ---")
    search_tasks = [asyncio.create_task(tavily_client.search(**query.model_dump())) for query in input_queries]
    search_results_list = await asyncio.gather(*search_tasks)

    print("--- Stage 2: Aggregating chunks for each query... ---")
    
    final_results = []
    # We iterate through the original queries and the results in parallel.
    for i, result_dict in enumerate(search_results_list):
        original_query = input_queries[i].query
        research_summary = result_dict.get('answer','')
        
        # We will collect all the chunked content for this single query.
        all_chunks_for_query = []
        
        search_results = result_dict.get('results', [])
        if not search_results:
            continue # Skip if a query returned no results

        for result_item in search_results:
            # The 'content' field now contains our valuable chunks.
            chunked_content = result_item.get('content')
            if chunked_content:
                all_chunks_for_query.append(chunked_content)
        
        if all_chunks_for_query:
            # Join all the collected chunks into a single block of text.
            combined_content = "\n\n--- NEW SOURCE ---\n\n".join(all_chunks_for_query)
            
            # Create our final Pydantic object for this query.
            final_results.append(ResearchResult(
                query=original_query, 
                raw_content=combined_content,
                research_summary=research_summary
            ))

    if not final_results:
        print("No relevant content chunks were found.")
        return []

    # Convert the list of Pydantic objects to a list of dictionaries for the agent.
    return [result.model_dump() for result in final_results]





async def main():

    # queries = [
    #     InputQuery(query="Dwight Yorke's impact on Manchester United during their treble-winning season", search_depth='advanced'),
    #     InputQuery(query="The evolution of Dwight Yorke's playing style throughout his career?",search_depth='advanced')
    # ]

    queries =[
        "Dwight Yorke's impact on Manchester United during their treble-winning season",
        "The evolution of Dwight Yorke's playing style throughout his career?"
    ]

    results = await research_tool(queries)
    #print('results', results)
    print("\n\n--- FINAL EXTRACTED CONTENT ---")
    
    if results:
        for result in results:
            print(f"\n--- Query: {result.get('query')} ---")
            print(f"\n--- Research summary: {result.get('research_summary')}")
            print(f"\nraw research content: {result.get('raw_content')}\n")
    else:
        print("No content was extracted.")

if __name__ == "__main__":
    asyncio.run(main())


