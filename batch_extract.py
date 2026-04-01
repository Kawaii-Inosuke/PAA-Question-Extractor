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
    
    # Clean keywords, region, and kw_type
    df['keyword'] = df['keyword'].astype(str).str.strip()
    df['region'] = df['region'].astype(str).str.strip().str.lower()

    # Normalize region values
    df['region'] = df['region'].replace({'india': 'in', 'usa': 'us'})

    # Handle Type of KW column (may be named 'Type of KW' or 'kw_type')
    kw_type_col = None
    for col in df.columns:
        if col.lower().strip() in ('type of kw', 'kw_type', 'type'):
            kw_type_col = col
            break

    if kw_type_col:
        df['kw_type'] = df[kw_type_col].astype(str).str.strip().str.capitalize()
    else:
        df['kw_type'] = 'Primary'

    # Filter out empty or 'nan' keywords
    df = df[df['keyword'].notna()]
    df = df[df['keyword'].str.lower() != 'nan']
    df = df[df['keyword'].str.strip() != '']

    keywords = df['keyword'].tolist()
    regions_map = {row['keyword']: row['region'] for _, row in df.iterrows()}
    targets = {row['keyword']: (8 if row['kw_type'] == 'Primary' else 4) for _, row in df.iterrows()}

    if not keywords:
        logger.info("No keywords found in CSV.")
        return

    logger.info(f"Total keywords to process: {len(keywords)}")
    logger.info(f"Targets per keyword: {targets}")
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
        results = await scrape_multiple_with_callback(keywords, region=first_region, callback=save_callback, targets=targets)

        success_count = sum(1 for r in results if r.get('count', 0) >= targets.get(r.get('keyword', ''), 8))
        logger.info(f"\nBatch processing complete!")
        logger.info(f"Successfully reached target for {success_count}/{len(keywords)} keywords.")
        
    except Exception as e:
        logger.error(f"Fatal error during batch extraction: {e}")

if __name__ == "__main__":
    asyncio.run(main())
