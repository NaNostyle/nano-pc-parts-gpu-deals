# PC Component Mixer

A powerful CLI tool to combine and filter PC component data from your scraped JSON files.

## Features

- **Mix Components**: Combine data from multiple component types (CPU, GPU, Motherboard, etc.)
- **Keyword Search**: Search for specific keywords in product descriptions. ALL specified keywords must be present in the raw_text (case-insensitive).
- **Price Filtering**: Filter by minimum and/or maximum price
- **Interactive Mode**: User-friendly interactive prompts
- **Command Line Mode**: Full CLI with flags for automation
- **Smart Naming**: Auto-generates descriptive filenames based on your search criteria

## Available Components

- `case` - Computer cases
- `cpu_cooler` - CPU coolers
- `cpu` - Processors
- `hard_drive` - Internal hard drives and SSDs
- `memory` - RAM modules
- `motherboard` - Motherboards
- `graphic_card` - Video cards/GPUs
- `power_supply` - Power supplies

## Usage Examples

### Interactive Mode (Recommended for beginners)
```bash
python pc_component_mixer.py --interactive
# or simply
python pc_component_mixer.py
```

### Command Line Examples

#### Mix CPUs and Memory, search for Intel and DDR4, under €200
```bash
python pc_component_mixer.py --components cpu,memory --keywords "intel,ddr4" --max-price 200
```
*Note: This will find products that contain BOTH "intel" AND "ddr4" in their raw_text*

#### Mix all components with price range €100-500
```bash
python pc_component_mixer.py --components all --min-price 100 --max-price 500
```

#### Search for NVIDIA graphics cards and ASUS motherboards
```bash
python pc_component_mixer.py --components graphic_card,motherboard --keywords "nvidia,asus"
```

#### Find budget components under €50
```bash
python pc_component_mixer.py --components all --max-price 50
```

#### Search for RGB components
```bash
python pc_component_mixer.py --components all --keywords "rgb"
```

## Command Line Options

- `--components, -c`: Components to mix (comma-separated or "all")
- `--keywords, -k`: Keywords to search (comma-separated)
- `--min-price, -min`: Minimum price in euros
- `--max-price, -max`: Maximum price in euros
- `--output, -o`: Custom output filename
- `--interactive, -i`: Run in interactive mode

## Output Files

The tool automatically generates descriptive filenames based on your search criteria:

- `pc_mix_cpu_intel_€100-_20250921_061945.json` - Intel CPUs under €100
- `pc_mix_graphic_card_motherboard_nvidia_asus_€200-500_20250921_062028.json` - NVIDIA/ASUS components €200-500
- `pc_mix_all_rgb_€50-_20250921_062100.json` - All RGB components under €50

## File Structure

Each output JSON file contains an array of product objects with:
- `name`: Product name
- `price`: Price with € symbol
- `url`: Direct link to PC Part Picker
- `raw_text`: Full product description
- `scraped_at`: Timestamp
- `source`: Source website
- `page`: Page number from original scrape

## Tips

1. **Use Interactive Mode** for exploring available options
2. **Combine Components** to find compatible parts
3. **Use Keywords** to find specific features (RGB, modular, etc.)
4. **Price Filtering** helps find components in your budget
5. **Check Sample Results** to verify your search criteria

## Examples for Common Use Cases

### Build a Gaming PC
```bash
python pc_component_mixer.py --components cpu,graphic_card,motherboard,memory --keywords "gaming" --max-price 300
```

### Find RGB Components
```bash
python pc_component_mixer.py --components all --keywords "rgb"
```

### Budget Build Under €500
```bash
python pc_component_mixer.py --components all --max-price 100
```

### High-End Components
```bash
python pc_component_mixer.py --components all --min-price 500
```

### Specific Brand Search
```bash
python pc_component_mixer.py --components all --keywords "corsair"
```
