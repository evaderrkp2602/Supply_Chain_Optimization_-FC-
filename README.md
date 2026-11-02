# Fulfillment Center SKU Slotting Optimization

An end-to-end supply-chain analytics project that models a B2B fulfillment center and uses linear programming to decide where each SKU should live on the pick floor, minimizing picker travel time under real warehouse constraints.

Stack: Python (pandas, NumPy), SQL (SQLite), PuLP for linear programming, Matplotlib, and Tableau.

This is an academic project on a synthetic dataset calibrated to resemble a real fulfillment center: 500 SKUs, two years of weekly pick volume, and four pick zones. Problems were deliberately planted (a long-tail demand curve, erratic SKUs, an unreliable replenishment source) so the models have something real to solve.

## Problem

A fulfillment center has thousands of SKUs but limited prime slots near its pick stations. Poor slotting makes pickers walk farther on the highest-volume items, inflating labor cost and cycle time. The goal is to place the fast movers closest.

## Approach

generate_data.py builds the synthetic FC and loads it into a SQLite database. abc_xyz.py segments SKUs by value (ABC) and demand predictability (XYZ) into a 3x3 slotting playbook. pareto.py quantifies demand concentration (the 80/20 rule). slotting.py is a linear program built with PuLP that assigns each SKU to a pick zone to minimize total travel. A Tableau dashboard presents picks-by-zone and KPI views for a non-technical audience.

## Key results

23 percent of SKUs drive 80 percent of all picks, a steep Pareto; those are the golden-zone candidates. The optimizer concentrates about 65 percent of all picks (1.9M of 3.0M) in the closest zone, even though it holds the fewest slots. Optimized average travel is about 8.0 seconds per pick, with the busiest SKUs automatically placed closest, versus arbitrary slotting which scatters them.

## The optimization model

Decision variable: x equals 1 if a SKU is slotted in a given zone, else 0. Objective: minimize the sum of picks times zone travel-time times the decision variable, across all SKU-zone pairs. Constraints: each SKU in exactly one zone, and each zone within its slot capacity. Why LP: per-SKU rules of thumb ignore shared zone capacity, while the LP optimizes all SKUs jointly and is provably optimal.

## Running it

Create a virtual environment and install pandas, numpy, pulp, and matplotlib. Then run generate_data.py to build the database, abc_xyz.py for segmentation, pareto.py for the Pareto chart, and slotting.py for the slotting LP with before and after travel numbers.

Rishikesh Selvaraj Pillai, MS Engineering Management (Supply Chain Management), Northeastern University.
