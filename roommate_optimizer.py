import pulp, pandas as pd

"""
Constraints
    - Do not room anyone with a person they gave a 0 rating to
    - There are X rooms total (based on GUI input)
    - One room can hold five people, the other two rooms hold four people ###replace this with GUI later.
    - 0 is the lowest score, six is the highest score
    - 'That's Me!' indicates that this is the person submitting, a person needs to be in the same room as themself. 
      'That's Me!' is replaced with a 0.
    - No person can be in two rooms
    - Everyone must be in a room

Objective Function
    - Maximize the overall score per room # potentially do the average

Other Notes:
    - The headers are long strings with the names hidden at the very end within `[ ]`. If a column header says 'That's Me!' 
      replace the timestamp in the first column with the name within `[ ]` specified.
    - Some people have not filled out the forms. Add a row for those people (the names in the `[ ]`), giving everyone a rating of 3. 
"""

#### ADD A HANDLER IN CASE SOMEONE SUBMITS MULTIPLE TIMES, TAKE THE MOST RECENT RESPONSE, DROP ALL OTHERS 

def clean_ratings(input_csv):
    '''
    Parameters:
        input_csv: csv file with the roommate ratings
    
    Output:
        ordered_df: dataframe with cleaned roommate ratings, organized alphabetically
    '''
    df = pd.read_csv(input_csv)

    # Get name list from columns, pulling only full names between the [ ]
    names = df.columns[1:].str.extract(r'\[(.*?)\]$')[0].tolist()
    df.columns = [df.columns[0]] + names

    # Submitter
    submitters = []
    for index, row in df.iterrows():
        found = False
        for name in names:
            if str(row[name]).strip() == "That's Me!":
                submitters.append(name)
                found = True
                break
        if not found:
            # In case "That's Me!" is missing
            submitters.append(f"Unknown_{index}")

    # Replace first column with the submitters
    df[df.columns[0]] = submitters

    # Replace values and convert to numeric
    df = df.replace("Do Not Room", 0)
    # Use 0 for "That's Me!" as it shouldn't add to the score of a pair (i,i)
    df = df.replace("That's Me!", 0)

    # Convert rating columns to numeric
    for col in names:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Rename first column to 'Response'
    df.rename(columns={df.columns[0]: 'Response'}, inplace=True)

    # Identify anyone who did not submit
    missing_people = [f for f in names if f not in submitters]
    print("Missing flowers:", missing_people)

    # Add missing people back in, they rate everyone a 3
    for mf in missing_people:
        new_row = {col: 3 for col in names}
        new_row['Response'] = mf
        new_row[mf] = 0 # That's Me! equivalent
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    # Reorder columns to have Response first, then all names in alphabetical order
    ordered_df = df[['Response'] + names]
    # Set Response as index and sort by index to have a consistent matrix
    ordered_df.set_index('Response', inplace=True)
    ordered_df = ordered_df.reindex(index=names, columns=names)

    return ordered_df

def assign_rooms(input_csv, capacities):
    '''
    Parameters:
        input_csv: csv file with the roommate ratings
        capacities: number of people that can sleep in a room
    
    Output:
        room_assignments: dictionary {room #: people in the room}
    '''
    df = clean_ratings(input_csv)

    names = df.index.tolist()
    N = len(names)
    R = df.values

    if sum(capacities) < N:
        return None, f"Capacity mismatch: Rooms hold {sum(capacities)}, but there are {N} people."

    # Set the problem in pulp
    prob = pulp.LpProblem("RoommateAssignment", pulp.LpMaximize)

    # Decision variables
    # x[i][r] = 1 if person i is in room r
    rooms = range(len(capacities))
    x = pulp.LpVariable.dicts("x", (range(N), rooms), cat='Binary')
    y = pulp.LpVariable.dicts("y", (range(N), range(N), rooms), cat='Binary')

    # Constraints
    # 1. Each person in one room
    for i in range(N):
        prob += pulp.lpSum([x[i][r] for r in rooms]) == 1

    # 2. Room sizes
    for r in rooms:
        prob += pulp.lpSum([x[i][r] for i in range(N)]) == capacities[r]

    # 3. No 0 ratings (excluding self-rating)
    for i in range(N):
        for j in range(N):
            if i != j and R[i][j] == 0:
                for r in rooms:
                    prob += x[i][r] + x[j][r] <= 1

    # 4. Objective: Maximize sum of ratings
    # Need the product x[i][r] * x[j][r] --> linearize
    for i in range(N):
        for j in range(N):
            for r in rooms:
                # y[i][j][r] = x[i][r] * x[j][r]
                prob += y[i][j][r] <= x[i][r]
                prob += y[i][j][r] <= x[j][r]

    # Objective function
    prob += pulp.lpSum([R[i][j] * y[i][j][r] for i in range(N) for j in range(N) for r in rooms])

    # Solve
    prob.solve()

    if pulp.LpStatus[prob.status] != 'Optimal':
        return None, "Could not find an optimal solution. Check for conflicting 'Do Not Room' constraints."

    # Results
    results = []
    for i in range(N):
        for r in rooms:
            if pulp.value(x[i][r]) == 1:
                results.append({"Name": names[i], "Room": r + 1})

    return pd.DataFrame(results), None

if __name__ == "__main__":
    print(assign_rooms('Seattle Roommate Preferences.csv'))