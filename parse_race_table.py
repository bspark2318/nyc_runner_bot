import re

def extract_race_table(selftext):
    """
    Extract the race schedule table from Reddit post selftext
    Returns the markdown table as a string
    """
    # Find the table that starts with |Race|Date|Release Date|Notes|
    table_pattern = r'\|Race\|Date\|Release Date\|Notes\|.*?(?=\n\n|\Z)'
    match = re.search(table_pattern, selftext, re.DOTALL)

    if match:
        return match.group(0).strip()
    return None


def parse_race_table(text):
    """Parse markdown table into structured race objects."""
    # Split into lines
    table_string = extract_race_table(text)
    lines = table_string.strip().split('\n')

    # Skip the header separator line (the one with |:-|:-|:-|:-|)
    data_lines = [line for line in lines[2:] if line.strip()]

    races = []
    
    for line in data_lines:
        # Split by pipe and clean up
        parts = [part.strip() for part in line.split('|')]
        # Remove empty first/last elements from splitting (but keep empty middle values)
        if parts and parts[0] == '':
            parts = parts[1:]
        if parts and parts[-1] == '':
            parts = parts[:-1]

        if len(parts) >= 4:
            race_name = parts[0]
            race_obj = {
                "race_name": race_name,
                "date": parts[1],
                "release_date": parts[2],
                "notes": parts[3]
            }
            races.append(race_obj)

    return races