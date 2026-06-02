"""Test the parser with holdings extraction."""

from src.ingestion.phase_2_2_parse.parser import parse_entry
from src.corpus.inventory import load_inventory

# Load inventory and find the Large Cap fund entry
entries = load_inventory()
large_cap_entry = None
for entry in entries:
    if "large-cap-fund" in entry.scheme_slug:
        large_cap_entry = entry
        break

if not large_cap_entry:
    print("Large Cap fund entry not found")
    exit(1)

print(f"Testing parser for: {large_cap_entry.scheme_name}")
print(f"URL: {large_cap_entry.url}")
print()

# Parse the entry with force=True to re-parse
doc, result = parse_entry(large_cap_entry, force=True)

if result.ok:
    print(f"Parse status: {result.parse_status}")
    print(f"Sections count: {result.sections_count}")
    print(f"Text length: {result.text_length}")
    print()
    
    # Check if holdings section exists
    holdings_section = None
    for section in doc.sections:
        if "holding" in section["heading"].lower():
            holdings_section = section
            break
    
    if holdings_section:
        print("✓ Holdings section found!")
        print(f"Heading: {holdings_section['heading']}")
        print(f"Text preview: {holdings_section['text'][:500]}...")
    else:
        print("✗ Holdings section NOT found")
        print("Available sections:")
        for section in doc.sections:
            print(f"  - {section['heading']}")
else:
    print(f"Parse failed: {result.errors}")
