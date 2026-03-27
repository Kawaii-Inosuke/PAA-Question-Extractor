import pandas as pd
import asyncio
import os
import logging
from scraper import scrape_multiple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("batch_extract")

async def main():
    csv_path = "[server] - PAA Keyword - question - keyword and region.csv"
    
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found: {csv_path}")
        return
        
    # Read the CSV
    df = pd.read_csv(csv_path)
    
    # Clean keywords and region
    df['keyword'] = df['keyword'].astype(str).str.strip()
    df['region'] = df['region'].astype(str).str.strip()
    
    # Filter out empty or 'nan' keywords
    df = df[df['keyword'].notna()]
    df = df[df['keyword'].str.lower() != 'nan']
    df = df[df['keyword'].str.strip() != '']
    
    keywords = df['keyword'].tolist()
    regions_map = {row['keyword']: row['region'] for _, row in df.iterrows()}
    
    if not keywords:
        logger.info("No keywords found in CSV.")
        return

    logger.info(f"Total keywords to process: {len(keywords)}")
    logger.info(f"Target: 8 questions per keyword.")
    logger.info("Tracking: Session-only (no local Excel files).")
    
    # Process all keywords in a single browser session
    # We use the region of the first keyword for the batch session initialization
    first_region = regions_map.get(keywords[0], "us")
    
    all_flattened_data = []
    output_file = "van.xlsx"

    def save_callback(res):
        keyword = res.get('keyword', 'unknown')
        region = res.get('region', 'us')
        questions = res.get('questions', [])
        
        for q in questions:
            all_flattened_data.append({
                'keyword': keyword,
                'region': region,
                'question': q
            })
        
        if all_flattened_data:
            df = pd.DataFrame(all_flattened_data)
            df.to_excel(output_file, index=False)
            logger.info(f"Updated {output_file} with results for '{keyword}'")

    try:
        from scraper import scrape_multiple_with_callback
        results = await scrape_multiple_with_callback(keywords, region=first_region, callback=save_callback)
        
        success_count = sum(1 for r in results if r.get('count', 0) >= 8)
        logger.info(f"\nBatch processing complete!")
        logger.info(f"Successfully reached 8+ questions for {success_count}/{len(keywords)} keywords.")
        
    except Exception as e:
        logger.error(f"Fatal error during batch extraction: {e}")

if __name__ == "__main__":
    asyncio.run(main())
