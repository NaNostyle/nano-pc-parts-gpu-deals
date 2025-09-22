#!/usr/bin/env python3
"""
Test script to check available categories in lbc package
"""

import lbc

print("Available categories in lbc package:")
print("=" * 40)

# Try to list all attributes of Category
for attr in dir(lbc.Category):
    if not attr.startswith('_'):
        print(f"  {attr}")

print("\nTrying to access some common categories:")
try:
    print(f"  INFORMATIQUE: {hasattr(lbc.Category, 'INFORMATIQUE')}")
    print(f"  COMPUTER: {hasattr(lbc.Category, 'COMPUTER')}")
    print(f"  ELECTRONICS: {hasattr(lbc.Category, 'ELECTRONICS')}")
    print(f"  INFORMATIQUE_ET_MULTIMEDIA: {hasattr(lbc.Category, 'INFORMATIQUE_ET_MULTIMEDIA')}")
except Exception as e:
    print(f"Error: {e}")

# Try to create a client and see what happens
print("\nTesting client creation:")
try:
    client = lbc.Client()
    print("✅ Client created successfully")
except Exception as e:
    print(f"❌ Error creating client: {e}")
