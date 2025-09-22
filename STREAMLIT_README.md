# 🌐 Streamlit Web Interface

A beautiful and interactive web interface for the NaNo PC Parts GPU Deal Finder.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Activate virtual environment
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

### 2. Set Up Environment Variables
```bash
# Set your OpenRouter API key
export OPENROUTER_API_KEY='your-api-key-here'

# Or create a .env file
echo "OPENROUTER_API_KEY=your-api-key-here" > .env
```

### 3. Launch the Web App
```bash
# Option 1: Use the launcher script
python run_app.py

# Option 2: Direct Streamlit command
streamlit run streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

## 🎨 Features

### 📊 Dashboard
- **Real-time metrics**: Total deals, average rating, excellent deals count
- **Total savings calculation**: Shows potential savings across all deals
- **Interactive charts**: Rating distribution, source breakdown, price vs rating scatter plot

### 🔍 Filtering & Search
- **Rating filter**: Set minimum rating threshold (1-10)
- **Price filter**: Set maximum price limit
- **Source filter**: Choose between Vinted and LeBonCoin
- **Real-time filtering**: Results update instantly

### 🏆 Deal Display
- **Top deals section**: Best deals sorted by rating
- **Expandable cards**: Click to see full details
- **Image display**: GPU images when available
- **Market comparison**: Side-by-side price comparison
- **Direct links**: Click to view original listings

### 📈 Analytics
- **Rating distribution chart**: See how deals are rated
- **Source pie chart**: Distribution between Vinted and LeBonCoin
- **Price vs Rating scatter plot**: Find the sweet spot for deals
- **Interactive charts**: Hover for details, zoom, pan

### 📋 Data Management
- **Data table**: View all deals in a sortable table
- **CSV export**: Download data for external analysis
- **Auto-refresh**: Fetch new deals with one click
- **Persistent storage**: Data saved between sessions

## 🎯 How to Use

### 1. First Time Setup
1. Set your OpenRouter API key
2. Click "🔄 Refresh Data" to fetch initial deals
3. Wait for the scraping and AI analysis to complete

### 2. Exploring Deals
1. Use the sidebar filters to narrow down results
2. Check the analytics charts for insights
3. Click on deal cards to see full details
4. Use the data table for detailed analysis

### 3. Finding the Best Deals
1. Set minimum rating to 8+ for excellent deals
2. Adjust price filter based on your budget
3. Sort by rating to see the best deals first
4. Check the market comparison for each deal

## 🛠️ Technical Details

### Architecture
- **Frontend**: Streamlit with custom CSS styling
- **Backend**: Python with pandas for data processing
- **Visualizations**: Plotly for interactive charts
- **Data Storage**: JSON files for persistence

### Performance
- **Lazy loading**: Data loaded only when needed
- **Caching**: Results cached to avoid repeated API calls
- **Responsive design**: Works on desktop and mobile
- **Real-time updates**: Instant filtering and sorting

### Security
- **Environment variables**: API keys stored securely
- **Local processing**: All data processed locally
- **No external storage**: Data stays on your machine

## 🎨 Customization

### Styling
The app uses custom CSS for a modern look:
- Gradient backgrounds
- Card-based layout
- Color-coded ratings
- Responsive design

### Configuration
You can modify:
- Chart colors and styles
- Filter ranges
- Display options
- Data refresh intervals

## 🐛 Troubleshooting

### Common Issues

**App won't start:**
```bash
# Check if Streamlit is installed
pip install streamlit

# Check if port 8501 is available
netstat -tulpn | grep 8501
```

**No data showing:**
```bash
# Check API key
echo $OPENROUTER_API_KEY

# Check if gpu_deals.json exists
ls -la gpu_deals.json
```

**Charts not displaying:**
```bash
# Update Plotly
pip install --upgrade plotly
```

### Performance Tips
- Use filters to reduce data load
- Close unused browser tabs
- Restart the app if it becomes slow
- Clear browser cache if needed

## 📱 Mobile Support

The app is fully responsive and works on:
- Desktop computers
- Tablets
- Mobile phones
- Touch devices

## 🔄 Updates

To update the app:
1. Pull latest changes from GitHub
2. Update dependencies: `pip install -r requirements.txt`
3. Restart the Streamlit app

## 🎮 Enjoy Your GPU Hunting!

The Streamlit interface makes it easy to find amazing GPU deals with beautiful visualizations and intuitive controls. Happy deal hunting! 🚀
