import json

def parse_race_table(table_string):
    """Parse markdown table into structured race objects."""
    # Split into lines
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
            race_obj = {
                "race": parts[0],
                "date": parts[1],
                "release_date": parts[2],
                "notes": parts[3]
            }
            races.append(race_obj)

    return races


# Your table data
race_table = """|Race|Date|Release Date|Notes|
|:-|:-|:-|:-|
|Virtual Resolution 5K|1/1-1/10\*|December 2025|[Virtual](https://www.nyrr.org/run/virtual-racing)|
|[Joe Kleinerman 10K](https://events.nyrr.org/nyrr-joe-kleinerman-10k)|1/10|[10/9/25](https://www.nyrr.org/run/race-calendar/race-registration-launch-timeline)||
|[Fred Lebow Half](https://events.nyrr.org/nyrr-fred-lebow-manhattan-half)|1/25|[10/9/25](https://www.nyrr.org/run/race-calendar/race-registration-launch-timeline)||
|[Manhattan 10K](https://events.nyrr.org/nyrr-manhattan-10k)|2/1|Lottery - 10/1/25|[4/6](https://www.nyrr.org/run/guaranteed-entry/united-airlines-nyc-half)|
|[Gridiron 4M](https://events.nyrr.org/nyrr-gridiron-4m)|2/8|[10/9/25](https://www.nyrr.org/run/race-calendar/race-registration-launch-timeline)||
|[Al Gordon 5K](https://events.nyrr.org/nyrr-al-gordon-4m)|2/21|[10/9/25](https://www.nyrr.org/run/race-calendar/race-registration-launch-timeline)||
|[Washington Heights  5K](https://events.nyrr.org/nyrr-washington-heights-salsa-blues-and-shamrocks-5k)|3/1|[10/9/25](https://www.nyrr.org/run/race-calendar/race-registration-launch-timeline)|[Club Points](https://www.nyrr.org/getinvolved/club-points)|
|NYC Half|3/15|Oct/Nov (Lottery)|[4/6](https://www.nyrr.org/run/guaranteed-entry/united-airlines-nyc-half) \- [Club Points](https://www.nyrr.org/getinvolved/club-points)|
|Run As One 4M|4/5\*|January|[Club Points](https://www.nyrr.org/getinvolved/club-points)|
|Race for Kids 4M|4/12\*|January||
|Women's Half|4/26\*|January|Women Only|
|Mindful 5K|5/2\*|January||
|Brooklyn R-U-N 5K|5/6\*|January||
|Brooklyn Half|5/16\*|Dec (Lottery)|[4/6](https://www.nyrr.org/run/guaranteed-entry/united-airlines-nyc-half) \- [Club Points](https://www.nyrr.org/getinvolved/club-points)|
|Virtual Global Running Day|5/31-6/7\*|April 2026|[Virtual](https://www.nyrr.org/run/virtual-racing)|
|Mini 10K|6/6\*|January|Women Only|
|Queens 10K|6/13\*|TBD? Lottery?|[4/6](https://www.nyrr.org/run/guaranteed-entry/united-airlines-nyc-half) \- [Club Points](https://www.nyrr.org/getinvolved/club-points)|
|Front Runners 4M|6/27\*|January||
|Achilles 4M|6/28\*|January||
|Retro 4M|7/11\*|May||
|Team Champs 5M|7/26\*|TBD? Lottery?|[Club Points (double)](https://www.nyrr.org/getinvolved/club-points)|
|Percy Sutton Harlem 5K|8/8\*|May|[Club Points](https://www.nyrr.org/getinvolved/club-points)|
|Training Series 12M|8/16\*|May||
|Grete's Gallop 10K|8/22\*|May||
|5th Ave Mile|9/13?\*|May|[Club Points](https://www.nyrr.org/getinvolved/club-points)|
|Bronx 10M|9/20\*|TBD? Lottery?|[4/6](https://www.nyrr.org/run/guaranteed-entry/united-airlines-nyc-half) \- [Club Points](https://www.nyrr.org/getinvolved/club-points)|
|Training Series 18M|9/27\*|May||
|Jersey City 5K|10/4\*|June||
|Staten Island Half|10/11\*|TBD? Lottery?|[4/6](https://www.nyrr.org/run/guaranteed-entry/united-airlines-nyc-half) \- [Club Points](https://www.nyrr.org/getinvolved/club-points)|
|Abbott Dash to Finish 5K|10/31\*|June||
|NYC Marathon|11/1|Lottery in Feb|[Club Points](https://www.nyrr.org/getinvolved/club-points)|
|Race to Deliver 4M|11/22\*|June||
|Virtual Run for Thanks 5K|11/21-11/30\*|October 2026|[Virtual](https://www.nyrr.org/run/virtual-racing)|
|Ted Corbitt 15K|12/5\*|June|[Club Points](https://www.nyrr.org/getinvolved/club-points)|
|Frosty 5K|12/12\*|June||
|Midnight Run|12/31|June||"""

if __name__ == "__main__":
    races = parse_race_table(race_table)
    print(json.dumps(races, indent=2))
