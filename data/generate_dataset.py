"""
Generate the sample training dataset for the Citizen Grievance System ML module.

Produces data/grievance_dataset.csv with columns: complaint, category, priority
Balanced: 60 rows per category (Water/Road/Electricity), 20 per priority (High/Medium/Low).

You can replace this CSV with your own data as long as it keeps the same columns.
"""
import csv
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "grievance_dataset.csv")

# Each entry: (complaint, category, priority)
ROWS = []

# ---------------------------------------------------------------
# WATER - High priority (20)
# ---------------------------------------------------------------
WATER_HIGH = [
    "No water supply in our area for 3 days, emergency situation",
    "Water pipe has burst and flooded the entire street",
    "Contaminated water supply causing illness in the neighborhood",
    "Main water pipeline broken, whole colony without water",
    "Sewage overflow mixing with drinking water supply",
    "Water tanker not arrived for 5 days, residents desperate",
    "Underground water tank leaking severely into basement",
    "Massive water leak from main supply line on main road",
    "Water supply completely cut off without notice for 4 days",
    "Sewage water entering homes during heavy rain, health risk",
    "Broken hydrant gushing water onto the road for hours",
    "Raw sewage flowing in open drain near school, children at risk",
    "Water contamination reported by multiple households, smell bad",
    "Flooded street due to blocked drainage, houses submerged",
    "No drinking water available, people queuing for hours",
    "Burst pipe near hospital affecting water supply to patients",
    "Sewage backing up into homes, urgent repair needed",
    "Water main break causing sinkhole on busy road",
    "Entire ward without water for days, no tanker support",
    "Toxic smell from water, possible chemical contamination",
]

# WATER - Medium priority (20)
WATER_MEDIUM = [
    "Water pipe is leaking near residential building",
    "Low water pressure in our colony since yesterday",
    "Water supply timing irregular for the past week",
    "Tap water has a brownish color and strange smell",
    "Leaking water meter causing high bill for residents",
    "Water tanker arrives late every day, schedule needed",
    "Drainage blockage causing water logging after rain",
    "Water storage tank not cleaned for years, dirty water",
    "Frequent water cuts during morning hours affecting daily routine",
    "Overflowing drain near market creating unhygienic conditions",
    "Water pressure too low to fill overhead tanks",
    "Rusted pipes delivering discolored water to homes",
    "Leakage from public water tap wasting water daily",
    "Sewer line partially blocked, slow drainage",
    "Water bill unusually high despite normal usage",
    "Drinking water has chlorine smell and bad taste",
    "Underground drainage pipe leaking into garden area",
    "Water supply available only 2 hours a day, insufficient",
    "Manhole cover missing near water pipeline, danger",
    "Recurring water leak from same pipe, needs permanent fix",
]

# WATER - Low priority (20)
WATER_LOW = [
    "Small water leak from garden tap, easy fix",
    "Water pressure slightly low in upper floors only",
    "Minor drip from bathroom pipe fitting",
    "Public water tap needs a new washer",
    "Water meter glass is foggy, cannot read properly",
    "Slight discoloration in water sometimes",
    "Drain cover is loose and rattles when vehicles pass",
    "Small puddle near water tap after use",
    "Water supply schedule changed, need confirmation",
    "Minor rust stain on the water tank lid",
    "Low flow from the community tap in afternoon",
    "Small crack in the external water pipe, slow leak",
    "Water pressure drops briefly during peak hours",
    "Drainage grate slightly tilted, minor issue",
    "Tap handle is loose and needs tightening",
    "Water bill seems slightly higher than usual",
    "Slight algae growth on top of water tank",
    "Public tap runs for a while after closing",
    "Minor water logging near drain after light rain",
    "Pipe insulation worn out in one small section",
]

# ---------------------------------------------------------------
# ROAD - High priority (20)
# ---------------------------------------------------------------
ROAD_HIGH = [
    "Large pothole on main road near school causing accidents daily",
    "Road completely collapsed after heavy rain, dangerous section",
    "Major sinkhole opened up on the highway overnight",
    "Bridge support cracked, road closed to traffic, urgent",
    "Massive pothole causing multiple accidents near hospital",
    "Road cave in after underground pipe burst, vehicles stuck",
    "Severe road damage on busy intersection, traffic chaos",
    "Landslide debris covering entire road near residential area",
    "Large pothole on sharp turn, several vehicles damaged",
    "Road surface completely broken on main market street",
    "Dangerous pothole on school zone road, children at risk",
    "Big crater in middle of road caused by recent rain",
    "Major road failure near bridge approach, half road gone",
    "Heavy pothole damage on bus route, passengers injured",
    "Road undermined by drainage failure, imminent collapse",
    "Large depression on road causing vehicles to bottom out",
    "Main road broken near railway crossing, long traffic jams",
    "Pothole on highway exit ramp, multiple tire bursts",
    "Road surface washed away in residential lane",
    "Giant pothole near bus stop, commuters falling",
]

# ROAD - Medium priority (20)
ROAD_MEDIUM = [
    "Several potholes on the road need filling before rain",
    "Road surface has many cracks and is uneven",
    "Footpath broken near market, pedestrians struggling",
    "Speed breaker damaged and needs repair",
    "Road shoulder has eroded in several places",
    "Uneven road surface causing discomfort to drivers",
    "Damaged manhole cover on road causing bumpy ride",
    "Potholes forming near bus stop, needs attention",
    "Road markings faded, lane division not visible",
    "Sidewalk tiles broken and dangerous for walking",
    "Cracks appearing on newly laid road surface",
    "Road drainage blocked causing water accumulation",
    "Pothole on service road near residential area",
    "Broken speed breaker creating hazard for two wheelers",
    "Damaged road divider exposing sharp metal edges",
    "Potholes on the approach road to colony gate",
    "Rough road surface causing vehicle damage complaints",
    "Missing road sign at intersection, confusion among drivers",
    "Pedestrian crossing paint completely worn off",
    "Potholes accumulating water during rain, mosquitoes",
]

# ROAD - Low priority (20)
ROAD_LOW = [
    "Small pothole on side road near residential area",
    "Minor crack on the road surface, no immediate danger",
    "Road paint slightly faded in one section",
    "Small debris on shoulder of the road",
    "Minor unevenness on the road near parking area",
    "Small piece of road edge chipped off",
    "Pothole is small and shallow, low risk",
    "Road marking needs minor touch up",
    "Slight dip in road surface near drain cover",
    "Minor gravel scattered on one side of road",
    "Small crack near the curb, easy to fix",
    "Road shoulder has minor wear from traffic",
    "Minor pothole on quiet residential lane",
    "Slight roughness on road surface in spots",
    "Broken tile on sidewalk, small area only",
    "Minor loose gravel on the edge of road",
    "Road surface has small patches of wear",
    "Slight depression near drain, minor water pooling",
    "Minor crack on speed breaker surface",
    "Small pothole in parking area of market",
]

# ---------------------------------------------------------------
# ELECTRICITY - High priority (20)
# ---------------------------------------------------------------
ELEC_HIGH = [
    "Electric wire has fallen on road extremely dangerous live wire",
    "Transformer exploded and caught fire near residential area",
    "High tension wire snapped and lying on the road",
    "Electric pole leaning dangerously over the street",
    "Power outage affecting entire city block for 12 hours",
    "Sparking from main electric line near school, fire risk",
    "Live electric wire fallen near playground, children playing",
    "Electric shock from street light pole, someone injured",
    "Substation on fire, smoke and sparks visible",
    "Exposed live wires after tree fell on power line",
    "Electric cable burning on the road, traffic stopped",
    "Power transformer leaking oil and smoking heavily",
    "Electric wire fallen on water logged road, electrocution risk",
    "High voltage wire sagging dangerously low over road",
    "Electric box exploded, blackout in the whole ward",
    "Burning electric wire near gas cylinder shop, explosion risk",
    "Power cable fallen across main road, vehicles swerving",
    "Severe electric shock from metro pillar, urgent",
    "Electric pole fire spreading to nearby trees",
    "Major power failure affecting hospital and emergency services",
]

# ELECTRICITY - Medium priority (20)
ELEC_MEDIUM = [
    "Street light not working in dark crime prone area near park",
    "Multiple street lights out in residential block, safety issue",
    "Frequent power cuts every evening for the past week",
    "Electric meter box making buzzing sound and sparking",
    "Voltage fluctuation damaging household appliances",
    "Street light pole rusted and unstable, may fall",
    "Power outage for 6 hours daily, affecting study for students",
    "Electric cable exposed on footpath, people tripping",
    "Transformer humming loudly and vibrating",
    "Low voltage in entire colony, ACs and motors not running",
    "Street light stays on during the day, wasting electricity",
    "Electric wires hanging loose above the footpath",
    "Power cut happens every time it rains",
    "Billing error, charged for twice the actual usage",
    "Faulty street light flickering on and off",
    "Electric junction box open and wires exposed",
    "High electricity bill despite minimal usage",
    "Power fluctuation causing lights to dim frequently",
    "Street light out near the women hostel entrance",
    "Old electric wiring in pole sparking during rain",
]

# ELECTRICITY - Low priority (20)
ELEC_LOW = [
    "Single street light bulb not working in a lane",
    "Small light fixture on pole needs new bulb",
    "Street light is dim in the evening",
    "Minor spark from switch box, low risk",
    "One street light flickers slightly sometimes",
    "Electric meter reading display is dim",
    "Small crack on the street light pole base",
    "Low wattage bulb on community road",
    "Minor billing discrepancy, small amount",
    "Street light turns on slightly late",
    "Small exposed wire end taped but needs sealing",
    "Light sensor on street light not working properly",
    "Minor voltage dip during peak hours only",
    "One bulb in the street light cluster is out",
    "Small rust spot on electric pole",
    "Street light pole number plate missing",
    "Minor humming from street light fixture",
    "Slight delay in power restoration after minor cuts",
    "Low brightness on one section of the road",
    "Small wiring issue in the public phone booth",
]

for txt in WATER_HIGH:
    ROWS.append((txt, "Water", "High"))
for txt in WATER_MEDIUM:
    ROWS.append((txt, "Water", "Medium"))
for txt in WATER_LOW:
    ROWS.append((txt, "Water", "Low"))
for txt in ROAD_HIGH:
    ROWS.append((txt, "Road", "High"))
for txt in ROAD_MEDIUM:
    ROWS.append((txt, "Road", "Medium"))
for txt in ROAD_LOW:
    ROWS.append((txt, "Road", "Low"))
for txt in ELEC_HIGH:
    ROWS.append((txt, "Electricity", "High"))
for txt in ELEC_MEDIUM:
    ROWS.append((txt, "Electricity", "Medium"))
for txt in ELEC_LOW:
    ROWS.append((txt, "Electricity", "Low"))

with open(OUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["complaint", "category", "priority"])
    for row in ROWS:
        writer.writerow(row)

print(f"Dataset written to {OUT}")
print(f"Total rows: {len(ROWS)}")
from collections import Counter
cats = Counter(r[1] for r in ROWS)
pris = Counter(r[2] for r in ROWS)
print(f"Category counts: {dict(cats)}")
print(f"Priority counts: {dict(pris)}")
