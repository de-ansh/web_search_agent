import click
import asyncio
from rich.console import Console
from rich.table import Table
from ..core.query_validator import QueryValidator
from ..core.similarity_detector import SimilarityDetector
from ..core.web_scraper import WebScraper
from ..ai.summarizer import ContentSummarizer

console = Console()

@click.command()
@click.argument('query', nargs=-1, required=True)
def main(query):
    """
    Web Browser Query Agent CLI
    Enter a query to search the web, summarize, and get results.
    """
    query_str = " ".join(query).strip()
    if not query_str:
        console.print("[bold red]Please enter a query.[/bold red]")
        return

    # Validate query
    validator = QueryValidator()
    validation = validator.validate_query(query_str)
    if not validation.is_valid:
        console.print(f"[bold yellow]This is not a valid query.[/bold yellow] [dim]({validation.reason})[/dim]")
        return
    else:
        console.print(f"[green]Query is valid.[/green] [dim]({validation.category})[/dim]")

    # Check for similar queries
    similarity_detector = SimilarityDetector()
    similarity_result = similarity_detector.find_similar_query(query_str)
    if similarity_result.found_similar and similarity_result.best_match:
        console.print("[cyan]Found similar query in cache. Returning cached results.[/cyan]")
        _print_results(similarity_result.best_match["results"])
        return

    # If not found, perform web search and summarize
    console.print("[blue]No similar query found. Searching the web...[/blue]")
    asyncio.run(_search_and_summarize(query_str, similarity_detector))

def _print_results(results):
    if not results:
        console.print("[red]No results found.[/red]")
        return
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Title", style="cyan", no_wrap=False, width=30)
    table.add_column("URL", style="blue", no_wrap=False, width=25)
    table.add_column("Summary", style="green", no_wrap=False, width=35)
    table.add_column("Method", style="yellow", no_wrap=False, width=8)
    
    for res in results:
        # Get summary method and confidence for display
        method = res.get("summary_method", "unknown")
        confidence = res.get("confidence", 0.0)
        
        # Format method display
        method_display = f"{method}"
        if confidence > 0:
            method_display += f" ({confidence:.1f})"
        
        table.add_row(
            res.get("title", "N/A"),
            res.get("url", "N/A"),
            res.get("summary", "N/A"),
            method_display
        )
    console.print(table)

async def _search_and_summarize(query_str, similarity_detector):
    # Initialize AI summarizer
    summarizer = ContentSummarizer()
    
    # Use Playwright to search and scrape
    async with WebScraper() as scraper:
        search_results = await scraper.search_google(query_str, max_results=5)
        if not search_results:
            console.print("[red]No search results found.[/red]")
            return
        
        # Scrape and summarize each result
        summaries = []
        console.print(f"[blue]Processing {len(search_results)} search results...[/blue]")
        
        for i, result in enumerate(search_results, 1):
            console.print(f"[dim]Processing result {i}/{len(search_results)}: {result['title'][:50]}...[/dim]")
            
            page = await scraper.scrape_page_content(result["url"])
            
            # Use AI-powered summarization
            summary_result = summarizer.summarize_content(
                content=page["content"],
                max_length=100,  # Limit summary length
                query_context=query_str
            )
            
            summaries.append({
                "title": result["title"],
                "url": result["url"],
                "summary": summary_result.summary,
                "summary_method": summary_result.method,
                "confidence": summary_result.confidence
            })
        
        # Print results
        _print_results(summaries)
        # Store in cache
        similarity_detector.store_query_with_results(query_str, summaries)

if __name__ == "__main__":
    main() 