import sys
from pathlib import Path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.append(str(project_root))

import asyncio
from tavily import AsyncTavilyClient
from config import API_KEY_TAVILY
from models import ResearchResult, InputQuery




tavily_client = AsyncTavilyClient(api_key=API_KEY_TAVILY )

async def research_tool(queries: list) -> list:
    """
    Performs concurrent research using the Tavily API, correctly
    parses results, and extracts content from relevant URLs.
    """
    if not isinstance(queries, list):
        raise ValueError("Error: input value must be a list.")
    
    print("--- Stage 1: Starting concurrent searches... ---")

    search_tasks = [asyncio.create_task(tavily_client.search(**query.model_dump())) for query in queries]
    #print(f"Search tasks: {search_tasks}")
    search_results_list = await asyncio.gather(*search_tasks)

    print("--- Stage 2: Finding relevant URLs... ---")
    #print(f"\nSearch Results list: {search_results_list}")

    url_to_query_map = []
    for i, result_dict in enumerate(search_results_list):
        original_query = queries[i].query
        for url_info in result_dict.get('results',[]):
            if url_info.get('score',0) > 0.6:
                url_to_query_map.append({'url':url_info.get('url'), 'query':original_query})

    if not url_to_query_map:
        print("No highly relevant URLs found to extract.")
        return []
    
    all_urls = list(set(item['url'] for item in url_to_query_map))
    
    #print(f"Relevant urls: {relevant_urls}\n")
    print(f"\n--- Stage 3: Concurrently extracting content from {len(all_urls)} URLs... ---")
    
    extracted_data_list = await tavily_client.extract(urls=all_urls)
    print(type(extracted_data_list))
    print(f"Extracted Data List: {extracted_data_list}")

    for item in extracted_data_list.get('results'):
        print("item", item)
        content_lookup = {item.get('url',''): item.get('raw_content', '')}

    print("--- Stage 4: Aggregating content and structuring the output... ---")

    query_content_aggregator = {q.query: [] for q in queries}
    for mapping in url_to_query_map:
        content = content_lookup.get(mapping['url'])
        if content:
            query_content_aggregator[mapping['query']].append(content)

    final_results = []
    for query, contents in query_content_aggregator.items():
        if contents:
            combined_content = "\n\n--- CONTENT ---\n\n".join(contents)
            final_results.append(ResearchResult(query=query, raw_content=combined_content))
    #print([result.model_dump() for result in final_results] )
    return [result.model_dump() for result in final_results]



async def main():

    queries = [
        InputQuery(query="Who won 2022 World Cup?", search_depth='advanced'),
        InputQuery(query="Who was the best player at the Fifa World Cup 2022?",search_depth='advanced')
    ]

    results = await research_tool(queries)
    print('results', results)
    print("\n\n--- FINAL EXTRACTED CONTENT ---")
    
    if results:
        for result in results:
            print(f"\n--- Query: {result.get('query')} ---")
            print(result.get('raw_content'))
    else:
        print("No content was extracted.")

if __name__ == "__main__":
    asyncio.run(main())


