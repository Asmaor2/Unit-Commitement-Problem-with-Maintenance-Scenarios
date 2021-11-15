# Imports
from ortools.linear_solver import pywraplp
import matplotlib.pyplot as plt
import pandas as pd
# Instantiate Solver
solver = pywraplp.Solver('Generator', pywraplp.Solver.GLOP_LINEAR_PROGRAMMING)
#Ingest the Input
generators = pd.read_csv('generator_info.csv')
print(generators.head())
generators.columns = ["name","type","lower_bound (MW)","upper_bound (MW)", "cost/MW", "CO2/MW"]
lower_bound = generators["lower_bound (MW)"].values.tolist()
upper_bound = generators["upper_bound (MW)"].values.tolist()
cost = generators["cost/MW"].values.tolist()
print("Lower Bounds: ", lower_bound)
print("Upper Bounds: ", upper_bound)
print("Costs: ", cost)
#Read the Demand.csv file
demand_df = pd.read_csv('demand.csv', header=None, names=['mw'])
print("Demand in MW")
print(demand_df.head())
#Read the Solar Curve.csv file
solar_df = pd.read_csv('solar_curve.csv', header=None, names=['sw'])
print("Solar curves")
print(solar_df.head(16))
#Create Continous variables for each generator and each hour in a day with their lower and upper bounds
A = [solver.NumVar(lower_bound[0], upper_bound[0], f'A{i}') for i in range(0,24)]
B = [solver.NumVar(lower_bound[1], upper_bound[1], f'B{i}') for i in range(0,24)]
C = [solver.NumVar(lower_bound[2], upper_bound[2], f'C{i}') for i in range(0,24)]
D = [solver.NumVar(lower_bound[3], upper_bound[3], f'D{i}') for i in range(0,24)]
E = solver.NumVar(lower_bound[4], upper_bound[4], "E")
F = solver.NumVar(lower_bound[5], upper_bound[5], "F")
G = solver.NumVar(lower_bound[6], upper_bound[6], "G")
H = [solver.NumVar(lower_bound[7], upper_bound[7], f'H{i}') for i in range(0,24)]
I = [solver.NumVar(lower_bound[8], upper_bound[8]*solar_df['sw'][i], f'I{i}') for i in range(0,24)]
J = [solver.NumVar(lower_bound[9], upper_bound[9]*solar_df['sw'][i], f'J{i}') for i in range(0,24)]

# Creating Contraints
# 1. Energy generated per hour is equal to the per hour demand
for i in range(0, 24):
    solver.Add(A[i] + B[i] + C[i] + D[i] + E + F + G + H[i] + I[i] + J[i] == demand_df['mw'][i])
    # for each hour
print(solver.NumConstraints())

#Objective
objective = solver.Objective()

# Time specific values
for i in range(0, 24):
    objective.SetCoefficient(A[i],cost[0])
    objective.SetCoefficient(B[i],cost[1])
    objective.SetCoefficient(C[i],cost[2])
    objective.SetCoefficient(D[i],cost[3])
    objective.SetCoefficient(H[i],cost[7])
    objective.SetCoefficient(I[i],cost[8])
    objective.SetCoefficient(J[i],cost[9])

# Solid generator values -> 24 hours
objective.SetCoefficient(E, cost[4] * 24)
objective.SetCoefficient(F, cost[5] * 24)
objective.SetCoefficient(G, cost[6] * 24)

objective.SetMinimization()  # Minimise Objective Function
# Solve the system.
result = solver.Solve()
if result == solver.OPTIMAL:
    for v in solver.variables():
        print(f"{v.name()} = {v.solution_value():.1f}")
    print(f"z = {objective.Value():.1f}")
else:
    print("Problem is not feasible")

#Create list of Solution Variable
sol_var = []
for v in solver.variables(): sol_var.append(v.solution_value())

# Set Generator lists
A_list, B_list, C_list, D_list, E_list, F_list, G_list, H_list, I_list, J_list = [], [], [], [], [], [], [], [], [], []
# Generator lists of power generator per generator
for i in range (0, 24): A_list.append(A[i].solution_value())
for i in range (0, 24): B_list.append(B[i].solution_value())
for i in range (0, 24): C_list.append(C[i].solution_value())
for i in range (0, 24): D_list.append(D[i].solution_value())
for i in range (0, 24): E_list.append(E.solution_value())
for i in range (0, 24): F_list.append(F.solution_value())
for i in range (0, 24): G_list.append(G.solution_value())
for i in range (0, 24): H_list.append(H[i].solution_value())
for i in range (0, 24): I_list.append(I[i].solution_value())
for i in range (0, 24): J_list.append(J[i].solution_value())

hours = []
for i in range(1, 25): hours.append(i)

# Visualisation
plt.plot(hours, A_list, label='Generator A hydro')
plt.plot(hours, B_list, label='Generator B hydro')
plt.plot(hours, C_list, label='Generator C hydro')
plt.plot(hours, D_list, label='Generator D hydro')
plt.plot(hours, E_list, label='Generator E solid')
plt.plot(hours, F_list, label='Generator F solid')
plt.plot(hours, G_list, label='Generator G solid')
plt.plot(hours, G_list, label='Generator H gaz')
plt.plot(hours, I_list, label='Generator I solar')
plt.plot(hours, J_list, label='Generator J solar')
plt.legend()
plt.title("UCP Optimized Solution")
plt.margins(0)
plt.show()