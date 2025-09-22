#!/usr/bin/env python3
"""
NaNo PC Parts - GPU Deal Finder
Fetches GPU listings from Vinted and Leboncoin, analyzes them with AI,
and provides deal ratings based on current market prices.
"""

import json
import time
import requests
import subprocess
import sys
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv is optional, continue without it
    pass

# Get OpenRouter API key from environment variable
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Import the scraping packages
try:
    from pyVinted import Vinted
    from lbc import Client as LBC
except ImportError as e:
    print(f"❌ Error importing packages: {e}")
    print("Please install required packages: pip install pyvinted lbc requests")
    sys.exit(1)


class OpenRouterClient:
    """Client for OpenRouter AI API"""
    
    def __init__(self, api_key: str, model: str = "x-ai/grok-4-fast:free"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/your-repo",  # Optional
            "X-Title": "NaNo PC Parts"  # Optional
        }
    
    def extract_gpu_keywords(self, listings: List[Dict]) -> List[str]:
        """Extract standardized GPU model keywords from listings using OpenRouter AI"""
        # Prepare the text for analysis
        titles_descriptions = []
        for listing in listings[:50]:  # Limit to first 50 for analysis
            title = listing.get('title', '')
            description = listing.get('description', '')
            combined_text = f"{title} {description}".strip()
            if combined_text:
                titles_descriptions.append(combined_text)
        
        if not titles_descriptions:
            return []
        
        # Create prompt for AI - use a simpler, more direct approach
        sample_texts = "\n".join(titles_descriptions[:10])  # Show first 10 as examples
        prompt = f"""Extract GPU model keywords from these listings. Return format: BRAND,MODEL

Examples:
{sample_texts}

Extract only GPU models (RTX, GTX, RX series). Return one per line:
RTX,3070
GTX,1660
RX,6700XT

Return only the keywords:"""
        
        try:
            response = self._make_request(prompt, max_tokens=200)
            if response:
                # Parse the response to extract keywords
                keywords = []
                for line in response.split('\n'):
                    line = line.strip()
                    if line and ',' in line and not line.startswith('#'):
                        # Validate format - handle various formats
                        parts = line.split(',')
                        if len(parts) == 2:
                            brand = parts[0].upper().strip()
                            model = parts[1].upper().strip()
                            
                            # Extract GPU brand and model from the model part
                            import re
                            gpu_match = re.search(r'(RTX|GTX|RX)\s*(\d{3,4})', model)
                            if gpu_match:
                                gpu_brand = gpu_match.group(1)
                                gpu_model = gpu_match.group(2)
                                keywords.append(f"{gpu_brand},{gpu_model}")
                            # Handle direct format like "GTX,970"
                            elif brand in ['RTX', 'GTX', 'RX'] and model.isdigit() and len(model) in [3, 4]:
                                keywords.append(f"{brand},{model}")
                            # Handle empty brand like ",GTX 1050"
                            elif not brand and (model.startswith('RTX') or model.startswith('GTX') or model.startswith('RX')):
                                gpu_match = re.search(r'(RTX|GTX|RX)\s*(\d{3,4})', model)
                                if gpu_match:
                                    gpu_brand = gpu_match.group(1)
                                    gpu_model = gpu_match.group(2)
                                    keywords.append(f"{gpu_brand},{gpu_model}")
                return keywords[:20]  # Limit to 20 keywords
        except Exception as e:
            print(f"❌ Error extracting keywords with AI: {e}")
            # Fallback to simple pattern matching
            return self._extract_keywords_fallback(listings)
        
        return []
    
    def _extract_keywords_fallback(self, listings: List[Dict]) -> List[str]:
        """Fallback keyword extraction using pattern matching"""
        keywords = set()
        
        # Common GPU patterns
        gpu_patterns = [
            r'RTX\s*(\d{4})',
            r'GTX\s*(\d{4})',
            r'RX\s*(\d{4})',
            r'Radeon\s*RX\s*(\d{4})',
            r'GeForce\s*RTX\s*(\d{4})',
            r'GeForce\s*GTX\s*(\d{4})'
        ]
        
        import re
        
        for listing in listings[:50]:  # Limit to first 50 for analysis
            title = listing.get('title', '').upper()
            description = listing.get('description', '').upper()
            combined_text = f"{title} {description}"
            
            for pattern in gpu_patterns:
                matches = re.findall(pattern, combined_text)
                for match in matches:
                    if 'RTX' in pattern:
                        keywords.add(f"RTX,{match}")
                    elif 'GTX' in pattern:
                        keywords.add(f"GTX,{match}")
                    elif 'RX' in pattern:
                        keywords.add(f"RX,{match}")
        
        return list(keywords)[:20]  # Limit to 20 keywords
    
    def generate_deal_rating(self, listing: Dict, current_price: Optional[float]) -> int:
        """Generate a deal rating from 1-10 for a listing using OpenRouter AI"""
        listing_price = listing.get('price', 0)
        title = listing.get('title', '')
        
        # Convert listing_price to float if it's a string
        if isinstance(listing_price, str):
            try:
                listing_price = float(listing_price)
            except (ValueError, TypeError):
                listing_price = 0
        
        if not current_price or not listing_price:
            return 5  # Default average rating
        
        # Calculate price difference percentage
        price_diff = ((listing_price - current_price) / current_price) * 100
        
        prompt = f"""Rate this GPU deal from 1-10:

Title: {title}
Listing Price: €{listing_price}
Market Price: €{current_price}
Price Difference: {price_diff:.1f}%

Rating scale:
- 10: Exceptional deal (30%+ below market)
- 9: Excellent deal (20-30% below market)  
- 8: Very good deal (10-20% below market)
- 7: Good deal (5-10% below market)
- 6: Fair deal (0-5% below market)
- 5: Average market price (0-5% above market)
- 4: Slightly overpriced (5-10% above market)
- 3: Overpriced (10-20% above market)
- 2: Very overpriced (20-30% above market)
- 1: Extremely overpriced (30%+ above market)

Return only the number (1-10):"""
        
        try:
            response = self._make_request(prompt, max_tokens=10)
            if response:
                # Extract number from response
                import re
                numbers = re.findall(r'\b([1-9]|10)\b', response)
                if numbers:
                    rating = int(numbers[0])
                    return max(1, min(10, rating))  # Ensure rating is between 1-10
        except Exception as e:
            print(f"❌ Error generating AI rating: {e}")
        
        # Fallback to simple algorithm
        if price_diff <= -30:
            return 10
        elif price_diff <= -20:
            return 9
        elif price_diff <= -10:
            return 8
        elif price_diff <= -5:
            return 7
        elif price_diff <= 0:
            return 6
        elif price_diff <= 5:
            return 5
        elif price_diff <= 10:
            return 4
        elif price_diff <= 20:
            return 3
        elif price_diff <= 30:
            return 2
        else:
            return 1
    
    def _make_request(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        """Make a request to OpenRouter API using the correct format"""
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": 0.1,
            "reasoning": {
                "effort": "low",
                "exclude": True
            }
        }
        
        try:
            response = requests.post(
                url=f"{self.base_url}/chat/completions",
                headers=self.headers,
                data=json.dumps(payload),
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            if 'choices' in data and len(data['choices']) > 0:
                return data['choices'][0]['message']['content']
        except Exception as e:
            print(f"❌ API request failed: {e}")
        
        return None


class GPUScraper:
    """Main class for scraping GPU listings and analyzing deals"""
    
    def __init__(self, openrouter_api_key: str):
        self.openrouter = OpenRouterClient(openrouter_api_key)
        self.vinted = Vinted()
        self.lbc = LBC()
    
    def fetch_vinted_gpus(self, limit: int = 100) -> List[Dict]:
        """Fetch GPU listings from Vinted"""
        print("🔍 Fetching GPU listings from Vinted...")
        
        try:
            # Search only for "carte graphique"
            search_term = "carte graphique"
            print(f"  Searching for: {search_term}")
            
            # Construct search URL for Vinted
            search_url = f"https://www.vinted.fr/catalog?search_text={search_term}"
            results = self.vinted.items.search(search_url, nbrItems=limit)
            
            all_listings = []
            for item in results:
                listing = {
                    'source': 'vinted',
                    'title': getattr(item, 'title', ''),
                    'description': getattr(item, 'description', ''),
                    'url': getattr(item, 'url', ''),
                    'price': getattr(item, 'price', 0),
                    'image_url': getattr(item, 'photo', ''),
                    'user': getattr(item, 'user', '') if getattr(item, 'user', None) else '',
                    'created_at': getattr(item, 'created_at_ts', ''),
                    'raw_data': item
                }
                all_listings.append(listing)
            
            # Remove duplicates and limit
            unique_listings = self._remove_duplicates(all_listings)
            return unique_listings[:limit]
            
        except Exception as e:
            print(f"❌ Error fetching from Vinted: {e}")
            return []
    
    def fetch_leboncoin_gpus(self, limit: int = 100) -> List[Dict]:
        """Fetch GPU listings from Leboncoin"""
        print("🔍 Fetching GPU listings from Leboncoin...")
        
        try:
            # Import LBC modules
            import lbc
            
            # Search for "carte graphique" using the correct API
            print(f"  Searching for: carte graphique")
            
            result = self.lbc.search(
                text="carte graphique",
                search_in_title_only=True,
                page=1,
                limit=limit,
                sort=lbc.Sort.NEWEST,
                ad_type=lbc.AdType.OFFER,
                category=lbc.Category.ELECTRONIQUE_ORDINATEURS
            )
            
            all_listings = []
            for ad in result.ads:
                # Check if it's actually a graphics card
                ad_text = f"{ad.subject} {getattr(ad, 'body', '')}".lower()
                if any(keyword in ad_text for keyword in ["carte graphique", "graphics", "gpu", "rtx", "gtx", "radeon", "geforce"]):
                    # Handle images safely
                    image_url = ''
                    if hasattr(ad, 'images') and ad.images:
                        if isinstance(ad.images, list) and len(ad.images) > 0:
                            if hasattr(ad.images[0], 'url'):
                                image_url = ad.images[0].url
                            elif isinstance(ad.images[0], dict) and 'url' in ad.images[0]:
                                image_url = ad.images[0]['url']
                    
                    # Handle user safely
                    user_name = ''
                    if hasattr(ad, 'user') and ad.user:
                        if hasattr(ad.user, 'name'):
                            user_name = ad.user.name
                        elif isinstance(ad.user, dict) and 'name' in ad.user:
                            user_name = ad.user['name']
                    
                    listing = {
                        'source': 'leboncoin',
                        'title': ad.subject,
                        'description': getattr(ad, 'body', ''),
                        'url': ad.url,
                        'price': float(ad.price) if ad.price else 0,
                        'image_url': image_url,
                        'user': user_name,
                        'created_at': getattr(ad, 'date', ''),
                        'raw_data': ad
                    }
                    all_listings.append(listing)
            
            # Remove duplicates and limit
            unique_listings = self._remove_duplicates(all_listings)
            return unique_listings[:limit]
            
        except Exception as e:
            print(f"❌ Error fetching from Leboncoin: {e}")
            return []
    
    def _extract_price(self, price_data) -> float:
        """Extract numeric price from various price formats"""
        if isinstance(price_data, (int, float)):
            return float(price_data)
        elif isinstance(price_data, str):
            # Remove currency symbols and extract number
            import re
            numbers = re.findall(r'[\d,]+\.?\d*', price_data.replace(',', '.'))
            if numbers:
                return float(numbers[0])
        elif isinstance(price_data, list) and len(price_data) > 0:
            return self._extract_price(price_data[0])
        
        return 0.0
    
    def _remove_duplicates(self, listings: List[Dict]) -> List[Dict]:
        """Remove duplicate listings based on title similarity"""
        unique_listings = []
        seen_titles = set()
        
        for listing in listings:
            title = listing.get('title', '').lower().strip()
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_listings.append(listing)
        
        return unique_listings
    
    def run_price_comparison_for_listing(self, listing: Dict) -> Optional[Dict]:
        """Run pc_component_mixer.py for a single listing and use AI to find best match"""
        title = listing.get('title', '')
        description = listing.get('description', '')
        
        if not title:
            return None
        
        # Extract potential keywords from the listing title/description
        combined_text = f"{title} {description}".strip()
        
        # Use AI to extract the most relevant GPU model from this specific listing
        gpu_keyword = self._extract_gpu_from_listing(combined_text)
        
        if not gpu_keyword:
            return None
        
        try:
            # Run pc_component_mixer.py for this specific GPU
            cmd = [
                sys.executable, "pc_component_mixer.py",
                "--components", "graphic_card",
                "--keywords", gpu_keyword,
                "--output", f"temp_price_{hash(combined_text)}.json"
            ]
            
            # Set environment variables to handle Unicode properly
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=30,
                encoding='utf-8',
                errors='replace',
                env=env
            )
            
            if result.returncode == 0:
                # Load the results
                try:
                    with open(f"temp_price_{hash(combined_text)}.json", 'r', encoding='utf-8') as f:
                        price_data = json.load(f)
                    
                    if price_data:
                        # Use AI to find the best match for this listing
                        best_match = self._find_best_match_with_ai(listing, price_data)
                        if best_match:
                            return {
                                'gpu_keyword': gpu_keyword,
                                'current_price': self._extract_price(best_match.get('price', 0)),
                                'matched_item': best_match
                            }
                    
                    # Clean up temp file
                    try:
                        os.remove(f"temp_price_{hash(combined_text)}.json")
                    except:
                        pass
                        
                except Exception as e:
                    print(f"  ❌ Error reading price comparison results: {e}")
            else:
                print(f"  ❌ Price comparison failed for {title}: {result.stderr}")
                
        except Exception as e:
            print(f"  ❌ Error running price comparison for {title}: {e}")
        
        return None
    
    def _extract_gpu_from_listing(self, text: str) -> Optional[str]:
        """Use AI to extract the most relevant GPU model from a listing text"""
        prompt = f"""Extract GPU model from this listing text for pc_component_mixer.py search.

PC_COMPONENT_MIXER TOOL INFO:
- Searches pcpartpicker.fr for PC components using keyword matching
- Use specific GPU model format for best results
- Format should be: BRAND,MODEL (e.g., RTX,3070 or GTX,970)

LISTING TEXT: {text}

IMPORTANT: Return ONLY the GPU model in format: BRAND,MODEL
Valid brands: RTX, GTX, RX
Valid models: 3-4 digit numbers (e.g., 3070, 970, 570)

Examples: RTX,3070, GTX,970, RX,570

If no valid GPU model found, return: NONE

Answer:"""
        
        # Retry logic for API calls
        for attempt in range(3):
            try:
                response = self.openrouter._make_request(prompt, max_tokens=500)
                if response:
                    # Parse the response
                    line = response.strip()
                    print(f"    🤖 AI extracted: '{line}'")
                    
                    # Handle "NONE" response
                    if line.upper() == "NONE":
                        print(f"    ❌ No GPU model found")
                        return None
                    
                    if ',' in line:
                        parts = line.split(',')
                        if len(parts) == 2:
                            brand = parts[0].upper().strip()
                            model = parts[1].upper().strip()
                            
                            # Handle special cases like "GeForce2" -> "GTX"
                            if brand.startswith('GEFORCE'):
                                brand = 'GTX'
                            elif brand.startswith('QUADRO'):
                                brand = 'GTX'  # Map Quadro to GTX for compatibility
                            
                            # Validate format
                            if brand in ['RTX', 'GTX', 'RX'] and model.isdigit() and len(model) in [3, 4]:
                                print(f"    ✅ Valid GPU format: {brand},{model}")
                                return f"{brand},{model}"
                            else:
                                print(f"    ❌ Invalid format: {brand},{model}")
                    else:
                        print(f"    ❌ No comma in response: {line}")
                else:
                    print(f"    ❌ No response from AI (attempt {attempt + 1}/3)")
                    if attempt < 2:  # Don't sleep on last attempt
                        import time
                        time.sleep(1)
            except Exception as e:
                print(f"  ❌ Error extracting GPU from listing (attempt {attempt + 1}/3): {e}")
                if attempt < 2:  # Don't sleep on last attempt
                    import time
                    time.sleep(1)
        
        return None
    
    def _find_best_match_with_ai(self, listing: Dict, price_data: List[Dict]) -> Optional[Dict]:
        """Use AI to find the best match for a listing from price comparison results"""
        listing_title = listing.get('title', '')
        listing_description = listing.get('description', '')
        
        # Prepare price data for AI analysis
        price_options = []
        for item in price_data[:10]:  # Limit to first 10 options
            price_options.append({
                'title': item.get('raw_text', ''),
                'price': item.get('price', 0),
                'url': item.get('url', '')
            })
        
        if not price_options:
            return None
        
        prompt = f"""You are matching a GPU listing to market prices from pc_component_mixer.py.

PC_COMPONENT_MIXER TOOL INFO:
- This tool searches pcpartpicker.fr for PC components
- It uses keyword matching to find products containing specific terms
- Results include: name, price (€), url, raw_text (full description), scraped_at, source, page
- The raw_text contains the complete product description from the website

LISTING TO MATCH:
Title: {listing_title}
Description: {listing_description}

MARKET OPTIONS (from pc_component_mixer.py):
"""
        
        for i, option in enumerate(price_options):
            prompt += f"{i+1}. {option['title']} - €{option['price']}\n"
        
        prompt += """
INSTRUCTIONS:
- Match the listing to the most similar GPU model from the market options
- Consider GPU model numbers, memory size, and brand compatibility
- Return only the number (1-10) of the best matching option
- If no good match exists, return the closest option

Answer:"""
        
        try:
            response = self.openrouter._make_request(prompt, max_tokens=10)
            if response:
                # Extract number from response
                import re
                numbers = re.findall(r'\b([1-9]|10)\b', response)
                if numbers:
                    index = int(numbers[0]) - 1
                    if 0 <= index < len(price_options):
                        return price_data[index]
        except Exception as e:
            print(f"❌ Error finding best match with AI: {e}")
        
        # Fallback: return the first option
        return price_data[0] if price_data else None
    
    def process_listings(self) -> List[Dict]:
        """Main processing function"""
        print("🚀 Starting NaNo PC Parts GPU Deal Finder")
        print("=" * 50)
        
        # Step 1: Fetch listings from both sources
        vinted_listings = self.fetch_vinted_gpus(100)
        leboncoin_listings = self.fetch_leboncoin_gpus(100)
        
        print(f"📊 Fetched {len(vinted_listings)} listings from Vinted")
        print(f"📊 Fetched {len(leboncoin_listings)} listings from Leboncoin")
        
        # Step 2: Combine results
        all_listings = vinted_listings + leboncoin_listings
        print(f"📊 Total listings: {len(all_listings)}")
        
        if not all_listings:
            print("❌ No listings found!")
            return []
        
        # Step 3: Process each listing individually with AI and price comparison
        print("\n🤖 Processing each listing with AI and price comparison...")
        final_results = []
        
        # Process 10 from Vinted and 10 from Leboncoin for testing
        vinted_test = [l for l in all_listings if l['source'] == 'vinted'][:10]
        leboncoin_test = [l for l in all_listings if l['source'] == 'leboncoin'][:10]
        test_listings = vinted_test + leboncoin_test
        print(f"  Testing with first {len(test_listings)} listings...")
        
        for i, listing in enumerate(test_listings):
            source = listing.get('source', 'unknown')
            title = listing.get('title', '')[:50]
            print(f"  Processing listing {i+1}/{len(test_listings)} [{source}]: {title}...")
            
            # Run price comparison for this specific listing
            price_result = self.run_price_comparison_for_listing(listing)
            
            if price_result:
                current_price = price_result['current_price']
                gpu_keyword = price_result['gpu_keyword']
                matched_item = price_result['matched_item']
                
                # Generate deal rating using AI
                rating = self.openrouter.generate_deal_rating(listing, current_price)
                
                # Build final result
                result = {
                    'source': listing['source'],
                    'title': listing['title'],
                    'url': listing['url'],
                    'listing_price': str(listing['price']),
                    'current_price': current_price,
                    'ai_keywords': [gpu_keyword],
                    'rating': rating,
                    'image_url': listing.get('image_url', ''),
                    'user': listing.get('user', ''),
                    'created_at': str(listing.get('created_at', '')),
                    'description': listing.get('description', '')[:200] + '...' if len(listing.get('description', '')) > 200 else listing.get('description', ''),
                    'matched_market_item': {
                        'title': matched_item.get('raw_text', ''),
                        'price': matched_item.get('price', 0),
                        'url': matched_item.get('url', '')
                    }
                }
            else:
                # No price comparison available, use default rating
                rating = 5
                result = {
                    'source': listing['source'],
                    'title': listing['title'],
                    'url': listing['url'],
                    'listing_price': str(listing['price']),
                    'current_price': None,
                    'ai_keywords': [],
                    'rating': rating,
                    'image_url': listing.get('image_url', ''),
                    'user': listing.get('user', ''),
                    'created_at': str(listing.get('created_at', '')),
                    'description': listing.get('description', '')[:200] + '...' if len(listing.get('description', '')) > 200 else listing.get('description', ''),
                    'matched_market_item': None
                }
            
            final_results.append(result)
            
            # Add small delay to avoid rate limiting
            time.sleep(0.5)
        
        # Sort by rating (best deals first)
        final_results.sort(key=lambda x: x['rating'], reverse=True)
        
        print(f"✅ Processed {len(final_results)} listings")
        return final_results


def main():
    """Main function"""
    # Load OpenRouter API key from environment variable
    api_key = OPENROUTER_API_KEY
    if not api_key:
        print("❌ Error: OPENROUTER_API_KEY environment variable not set")
        print("Please set it with: export OPENROUTER_API_KEY='your-api-key-here'")
        print("Or create a .env file with: OPENROUTER_API_KEY=your-api-key-here")
        return
    
    model = "x-ai/grok-4-fast:free"  # Default model
    
    # Initialize scraper
    scraper = GPUScraper(api_key)
    
    # Process listings
    results = scraper.process_listings()
    
    if results:
        # Save results
        output_file = "gpu_deals.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to {output_file}")
        print(f"📊 Total deals analyzed: {len(results)}")
        
        # Show top 10 deals
        print("\n🏆 Top 10 GPU Deals:")
        for i, deal in enumerate(results[:10], 1):
            print(f"  {i}. {deal['title'][:60]}...")
            print(f"     Price: €{deal['listing_price']} | Market: €{deal['current_price']} | Rating: {deal['rating']}/10")
            print(f"     Source: {deal['source']} | Keywords: {', '.join(deal['ai_keywords'])}")
            print()
    else:
        print("❌ No results to save")


if __name__ == "__main__":
    main()
