# Imports


from ortools.linear_solver import pywraplp
import matplotlib.pyplot as plt
import pandas as pd
import csv

# Instantiate Solver
solver = pywraplp.Solver('Generator', pywraplp.Solver.GLOP_LINEAR_PROGRAMMING)
# Ingest the Input
generators = pd.read_csv('generator_info.csv')
demand = pd.read_csv('demand.csv')
print(generators.head())
print(demand.head())
generators.columns = ["Generator", "Type", "Fuel", "fuel consumption of gen", "Fixed fuel consumption of gen",
                      "Fuel consumption of gen start-up", "Fuel consumption of gen shut-down", "Upward ramp",
                      "Downward ramp", "Maximum gross power of gen", "Minimum gross power of gen",
                      "Gross to net power conversion factor for gen", "Cost of fuel consumed by gen", "Fixed O&M cost",
                      "Variable O&M cost", "MTBF"]
demand.columns = ['demand']
dem = demand["demand"].values.tolist()
gen = generators["Generator"].values.tolist()
max_power = generators["Maximum gross power of gen"].values.tolist()
min_power = generators["Minimum gross power of gen"].values.tolist()
alpha = generators["fuel consumption of gen"].values.tolist()
beta = generators["Fixed fuel consumption of gen"].values.tolist()
start_up = generators["Fuel consumption of gen start-up"].values.tolist()
shut_down = generators["Fuel consumption of gen shut-down"].values.tolist()
Upward = generators["Upward ramp"].values.tolist()
Downward = generators["Downward ramp"].values.tolist()
bg = generators["Gross to net power conversion factor for gen"].values.tolist()
fg = generators["Cost of fuel consumed by gen"].values.tolist()
ocg = generators["Fixed O&M cost"].values.tolist()
og = generators["Variable O&M cost"].values.tolist()
MTBF = generators["MTBF"].values.tolist()
print("Generators: ", gen)
print("Demande: ", dem)
print("Maximum gross power of generator: ", max_power)
print("Minimum gross power of generator: ", min_power)

#Expanding demande:
t=72  #Number of hours
a=t//len(dem)
r=t%len(dem)
demand_=a*dem+dem[:r]

# Create Continuous variables for each generator and each hour in a day with their lower and upper bounds
Qg = []
Ug = []
Yg = []
Zg = []
for g in range(0, 34):
    Ug.append([solver.NumVar(0, 1, f'U{i}') for i in range(0, t)])
    Yg.append([solver.NumVar(0, 1, f'Y{i}') for i in range(0, t)])
    Zg.append([solver.NumVar(0, 1, f'Z{i}') for i in range(0, t)])
    Qg.append([solver.NumVar(0, bg[g] * max_power[g], f'G{i}') for i in range(0, t)])




# Creating Constraints
# 1. Energy generated per hour is equal to the per hour demand

for i in range(0, t-1):
    C = 0
    for g in range(0, 34):
        C += Qg[g][i]
    solver.Add(C == demand_[i])

# 2. Ramp, start-up and shut-down Constraints
for i in range(1, t):
    for g in range(0, 34):
        solver.Add(Qg[g][i] - Qg[g][i - 1] <= Upward[g])
        solver.Add(Qg[g][i - 1] - Qg[g][i] <= Downward[g])
        solver.Add(Ug[g][i] == Ug[g][i - 1] + Yg[g][i] - Zg[g][i])
# 3. Minimum and maximum net capacities Constraints
for i in range(0, t):
    for g in range(0, 34):
        solver.Add(Qg[g][i] >= Ug[g][i] * bg[g] * min_power[g])
        solver.Add(Qg[g][i] <= Ug[g][i] * bg[g] * max_power[g])


print("Number of constraints : ", solver.NumConstraints())
#Generators in maintenance
M=[26,27,25,24]
costs={'No maintenance':545996.8, 'G25':594646.3, 'G18, G25':594646.3,'G17, G18, G25':597178.2 , 'G1, G3, G5':545996.8,'G2, G5, G7':545996.8,'G3, G5, G9, G20':545996.8}
z=[545996.8, 594646.3, 594646.3, 597178.2, 545996.8, 545996.8, 545996.8]
# Objective
objective = solver.Objective()
# Coeff settings
for i in range(t):
    for g in range(34):
        if  g in M and i<=48 :
            objective.SetCoefficient(Qg[g][i], (fg[g] * alpha[g] + og[g]) / bg[g])
            solver.Add(Ug[g][i] == 0)
            solver.Add(Yg[g][i] == 0)
            solver.Add(Zg[g][i] == 0)
        else:
            objective.SetCoefficient(Qg[g][i], fg[g] * alpha[g]  / bg[g])
        objective.SetCoefficient(Ug[g][i], fg[g] * beta[g])
        objective.SetCoefficient(Yg[g][i], fg[g] * start_up[g])
        objective.SetCoefficient(Zg[g][i], fg[g] * shut_down[g])

objective.SetMinimization()  # Minimise Objective Function
# Solve the system.
result = solver.Solve()
if result == solver.OPTIMAL:
    for v in solver.variables():
        print(f"{v.name()} = {v.solution_value():.1f}")
    #print(f"z = {objective.Value():.1f}") #Case without maintenance
    print(f"z = {objective.Value()+ sum(ocg):.1f}")  # Case without maintenance
else:
    print("Problem is not feasible")

# Create list of Solution Variable
sol_var = []
for v in solver.variables(): sol_var.append(v.solution_value())
# Set Generator lists
G_Solutions = []
U_Solutions = []
Y_Solutions = []
Z_Solutions = []
# Generator lists of power generator
for g in range(0, 34):
    G_, U_, Y_, Z_= [],[],[],[]
    for i in range(0, t):
        G_.append(Qg[g][i].solution_value())
        U_.append(Ug[g][i].solution_value())
        Y_.append(Yg[g][i].solution_value())
        Z_.append(Zg[g][i].solution_value())
    G_Solutions.append(G_)
    U_Solutions.append(U_)
    Y_Solutions.append(Y_)
    Z_Solutions.append(Z_)

hours= [i for i in range(1,t+1)]


# Viz per FUEL
G_OIL = []
G_COAL = []
G_LWR = []
G_WIND = []
G_HYDRO = []

for g in range(0, 34):
    if g < 9 or (g > 12 and g < 16) or (g > 19 and g < 23):
        G_OIL.append(G_Solutions[g])
    elif g == 24 or g == 25:
        G_LWR.append(G_Solutions[g])
    elif g == 26 or g == 27:
        G_WIND.append(G_Solutions[g])
    elif g >27:
        G_HYDRO.append(G_Solutions[g])
    else:
        G_COAL.append(G_Solutions[g])
print(G_HYDRO)

G_OIL_ = []
G_COAL_ = []
G_LWR_ = []
G_WIND_ = []
G_HYDRO_ = []

for i in range(t):
    o,c,l,w,h=0,0,0,0,0
    for g in range(len(G_OIL)):
        o+=G_OIL[g][i]
    G_OIL_.append(o)
    for g in range(len(G_COAL)):
        c+=G_COAL[g][i]
    G_COAL_.append(c)
    for g in range(len(G_LWR)):
        l+=G_LWR[g][i]
    G_LWR_.append(l)
    for g in range(len(G_WIND)):
        w+=G_WIND[g][i]
    G_WIND_.append(w)
    for g in range(len(G_HYDRO)):
        h+=G_HYDRO[g][i]
    G_HYDRO_.append(h)
print(G_COAL_)




'''

plt.plot(hours, G_OIL_, label='OIL Generator')
plt.plot(hours, G_COAL_, label='COAL Generator')
plt.plot(hours, G_LWR_, label='LWR Generator')
plt.plot(hours, G_WIND_, label='WIND Generator')
plt.plot(hours, G_HYDRO_, label='HYDRO Generator')
plt.legend()
plt.title("UCP Optimized Solution")
plt.margins(0)
plt.ylim(0, 1200)
plt.xlabel("Number of hours")
plt.ylabel("Total net power dispatched by generator")
plt.show()

'''



# plot bars
'''
barWidth = 0.85
plt.bar(hours, G_OIL_, color='#5E1822', label='OIL Generator', edgecolor='white', width=barWidth)
plt.bar(hours, G_COAL_,color='#9C5C5D', label='COAL Generator', bottom=G_OIL_,  edgecolor='white', width=barWidth)
plt.bar(hours, G_LWR_,color='#BF8291', label='LWR Generator', bottom=[i + j for i, j in zip(G_OIL_, G_COAL_)], edgecolor='white',width=barWidth)
plt.bar(hours, G_WIND_, color='#9A8EA4',label='WIND Generator', bottom=[i + j + k for i, j, k in zip(G_OIL_, G_COAL_,G_LWR_)], edgecolor='white',width=barWidth)
plt.bar(hours, G_HYDRO_,color='#EEBCBF', label='HYDRO Generator', bottom=[i + j + k + l for i, j, k, l in zip(G_OIL_, G_COAL_,G_LWR_,G_WIND_)], edgecolor='white',width=barWidth)
plt.legend(loc='upper left', bbox_to_anchor=(1,1), ncol=1)
plt.title("UCP Optimized Solution")
plt.margins(0)
plt.ylim(0, 1600)
plt.xlim(0, t-.5)
plt.show()
'''
#Cost calculating
COST=[]

for i in range(t):
    c = 0
    for g in range(34):
        c+=G_Solutions[g][i]*fg[g] * alpha[g] / bg[g] + U_Solutions[g][i]* fg[g] * beta[g] + Y_Solutions[g][i]* fg[g] * start_up[g] + Z_Solutions[g][i]*fg[g] * shut_down[g]
    COST.append(c)
print("Cost")
print(COST)

#Write cost in csv
'''
file = open("scenarios.txt", "w")
writer = csv.writer(file)
for w in range(len(COST)):
    writer.writerow([COST[w]])
file.close()
'''
df = pd.read_csv("scenarios.csv")
df["scen1"] = "abc"
df.to_csv("sample.csv", index=False)
#cost plot


plt.plot(hours, COST, label='COST ($)')
plt.legend()
plt.title("UCP Optimized Solution of Scenario 2")
plt.margins(0)
plt.xlabel("Number of hours")
plt.ylabel("Total cost of generated energy per hour in $")
plt.show()


# cost per scenario
'''
height = z
bars = ('Scenario 1', 'Scenario 2', 'Scenario 3', 'Scenario 4', 'Scenario 5', 'Scenario 6', 'Scenario 7')
x_pos = [1,2,3,4,5,6,7]
plt.bar(x_pos, height)
plt.xticks(x_pos, bars)
plt.show()
'''


