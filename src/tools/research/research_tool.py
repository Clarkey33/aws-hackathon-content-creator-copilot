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
    Performs concurrent research using the Tavily API, correctly
    parses results, and extracts content from relevant URLs.
    """

    print(f"--- Received queries for research_tool: {queries} ---")
    print(f"--- Type of queries variable: {type(queries)} ---")


    if not isinstance(queries, list) or not all(isinstance(q, str) for q in queries):
        raise ValueError("Error: input value must be a list of strings.")
    
    input_queries = [InputQuery(query=q) for q in queries]
    
    print("--- Stage 1: Starting concurrent searches... ---")

    search_tasks = [asyncio.create_task(tavily_client.search(**query.model_dump())) for query in input_queries]
    #print(f"\nSearch tasks: {search_tasks}")
    search_results_list = await asyncio.gather(*search_tasks)

    print("--- Stage 2: Finding relevant URLs... ---")
    #print(f"\nSearch Results list: {search_results_list}\n")

    
    url_to_query_map = []
    for i, result_dict in enumerate(search_results_list):
        original_query = input_queries[i].query
        for url_info in result_dict.get('results',[]):
            if url_info.get('score',0) > 0.72:
                url_to_query_map.append(
                    {'url':url_info.get('url'),
                     'query':original_query,
                     'research_summary':result_dict.get('answer','')
                     }
                     )
                
    #print(f"\n URL to QUERY MAP: {url_to_query_map}\n")

    if not url_to_query_map:
        print("No highly relevant URLs found to extract.")
        return []
    
    all_urls = list(set(item['url'] for item in url_to_query_map))
    
    #print(f"Relevant urls: {relevant_urls}\n")
    print(f"\n--- Stage 3: Concurrently extracting content from {len(all_urls)} URLs... ---")
    
    extracted_data_list = await tavily_client.extract(urls=all_urls)

    content_lookup = {
        item.get('url', ''): item.get('raw_content', '')
        for item in extracted_data_list.get('results', [])
        }

    print("--- Stage 4: Aggregating content and structuring the output... ---")

    query_content_aggregator = {q.query: [] for q in input_queries}
    for mapping in url_to_query_map:
        content = content_lookup.get(mapping['url'])
        if content:
            content_package = {
            'research_summary': mapping.get('research_summary', ""),
            'content': content
            }
            query_content_aggregator[mapping['query']].append(content_package)

    final_results = []
    for query, content_packages in query_content_aggregator.items():
        if content_packages:
            combined_content = "\n\n--- NEW SOURCE ---\n\n".join(
            pkg['content'] for pkg in content_packages
            )
            research_summary = content_packages[0].get('research_summary', "No summary available.")
            final_results.append(ResearchResult(query=query, 
                                                raw_content=combined_content, 
                                                research_summary=research_summary
                                                ))
    #print([result.model_dump() for result in final_results] )
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


