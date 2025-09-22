#!/usr/bin/env python3
"""
PC Component Mixer - CLI tool to combine and filter PC component data
Allows mixing different component types, keyword search, and price filtering
"""

import json
import argparse
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
import glob

def load_json_file(filepath: str) -> List[Dict]:
    """Load JSON file and return list of products"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                return [data]
    except Exception as e:
        print(f"❌ Error loading {filepath}: {str(e)}")
        return []

def find_component_files() -> Dict[str, List[str]]:
    """Find all available component JSON files"""
    component_types = {
        'case': ['french_cases_precise_*.json'],
        'cpu_cooler': ['french_cpu_coolers_precise_*.json'],
        'cpu': ['french_cpus_precise_*.json'],
        'hard_drive': ['french_internal_hard_drives_precise_*.json'],
        'memory': ['french_memory_precise_*.json'],
        'motherboard': ['french_motherboards_precise_*.json'],
        'graphic_card': ['french_video_cards_precise_*.json'],
        'power_supply': ['french_power_supplies_precise_*.json']
    }
    
    found_files = {}
    for component_type, patterns in component_types.items():
        files = []
        for pattern in patterns:
            files.extend(glob.glob(pattern))
        if files:
            # Sort by modification time (newest first)
            files.sort(key=os.path.getmtime, reverse=True)
            found_files[component_type] = files
    
    return found_files

def search_products(products: List[Dict], keywords: List[str], min_price: Optional[float] = None, max_price: Optional[float] = None) -> List[Dict]:
    """Search products by keywords and price range"""
    filtered_products = []
    
    for product in products:
        # Check keywords in raw_text (case insensitive) - ALL keywords must be present
        if keywords:
            raw_text = product.get('raw_text', '').lower()
            # Check that ALL keywords are present in the raw_text
            if not all(keyword.lower() in raw_text for keyword in keywords):
                continue
        
        # Check price range
        if min_price is not None or max_price is not None:
            try:
                price_str = product.get('price', '').replace('€', '').replace(',', '.')
                price = float(price_str)
                
                if min_price is not None and price < min_price:
                    continue
                if max_price is not None and price > max_price:
                    continue
            except (ValueError, TypeError):
                continue
        
        filtered_products.append(product)
    
    return filtered_products

def generate_output_filename(components: List[str], keywords: List[str], min_price: Optional[float], max_price: Optional[float]) -> str:
    """Generate output filename based on parameters"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Component part
    component_part = "_".join(components)
    
    # Keywords part
    keyword_part = ""
    if keywords:
        # Clean keywords for filename
        clean_keywords = [re.sub(r'[^\w]', '', kw) for kw in keywords[:3]]  # Max 3 keywords
        keyword_part = "_" + "_".join(clean_keywords)
    
    # Price part
    price_part = ""
    if min_price is not None or max_price is not None:
        if min_price is not None and max_price is not None:
            price_part = f"_€{min_price:.0f}-{max_price:.0f}"
        elif min_price is not None:
            price_part = f"_€{min_price:.0f}+"
        elif max_price is not None:
            price_part = f"_€{max_price:.0f}-"
    
    filename = f"pc_mix_{component_part}{keyword_part}{price_part}_{timestamp}.json"
    return filename

def interactive_mode():
    """Interactive CLI mode"""
    print("🔧 PC Component Mixer - Interactive Mode")
    print("=" * 50)
    
    # Find available files
    available_files = find_component_files()
    if not available_files:
        print("❌ No component JSON files found!")
        return
    
    print("\n📁 Available component types:")
    for i, (component_type, files) in enumerate(available_files.items(), 1):
        print(f"  {i}. {component_type.replace('_', ' ').title()} ({len(files)} files)")
    
    # Component selection
    print("\n🎯 Select components to mix (comma-separated numbers, or 'all'):")
    selection = input("> ").strip()
    
    selected_components = []
    if selection.lower() == 'all':
        selected_components = list(available_files.keys())
    else:
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(',')]
            component_types = list(available_files.keys())
            selected_components = [component_types[i] for i in indices if 0 <= i < len(component_types)]
        except (ValueError, IndexError):
            print("❌ Invalid selection!")
            return
    
    if not selected_components:
        print("❌ No components selected!")
        return
    
    print(f"\n✅ Selected components: {', '.join(selected_components)}")
    
    # Load data
    all_products = []
    for component_type in selected_components:
        files = available_files[component_type]
        if files:
            latest_file = files[0]  # Use newest file
            print(f"📂 Loading {component_type} from {latest_file}...")
            products = load_json_file(latest_file)
            all_products.extend(products)
            print(f"   Loaded {len(products)} {component_type} products")
    
    print(f"\n📊 Total products loaded: {len(all_products)}")
    
    # Keyword search
    print("\n🔍 Enter keywords to search (comma-separated, or press Enter to skip):")
    keywords_input = input("> ").strip()
    keywords = [kw.strip() for kw in keywords_input.split(',') if kw.strip()] if keywords_input else []
    
    # Price filtering
    print("\n💰 Price filtering (press Enter to skip):")
    min_price_input = input("Minimum price (€): ").strip()
    max_price_input = input("Maximum price (€): ").strip()
    
    min_price = float(min_price_input) if min_price_input else None
    max_price = float(max_price_input) if max_price_input else None
    
    # Filter products
    print("\n🔍 Filtering products...")
    filtered_products = search_products(all_products, keywords, min_price, max_price)
    
    print(f"✅ Found {len(filtered_products)} products matching criteria")
    
    if not filtered_products:
        print("❌ No products found matching your criteria!")
        return
    
    # Generate output filename
    output_filename = generate_output_filename(selected_components, keywords, min_price, max_price)
    
    # Save results
    print(f"\n💾 Saving results to {output_filename}...")
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(filtered_products, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved {len(filtered_products)} products to {output_filename}")
    
    # Show sample results
    print(f"\n📋 Sample results (first 5):")
    for i, product in enumerate(filtered_products[:5], 1):
        print(f"  {i}. {product.get('name', 'N/A')} - {product.get('price', 'N/A')}")
    
    if len(filtered_products) > 5:
        print(f"  ... and {len(filtered_products) - 5} more")

def main():
    """Main function with CLI argument parsing"""
    parser = argparse.ArgumentParser(
        description="PC Component Mixer - Combine and filter PC component data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python pc_component_mixer.py

  # Command line mode
  python pc_component_mixer.py --components cpu,memory --keywords "intel,ddr4" --min-price 50 --max-price 200

  # Mix all components with price filter
  python pc_component_mixer.py --components all --max-price 100

  # Search specific components
  python pc_component_mixer.py --components graphic_card,motherboard --keywords "nvidia,asus"
        """
    )
    
    parser.add_argument(
        '--components', '-c',
        help='Components to mix (comma-separated): case, cpu_cooler, cpu, hard_drive, memory, motherboard, graphic_card, power_supply, or "all"',
        type=str
    )
    
    parser.add_argument(
        '--keywords', '-k',
        help='Keywords to search in raw_text (comma-separated)',
        type=str
    )
    
    parser.add_argument(
        '--min-price', '-min',
        help='Minimum price in euros',
        type=float
    )
    
    parser.add_argument(
        '--max-price', '-max',
        help='Maximum price in euros',
        type=float
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output filename (auto-generated if not specified)',
        type=str
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Run in interactive mode (ignores other arguments)'
    )
    
    args = parser.parse_args()
    
    # If no arguments or interactive flag, run interactive mode
    if args.interactive or not any([args.components, args.keywords, args.min_price, args.max_price]):
        interactive_mode()
        return
    
    # Command line mode
    print("🔧 PC Component Mixer - Command Line Mode")
    print("=" * 50)
    
    # Find available files
    available_files = find_component_files()
    if not available_files:
        print("❌ No component JSON files found!")
        return
    
    # Parse components
    if args.components.lower() == 'all':
        selected_components = list(available_files.keys())
    else:
        selected_components = [comp.strip() for comp in args.components.split(',')]
        # Validate components
        invalid_components = [comp for comp in selected_components if comp not in available_files]
        if invalid_components:
            print(f"❌ Invalid components: {', '.join(invalid_components)}")
            print(f"Available components: {', '.join(available_files.keys())}")
            return
    
    print(f"✅ Selected components: {', '.join(selected_components)}")
    
    # Load data
    all_products = []
    for component_type in selected_components:
        files = available_files[component_type]
        if files:
            latest_file = files[0]  # Use newest file
            print(f"📂 Loading {component_type} from {latest_file}...")
            products = load_json_file(latest_file)
            all_products.extend(products)
            print(f"   Loaded {len(products)} {component_type} products")
    
    print(f"\n📊 Total products loaded: {len(all_products)}")
    
    # Parse keywords
    keywords = [kw.strip() for kw in args.keywords.split(',')] if args.keywords else []
    if keywords:
        print(f"🔍 Keywords: {', '.join(keywords)}")
    
    # Parse price range
    if args.min_price is not None or args.max_price is not None:
        price_range = []
        if args.min_price is not None:
            price_range.append(f"min: €{args.min_price}")
        if args.max_price is not None:
            price_range.append(f"max: €{args.max_price}")
        print(f"💰 Price range: {', '.join(price_range)}")
    
    # Filter products
    print("\n🔍 Filtering products...")
    filtered_products = search_products(all_products, keywords, args.min_price, args.max_price)
    
    print(f"✅ Found {len(filtered_products)} products matching criteria")
    
    if not filtered_products:
        print("❌ No products found matching your criteria!")
        return
    
    # Generate output filename
    if args.output:
        output_filename = args.output
    else:
        output_filename = generate_output_filename(selected_components, keywords, args.min_price, args.max_price)
    
    # Save results
    print(f"\n💾 Saving results to {output_filename}...")
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(filtered_products, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved {len(filtered_products)} products to {output_filename}")
    
    # Show sample results
    print(f"\n📋 Sample results (first 5):")
    for i, product in enumerate(filtered_products[:5], 1):
        print(f"  {i}. {product.get('name', 'N/A')} - {product.get('price', 'N/A')}")
    
    if len(filtered_products) > 5:
        print(f"  ... and {len(filtered_products) - 5} more")

if __name__ == "__main__":
    main()
