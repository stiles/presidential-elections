import json
import re
import html
from pathlib import Path

import requests
from bs4 import BeautifulSoup
import us

# Build fips -> abbr mapping from the us library (50 states + DC), exclude territories
_all_fips_to_abbr = us.states.mapping("fips", "abbr")
_exclude = {"60", "66", "69", "72", "78"}  # AS, GU, MP, PR, VI
STATE_FIPS_TO_ABBR = {
    fips: abbr
    for fips, abbr in _all_fips_to_abbr.items()
    if fips and fips.isdigit() and int(fips) <= 56 and fips not in _exclude
}
STATE_FIPS_TO_ABBR["11"] = "DC"


def parse_percent(percent_text: str) -> float:
    cleaned = percent_text.strip().replace("%", "")
    if cleaned == "":
        return 0.0
    return float(cleaned) / 100.0


def parse_int(num_text: str) -> int:
    return int(num_text.replace(",", "").strip())


def extract_from_area(area: BeautifulSoup, state_abbr: str):
    href = area.get("href", "")
    m = re.search(r"fips=(\d+)", href)
    if not m:
        return None
    county_fips = m.group(1)

    county_name_raw = area.get("alt", "").strip()
    county_name = county_name_raw.replace(" County", "").upper()

    # onmouseover contains showAltMsg('<escaped html>')
    over = area.get("onmouseover", "")
    m2 = re.search(r"showAltMsg\('(.*)'\)", over, re.S)
    if not m2:
        return None
    frag_escaped = m2.group(1)
    frag_html = html.unescape(frag_escaped)
    frag_soup = BeautifulSoup(frag_html, "html.parser")

    tds = [td.get_text(strip=True) for td in frag_soup.find_all("td")]

    # Find total vote
    total_votes = None
    for i, text in enumerate(tds):
        if text == "Total Vote:" and i + 1 < len(tds):
            total_votes = parse_int(tds[i + 1])
            break
    if total_votes is None:
        return None

    dem_share = None
    rep_share = None
    # Candidate rows are [Name][(Party)][Percent]
    for i in range(len(tds) - 2):
        party = tds[i + 1]
        percent = tds[i + 2]
        if party == "(D)":
            dem_share = parse_percent(percent)
        elif party == "(R)":
            rep_share = parse_percent(percent)

    # Some counties may be missing a party in the top-two; default to 0
    dem_share = dem_share or 0.0
    rep_share = rep_share or 0.0

    dem_votes = round(total_votes * dem_share)
    rep_votes = round(total_votes * rep_share)
    winner = "dem" if dem_share > rep_share else "rep"

    return {
        "fips": county_fips,
        "county_name": county_name,
        "state_po": state_abbr,
        "year": "2024",
        "votes_dem": dem_votes,
        "votes_rep": rep_votes,
        "votes_all": total_votes,
        "dem_pct": round(dem_share, 4),
        "rep_pct": round(rep_share, 4),
        "winner": winner,
    }


def fetch_state_counties(state_fips: str) -> list:
    state_fips2 = state_fips.zfill(2)
    state_abbr = STATE_FIPS_TO_ABBR[state_fips2]
    url = (
        f"https://uselectionatlas.org/RESULTS/state.php?year=2024&fips={int(state_fips2)}&f=1&off=0&elect=0"
    )
    resp = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X) Python scraper",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
        timeout=30,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    map_tag = soup.find("map")
    if map_tag is None:
        return []

    results = []
    for area in map_tag.find_all("area"):
        parsed = extract_from_area(area, state_abbr)
        if parsed:
            results.append(parsed)
    return results


def main():
    all_results = []
    for fips in sorted(STATE_FIPS_TO_ABBR.keys(), key=lambda x: int(x)):
        state_results = fetch_state_counties(fips)
        all_results.extend(state_results)
        print(f"Fetched {STATE_FIPS_TO_ABBR[fips]}: {len(state_results)} counties")

    out_path = Path("data/processed/presidential_county_results_2024.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        json.dump(all_results, f, indent=2)
    print(f"Wrote {len(all_results)} county records to {out_path}")


if __name__ == "__main__":
    main()