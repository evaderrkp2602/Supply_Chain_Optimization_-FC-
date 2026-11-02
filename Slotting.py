import sqlite3
import pandas as pd
import pulp
import os

con = sqlite3.connect("db/supply_chain.db")
df = pd.read_sql("SELECT sku_id, units_sold FROM demand_history", con)
con.close()

picks = df.groupby("sku_id")["units_sold"].sum().to_dict()
skus = list(picks.keys())

# Modelling the Warehouse Floor, few zones at different distances from the pick-station with limited number of slots
zones = {
    "Golden": {"travel_sec": 5,  "capacity": 60},
    "Near" : {"travel_sec" : 10, "capacity": 120},
    "Mid"  : {"travel_sec": 18, "capacity": 150},
    "Far":   {"travel_sec": 30, "capacity": 300},
}

# Two Number/KPI per zone matter travel_sec and how many SKUs fit i.e SKU capacity

# The zones must have enough total slots for all your SKUs therefore the following checkline

total_slots = sum(z["capacity"] for z in zones.values())
print (f"SKUs: {len(skus)} | Total slots: {total_slots}")
assert total_slots >= len(skus), "Not enough for all SKUs!"

# Creating the Optimization Problem
m = pulp.LpProblem("Slotting", pulp.LpMinimize)

# Creating the Decision Variables
x = pulp.LpVariable.dicts("Assign", [(s,z) for s in skus for z in zones], cat="Binary")
# This variable creates SKU - Zone Pairing for example if x [(4, "Golden")] = 1 would mean "put SKU 4 in the Golden Zone"

# This is our objective function and the grand total of travel time across every placement, exactly what we are going to be minimizing 
m += pulp.lpSum(picks[s] * zones[z]["travel_sec"] * x[(s,z)]
                for s in skus for z in zones)

# Constraint 1 - Each SKU goes into exactly one Zone and it cannot be in two places and it needs to be somewhere
for s in skus: # i.e for all SKUs the variable x should be 1 as in it has been kept somewhere
    m += pulp.lpSum(x[(s,z)]for z in zones) == 1

# Constraint 2 - Each Zone is within its slot Capacity
for z in zones:
    m += pulp.lpSum(x[(s,z)]for s in skus) <= zones[z]["capacity"]

# Solver 
m.solve(pulp.COIN_CMD(path="/opt/homebrew/bin/cbc", msg=0))   #the CBC solver crunches it; msg=0 hides it
print("Status:", pulp.LpStatus[m.status]) # should say "Optimal"

# How good is the solution?
optimized = pulp.value(m.objective)    # the minimized total travel time
total_picks = sum(picks.values())
print (f"Optimized avg tavel/pick: {optimized/total_picks:.2f} sec")

# Sanity Check: Where did the 10 Busiest SKUs land? They should land only in the Golden/Near Zone
top = sorted(skus, key=lambda s: picks[s], reverse=True)[:10]
print("\nTop-10 fastest SKUs --> assigned zone: ")
for s in top:
    zone = [z for z in zones if x[(s,z)].value() == 1][0]
    print(f" SKU {s:>3} picks={picks[s]:>8,}  ->   {zone}")

# Baseline: arbitrary slotting - SKUs placed in ID order, ignoring how fast they move
baseline = 0
i = 0
for z in zones:                                  # fill Golden, then Near, then Mid, then Far
    for _ in range(zones[z]["capacity"]):
        if i >= len(skus):
            break
        baseline += picks[skus[i]] * zones[z]["travel_sec"]   # whatever SKU happens to be next
        i += 1

reduction = (baseline - optimized) / baseline * 100
print(f"\nAvg travel/pick - arbitrary : {baseline/total_picks:.2f} sec")
print(f"Avg travel/pick - optimized : {optimized/total_picks:.2f} sec")
print(f"==> Travel time cut {reduction:.1f}% by optimized slotting")

# Exporting as a CSV file to create a PowerBI dashboard 


os.makedirs("reports", exist_ok = True)

# grab each SKU's ABC Class from the databse to enrich the output
con = sqlite3.connect ("db/supply_chain.db")
abc = pd.read_sql("SELECT sku_id, abc_class FROM products", con).set_index("sku_id")["abc_class"].to_dict()
con.close()

# build one row per SKU: its picks, its ABC class, and where the LP slotted it
rows = []
for s in skus:
    zone = [z for z in zones if x[(s, z)].value() == 1][0]   # the zone this SKU got
    rows.append({
        "sku_id": s,
        "picks": picks[s],
        "abc_class": abc.get(s, ""),
        "assigned_zone": zone,
        "travel_sec_per_pick": zones[zone]["travel_sec"],
        "travel_total": picks[s] * zones[zone]["travel_sec"],
    })

results = pd.DataFrame(rows)
results.to_csv("reports/slotting_results.csv", index=False)
print("Saved -> reports/slotting_results.csv")
