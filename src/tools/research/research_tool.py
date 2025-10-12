import sys
from pathlib import Path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.append(str(project_root))

import asyncio
from tavily import AsyncTavilyClient
from config import API_KEY_TAVILY


tavily_client = AsyncTavilyClient(api_key=API_KEY_TAVILY )

async def research_tool(queries: list) -> list:
    """
    Performs concurrent research using the Tavily API, correctly
    parses results, and extracts content from relevant URLs.
    """
    if not isinstance(queries, list):
        raise ValueError("Error: input value must be a list.")
    
    print("--- Stage 1: Starting concurrent searches... ---")

    search_tasks = [asyncio.create_task(tavily_client.search(**query)) for query in queries]
    #print(f"Search tasks: {search_tasks}")
    search_results_list = await asyncio.gather(*search_tasks)

    print("--- Stage 2: Finding relevant URLs... ---")
    #print(f"\nSearch Results list: {search_results_list}")

    relevant_urls = []
    
    for result_dict in search_results_list:
        for url_info in result_dict.get('results', []):
            if url_info.get('score', 0) > 0.8: 
                relevant_urls.append(url_info.get('url'))
    if not relevant_urls:
        print("No highly relevant URLs found to extract.")
        return []
    
    #print(f"Relevant urls: {relevant_urls}\n")
    print(f"\n--- Stage 3: Concurrently extracting content from {len(relevant_urls)} URLs... ---")
    
    extracted_data = await tavily_client.extract(urls=relevant_urls)
    print(type(extracted_data))


    return extracted_data

async def main():
    queries = [
        {"query": "Who won 2022 World Cup?", "search_depth": "basic"},
        {"query": "Who was the best player at the Fifa World Cup 2022?", "search_depth": "basic"}
    ]
    results = await research_tool(queries)
    print("\n\n--- FINAL EXTRACTED CONTENT ---")
    
    if results.get('results'):
        print(f"Results: {results.get('results')}")
        print(f"Results:{results.get('results')}")
        for i, content in enumerate(results.get('results'), 1):
            #for info in content:
            print(f"content:{type(content)}")
            print(f"\n--- Extracted Content #{i} ---\n")
            print(content.get('raw_content')) 
    else:
        print("No content was extracted.")

if __name__ == "__main__":
    asyncio.run(main())


