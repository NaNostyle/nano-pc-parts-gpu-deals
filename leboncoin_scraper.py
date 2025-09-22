#!/usr/bin/env python3
"""
Leboncoin Graphics Card Scraper
Uses the lbc package to scrape graphic cards from Leboncoin
"""

import lbc
import json
from datetime import datetime

def scrape_leboncoin_graphics_cards():
    """Scrape graphics cards from Leboncoin"""
    print("🚀 Starting Leboncoin graphics card scraping...")
    
    try:
        client = lbc.Client()
        
        # Search for graphics cards in entire France
        # Use multiple major cities to cover all of France
        locations = [
            lbc.City(lat=48.85994982004764, lng=2.33801967847424, radius=50_000, city="Paris"),
            lbc.City(lat=45.764043, lng=4.835659, radius=50_000, city="Lyon"),
            lbc.City(lat=43.296482, lng=5.369780, radius=50_000, city="Marseille"),
            lbc.City(lat=43.604652, lng=1.444209, radius=50_000, city="Toulouse"),
            lbc.City(lat=43.710173, lng=7.261953, radius=50_000, city="Nice"),
            lbc.City(lat=47.218371, lng=-1.553621, radius=50_000, city="Nantes"),
            lbc.City(lat=48.573405, lng=7.752111, radius=50_000, city="Strasbourg"),
            lbc.City(lat=43.611015, lng=3.876734, radius=50_000, city="Montpellier"),
            lbc.City(lat=44.837789, lng=-0.579180, radius=50_000, city="Bordeaux"),
            lbc.City(lat=50.629250, lng=3.057256, radius=50_000, city="Lille")
        ]
        
        # Search multiple pages to get 100 results
        all_ads = []
        page = 1
        max_pages = 3  # 3 pages should give us ~100 results
        
        while len(all_ads) < 100 and page <= max_pages:
            print(f"📄 Scraping page {page}...")
            
            result = client.search(
                text="carte graphique",
                search_in_title_only=True,
                page=page,
                limit=35,
                sort=lbc.Sort.NEWEST,
                ad_type=lbc.AdType.OFFER,
                category=lbc.Category.ELECTRONIQUE_ORDINATEURS
            )
            
            # Filter for graphics cards specifically
            for ad in result.ads:
                if len(all_ads) >= 100:
                    break
                # Check if it's actually a graphics card
                ad_text = f"{ad.subject} {getattr(ad, 'body', '')}".lower()
                if any(keyword in ad_text for keyword in ["carte graphique", "graphics", "gpu", "rtx", "gtx", "radeon", "geforce"]):
                    all_ads.append(ad)
            
            page += 1
        
        result.ads = all_ads[:100]  # Limit to exactly 100
        
        print(f"✅ Found {len(result.ads)} graphics cards:")
        
        # Convert ads to structured data
        structured_ads = []
        for ad in result.ads:
            structured_ad = {
                "id": str(ad.id),
                "title": ad.subject,
                "price": float(ad.price) if ad.price else None,
                "price_currency": "EUR",
                "url": ad.url,
                "description": getattr(ad, 'body', ''),
                "location": {
                    "city": getattr(ad, 'location', 'Unknown') if hasattr(ad, 'location') else 'Unknown',
                    "region": "France",
                    "postal_code": "Unknown"
                },
                "images": getattr(ad, 'images', []) or [],
                "images_count": len(getattr(ad, 'images', []) or []),
                "urgent": getattr(ad, 'urgent', False),
                "professional": getattr(ad, 'professional', False),
                "category": "Electronics/Computers",
                "subcategory": "Graphics Cards",
                "scraped_at": datetime.now().isoformat(),
                "source": "leboncoin",
                "raw_data": {
                    "subject": ad.subject,
                    "body": getattr(ad, 'body', ''),
                    "price": ad.price,
                    "url": ad.url,
                    "id": ad.id
                }
            }
            structured_ads.append(structured_ad)
            print(f"- {ad.subject} - €{ad.price} - {ad.url}")
            
        return structured_ads
        
    except lbc.exceptions.DatadomeError as e:
        print(f"⚠️ Datadome protection blocked the request: {e}")
        print("💡 This is expected - Leboncoin blocks automated requests")
        return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


if __name__ == "__main__":
    print("🔧 Leboncoin Graphics Card Scraper")
    print("=" * 50)
    
    results = scrape_leboncoin_graphics_cards()
    
    if results:
        # Create structured output with metadata
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"leboncoin_graphics_cards_structured_{timestamp}.json"
        
        # Calculate statistics
        prices = [item['price'] for item in results if item['price'] is not None]
        avg_price = sum(prices) / len(prices) if prices else 0
        min_price = min(prices) if prices else 0
        max_price = max(prices) if prices else 0
        
        structured_output = {
            "metadata": {
                "scraped_at": datetime.now().isoformat(),
                "total_items": len(results),
                "source": "leboncoin",
                "search_query": "carte graphique",
                "search_area": "France",
                "price_statistics": {
                    "average_price": round(avg_price, 2),
                    "min_price": min_price,
                    "max_price": max_price,
                    "price_range": f"€{min_price} - €{max_price}"
                },
                "scraper_version": "2.0.0"
            },
            "items": results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(structured_output, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 Structured results saved to: {filename}")
        print(f"📊 Statistics:")
        print(f"   Total items: {len(results)}")
        print(f"   Average price: €{avg_price:.2f}")
        print(f"   Price range: €{min_price} - €{max_price}")
    else:
        print("❌ No results found")