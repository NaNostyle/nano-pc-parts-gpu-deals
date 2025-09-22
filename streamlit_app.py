#!/usr/bin/env python3
"""
Streamlit Frontend for NaNo PC Parts - GPU Deal Finder
A beautiful web interface for finding and analyzing GPU deals
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import time
from datetime import datetime
from typing import List, Dict, Any
import requests

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import our GPU scraper
from nano_pc_parts import GPUScraper, OPENROUTER_API_KEY

# Page configuration
st.set_page_config(
    page_title="🎮 NaNo PC Parts - GPU Deal Finder",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    
    .deal-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        color: white;
    }
    
    .rating-excellent { color: #00ff00; font-weight: bold; }
    .rating-good { color: #ffff00; font-weight: bold; }
    .rating-average { color: #ff8800; font-weight: bold; }
    .rating-poor { color: #ff0000; font-weight: bold; }
    
    .metric-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        border-left: 5px solid #667eea;
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0.5rem 2rem;
        font-weight: bold;
    }
    
    .stButton > button:hover {
        background: linear-gradient(90deg, #764ba2 0%, #667eea 100%);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

def load_existing_data() -> List[Dict]:
    """Load existing GPU deals data from JSON file"""
    try:
        if os.path.exists("gpu_deals.json"):
            with open("gpu_deals.json", 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error loading existing data: {e}")
    return []

def save_data(data: List[Dict]):
    """Save data to JSON file"""
    try:
        with open("gpu_deals.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Error saving data: {e}")

def get_rating_color(rating: int) -> str:
    """Get color class for rating"""
    if rating >= 8:
        return "rating-excellent"
    elif rating >= 6:
        return "rating-good"
    elif rating >= 4:
        return "rating-average"
    else:
        return "rating-poor"

def get_rating_emoji(rating: int) -> str:
    """Get emoji for rating"""
    if rating >= 9:
        return "🔥"
    elif rating >= 7:
        return "⭐"
    elif rating >= 5:
        return "👍"
    else:
        return "👎"

def create_deal_card(deal: Dict) -> str:
    """Create HTML card for a deal"""
    rating = deal.get('rating', 5)
    rating_color = get_rating_color(rating)
    rating_emoji = get_rating_emoji(rating)
    
    savings = ""
    if deal.get('current_price') and deal.get('listing_price'):
        try:
            current = float(deal['current_price'])
            listing = float(deal['listing_price'])
            if current > 0:
                savings_percent = ((current - listing) / current) * 100
                savings = f"💰 {savings_percent:.1f}% savings"
        except:
            pass
    
    return f"""
    <div class="deal-card">
        <h3>{deal.get('title', 'Unknown GPU')[:60]}...</h3>
        <p><strong>Price:</strong> €{deal.get('listing_price', 'N/A')} | <strong>Market:</strong> €{deal.get('current_price', 'N/A')}</p>
        <p><strong>Rating:</strong> <span class="{rating_color}">{rating_emoji} {rating}/10</span> | <strong>Source:</strong> {deal.get('source', 'Unknown').title()}</p>
        <p><strong>Keywords:</strong> {', '.join(deal.get('ai_keywords', []))}</p>
        {f'<p><strong>{savings}</strong></p>' if savings else ''}
        <p><a href="{deal.get('url', '#')}" target="_blank">🔗 View Deal</a></p>
    </div>
    """

def main():
    # Header
    st.markdown('<h1 class="main-header">🎮 NaNo PC Parts - GPU Deal Finder</h1>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("⚙️ Configuration")
    
    # API Key check
    api_key = OPENROUTER_API_KEY
    if not api_key:
        st.sidebar.error("❌ OPENROUTER_API_KEY not set")
        st.sidebar.info("Please set your OpenRouter API key in environment variables or .env file")
        st.stop()
    else:
        st.sidebar.success("✅ OpenRouter API key configured")
    
    # Load existing data
    existing_data = load_existing_data()
    
    # Sidebar options
    st.sidebar.header("📊 Data Options")
    
    if st.sidebar.button("🔄 Refresh Data", type="primary"):
        with st.spinner("🔄 Fetching new GPU deals..."):
            try:
                scraper = GPUScraper(api_key)
                new_data = scraper.process_listings()
                if new_data:
                    save_data(new_data)
                    st.success("✅ New data fetched successfully!")
                    st.rerun()
                else:
                    st.error("❌ No new data found")
            except Exception as e:
                st.error(f"❌ Error fetching data: {e}")
    
    # Filter options
    st.sidebar.header("🔍 Filters")
    
    min_rating = st.sidebar.slider("Minimum Rating", 1, 10, 5)
    max_price = st.sidebar.number_input("Max Price (€)", 0, 2000, 1000)
    source_filter = st.sidebar.multiselect("Source", ["vinted", "leboncoin"], default=["vinted", "leboncoin"])
    
    # Filter data
    filtered_data = []
    for deal in existing_data:
        try:
            # Get rating
            rating = deal.get('rating', 0)
            
            # Get and parse listing price
            listing_price_str = str(deal.get('listing_price', '0'))
            listing_price_clean = listing_price_str.replace('€', '').replace(',', '').strip()
            
            # Try to convert to float
            try:
                listing_price = float(listing_price_clean)
            except (ValueError, TypeError):
                listing_price = 0
            
            # Get source
            source = deal.get('source', '')
            
            # Apply filters
            if (rating >= min_rating and 
                listing_price <= max_price and
                source in source_filter):
                filtered_data.append(deal)
                
        except Exception as e:
            # If there's any error with this deal, skip it
            continue
    
    # Debug information
    with st.expander("🔍 Debug Information"):
        st.write(f"**Total deals in file:** {len(existing_data)}")
        st.write(f"**Filtered deals:** {len(filtered_data)}")
        st.write(f"**Current filters:** Min Rating: {min_rating}, Max Price: €{max_price}, Sources: {source_filter}")
        
        if existing_data:
            st.write("**Sample deal structure:**")
            st.json(existing_data[0])
        
        # Show source breakdown
        source_breakdown = {}
        for deal in existing_data:
            source = deal.get('source', 'unknown')
            source_breakdown[source] = source_breakdown.get(source, 0) + 1
        st.write("**Source breakdown:**", source_breakdown)
        
        # Show rating breakdown
        rating_breakdown = {}
        for deal in existing_data:
            rating = deal.get('rating', 0)
            rating_breakdown[rating] = rating_breakdown.get(rating, 0) + 1
        st.write("**Rating breakdown:**", rating_breakdown)
        
        # Show price range
        prices = []
        for deal in existing_data:
            try:
                price_str = str(deal.get('listing_price', '0'))
                price_clean = price_str.replace('€', '').replace(',', '').strip()
                price = float(price_clean)
                prices.append(price)
            except:
                continue
        
        if prices:
            st.write(f"**Price range:** €{min(prices):.2f} - €{max(prices):.2f}")
            st.write(f"**Average price:** €{sum(prices)/len(prices):.2f}")
        
        # Show why deals are being filtered out
        if len(filtered_data) == 0 and len(existing_data) > 0:
            st.write("**Why no deals match filters:**")
            sample_deal = existing_data[0]
            sample_rating = sample_deal.get('rating', 0)
            sample_price_str = str(sample_deal.get('listing_price', '0'))
            sample_price_clean = sample_price_str.replace('€', '').replace(',', '').strip()
            try:
                sample_price = float(sample_price_clean)
            except:
                sample_price = 0
            sample_source = sample_deal.get('source', '')
            
            st.write(f"- Sample deal rating: {sample_rating} (filter: >= {min_rating})")
            st.write(f"- Sample deal price: €{sample_price} (filter: <= €{max_price})")
            st.write(f"- Sample deal source: '{sample_source}' (filter: {source_filter})")
    
    # Main content
    if not filtered_data:
        st.warning("📭 No deals found. Click 'Refresh Data' to fetch new deals!")
        return
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Deals", len(filtered_data))
    
    with col2:
        if filtered_data:
            avg_rating = sum(deal.get('rating', 0) for deal in filtered_data) / len(filtered_data)
            st.metric("Average Rating", f"{avg_rating:.1f}/10")
        else:
            st.metric("Average Rating", "0.0/10")
    
    with col3:
        excellent_deals = len([d for d in filtered_data if d.get('rating', 0) >= 8])
        st.metric("Excellent Deals (8+)", excellent_deals)
    
    with col4:
        total_savings = 0
        valid_deals = 0
        for deal in filtered_data:
            try:
                current_price = deal.get('current_price')
                listing_price = deal.get('listing_price')
                
                if current_price and listing_price:
                    # Handle string prices
                    if isinstance(current_price, str):
                        current_price = float(current_price.replace('€', '').replace(',', ''))
                    if isinstance(listing_price, str):
                        listing_price = float(listing_price.replace('€', '').replace(',', ''))
                    
                    if current_price > 0 and listing_price > 0:
                        savings = current_price - listing_price
                        if savings > 0:  # Only count positive savings
                            total_savings += savings
                            valid_deals += 1
            except (ValueError, TypeError):
                continue
        
        st.metric("Total Potential Savings", f"€{total_savings:.0f}")
    
    # Charts
    st.header("📈 Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Rating distribution
        rating_counts = {}
        for deal in filtered_data:
            rating = deal.get('rating', 5)
            rating_counts[rating] = rating_counts.get(rating, 0) + 1
        
        if rating_counts:
            # Sort ratings for better visualization
            sorted_ratings = sorted(rating_counts.keys())
            fig_rating = px.bar(
                x=sorted_ratings,
                y=[rating_counts[r] for r in sorted_ratings],
                title="Deal Rating Distribution",
                labels={'x': 'Rating', 'y': 'Number of Deals'},
                color=sorted_ratings,
                color_continuous_scale='RdYlGn'
            )
            fig_rating.update_layout(showlegend=False)
            st.plotly_chart(fig_rating, use_container_width=True)
        else:
            st.info("No rating data available")
    
    with col2:
        # Source distribution
        source_counts = {}
        for deal in filtered_data:
            source = deal.get('source', 'unknown')
            if source:  # Only count non-empty sources
                source_counts[source] = source_counts.get(source, 0) + 1
        
        if source_counts:
            # Capitalize source names for better display
            display_names = {k: k.title() for k in source_counts.keys()}
            fig_source = px.pie(
                values=list(source_counts.values()),
                names=[display_names[k] for k in source_counts.keys()],
                title="Deals by Source",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig_source, use_container_width=True)
        else:
            st.info("No source data available")
    
    # Price vs Rating scatter plot
    if filtered_data:
        prices = []
        ratings = []
        titles = []
        sources = []
        
        for deal in filtered_data:
            try:
                listing_price = deal.get('listing_price', '0')
                if isinstance(listing_price, str):
                    price = float(listing_price.replace('€', '').replace(',', ''))
                else:
                    price = float(listing_price)
                
                rating = deal.get('rating', 5)
                title = deal.get('title', '')[:30]
                source = deal.get('source', 'unknown')
                
                if price > 0 and rating > 0:
                    prices.append(price)
                    ratings.append(rating)
                    titles.append(title)
                    sources.append(source)
            except (ValueError, TypeError):
                continue
        
        if prices and ratings:
            fig_scatter = px.scatter(
                x=prices,
                y=ratings,
                title="Price vs Rating",
                labels={'x': 'Price (€)', 'y': 'Rating'},
                hover_name=titles,
                color=sources,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_scatter.update_layout(
                xaxis_title="Price (€)",
                yaxis_title="Rating (1-10)"
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("No valid price/rating data for scatter plot")
    
    # Top deals
    st.header("🏆 Top GPU Deals")
    
    # Sort by rating
    top_deals = sorted(filtered_data, key=lambda x: x.get('rating', 0), reverse=True)[:10]
    
    for i, deal in enumerate(top_deals, 1):
        with st.expander(f"#{i} - {deal.get('title', 'Unknown')[:50]}... (Rating: {deal.get('rating', 0)}/10)"):
            st.markdown(create_deal_card(deal), unsafe_allow_html=True)
            
            # Additional details
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if deal.get('image_url'):
                    st.image(deal['image_url'], width=200)
            
            with col2:
                st.write("**Description:**")
                st.write(deal.get('description', 'No description available'))
            
            with col3:
                st.write("**Market Comparison:**")
                if deal.get('matched_market_item'):
                    market_item = deal['matched_market_item']
                    st.write(f"**Market Item:** {market_item.get('title', 'N/A')[:50]}...")
                    st.write(f"**Market Price:** €{market_item.get('price', 'N/A')}")
                    if market_item.get('url'):
                        st.write(f"[View Market Item]({market_item['url']})")
    
    # Data table
    st.header("📋 All Deals Data")
    
    # Create DataFrame
    df_data = []
    for deal in filtered_data:
        # Clean up price data
        listing_price = deal.get('listing_price', '')
        current_price = deal.get('current_price', '')
        
        # Convert prices to proper format
        if isinstance(listing_price, str):
            listing_price = listing_price.replace('€', '').replace(',', '')
        if isinstance(current_price, str):
            current_price = current_price.replace('€', '').replace(',', '')
        
        df_data.append({
            'Title': deal.get('title', ''),
            'Source': deal.get('source', '').title(),
            'Price (€)': listing_price,
            'Market Price (€)': current_price,
            'Rating': deal.get('rating', 0),
            'Keywords': ', '.join(deal.get('ai_keywords', [])),
            'URL': deal.get('url', '')
        })
    
    if df_data:
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"gpu_deals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>🎮 <strong>NaNo PC Parts - GPU Deal Finder</strong></p>
        <p>Powered by AI and real-time market data</p>
        <p>Last updated: {}</p>
    </div>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
