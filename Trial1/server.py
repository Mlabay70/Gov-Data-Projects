import os
import sqlite3

# Import the residential permits DB initializer from a separate file
from init_residential_db import init_residential_db
# Call DB initialization at startup
init_residential_db()
# ...existing code...
from flask import Flask, render_template, request, send_from_directory, redirect, url_for, jsonify
import sqlite3
import os

app = Flask(__name__)

# Next Project: Residential Construction Permits
@app.route('/nextproject', methods=['GET'])
def nextproject():
    return render_template('nextproject/index.html', result=None)

@app.route('/nextproject/query', methods=['POST'])
def nextproject_query():
    state = request.form.get('state', '').strip()
    result = ''
    trendline = None
    if state:
        conn = sqlite3.connect('residential_permits.db')
        c = conn.cursor()
        # Get all columns from the permits table
        c.execute('PRAGMA table_info(permits)')
        columns = [col[1] for col in c.fetchall()]
        # Query all rows for the given state
        c.execute('SELECT * FROM permits WHERE STUSAB = ?', (state,))
        rows = c.fetchall()
        if rows:
            result = '<table border="1"><tr>' + ''.join(f'<th>{col}</th>' for col in columns) + '</tr>'
            for row in rows:
                result += '<tr>' + ''.join(f'<td>{cell}</td>' for cell in row) + '</tr>'
            result += '</table>'
            # Build trendline data for ALL_PERMITS_XXXX fields
            years = []
            values = []
            for col in columns:
                if col.startswith('ALL_PERMITS_') and col[-4:].isdigit():
                    years.append(col[-4:])
                    idx = columns.index(col)
                    total = sum(int(row[idx]) if row[idx] not in (None, '') else 0 for row in rows)
                    values.append(total)
            # Ensure years and values are sorted by year
            print('DEBUG raw years:', years, type(years))
            print('DEBUG raw values:', values, type(values))
            # Check for accidental method references
            if callable(years):
                print('ERROR: years is a method, not a list!')
            if callable(values):
                print('ERROR: values is a method, not a list!')
            year_value_pairs = sorted(zip(years, values), key=lambda x: x[0])
            years_list = [str(y) for y, v in year_value_pairs]
            values_list = [int(v) for y, v in year_value_pairs]
            print('DEBUG years_list:', years_list, type(years_list))
            print('DEBUG values_list:', values_list, type(values_list))
            trendline = {
                'years': years_list,
                'values': values_list
            }
            print('DEBUG trendline:', trendline)
            print('DEBUG trendline types:', type(trendline['years']), type(trendline['values']))
        else:
            result = f'No permits found for state: {state}'
        conn.close()
    else:
        result = 'No state selected.'
    return render_template('nextproject/results.html', result=result, trendline=trendline)

# Route to serve favicon.ico
@app.route('/favicon.ico')
def favicon():
    return send_from_directory('.', 'favicon.ico')

# API endpoint to get building locations for a zip code
@app.route('/api/buildings')
def api_buildings():
    zipcode = request.args.get('zipcode', '').strip()
    state = request.args.get('state', '').strip()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    sql = '''
        SELECT [Real Property Asset Name], [Street Address], [City], [State], [Zip Code], [Latitude], [Longitude], [Available Square Feet], [Construction Date]
        FROM buildings
        WHERE [Zip Code] LIKE ?
    '''
    params = [f'%{zipcode}%']
    if state:
        sql += " AND [State] = ?"
        params.append(state)
    c.execute(sql, params)
    buildings = [
        {
            'name': row[0],
            'address': row[1],
            'city': row[2],
            'state': row[3],
            'zipcode': row[4],
            'lat': row[5],
            'lng': row[6],
            'available_sqft': row[7],
            'construction_date': row[8]
        }
        for row in c.fetchall()
    ]
    conn.close()
    return jsonify(buildings)


# Landing page route
@app.route('/')
def landing():
    return render_template('landing.html')

# Gov Build subproject route
@app.route('/govbuild')
def govbuild():
    return render_template('index.html', result=None)

# Serve static files (like style.css)
@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)


# Format the database using the CSV columns and import data
import csv
DB_PATH = 'database.db'
CSV_PATH = '2025-9-26-iolp-buildings - Sheet1.csv'
TABLE_NAME = 'buildings'

def format_and_import_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Drop table if exists for clean import
    c.execute(f'DROP TABLE IF EXISTS {TABLE_NAME}')
    # Create table with columns from CSV
    c.execute(f'''
        CREATE TABLE {TABLE_NAME} (
            [Location Code] TEXT,
            [Real Property Asset Name] TEXT,
            [Installation Name] TEXT,
            [Owned or Leased] TEXT,
            [GSA Region] TEXT,
            [Street Address] TEXT,
            [City] TEXT,
            [State] TEXT,
            [Zip Code] TEXT,
            [Latitude] REAL,
            [Longitude] REAL,
            [Building Rentable Square Feet] REAL,
            [Available Square Feet] REAL,
            [Construction Date] TEXT,
            [Congressional District] TEXT,
            [Congressional District Representative Name] TEXT,
            [Building Status] TEXT,
            [Real Property Asset Type] TEXT
        )
    ''')
    # Import data from CSV
    with open(CSV_PATH, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = [tuple(row[col] for col in reader.fieldnames) for row in reader]
        placeholders = ','.join(['?'] * len(reader.fieldnames))
        c.executemany(f'INSERT INTO {TABLE_NAME} VALUES ({placeholders})', rows)
    conn.commit()
    conn.close()

format_and_import_db()

@app.route('/query', methods=['POST'])
def query():
    zipcode = request.form.get('zipcode', '').strip()
    state = request.form.get('state', '').strip()
    result = ''
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        sql = """
            SELECT [Real Property Asset Name], [Street Address], [City], [State], [Zip Code], [Available Square Feet], [Construction Date]
            FROM buildings
            WHERE [Zip Code] LIKE ?
        """
        params = [f'%{zipcode}%']
        if state:
            sql += " AND [State] = ?"
            params.append(state)
        sql += " ORDER BY [Construction Date] ASC"
        c.execute(sql, params)
        rows = c.fetchall()
        if rows:
            # Add View on Map button above the table
            result = f'<a href="/map.html?zipcode={zipcode}&state={state}" class="btn" style="margin-bottom:16px;display:inline-block;">View on Map</a>'
            result += '<table border="1"><tr>'
            result += '<th>Asset Name</th><th>Street Address</th><th>City</th><th>State</th><th>Zip Code</th><th>Available Sq Ft</th><th>Construction Date</th></tr>'
            for row in rows:
                available = row[5]
                highlight = ' style="background:#e6ffed;font-weight:bold;"' if available and float(available) > 0 else ''
                result += f'<tr{highlight}>' + ''.join(f'<td>{cell}</td>' for cell in row) + '</tr>'
            result += '</table>'
        else:
            result = 'No buildings found for that zip code and state.'
        conn.close()
    except Exception as e:
        result = f'Error: {e}'
    return render_template('index.html', result=result)

# Serve map.html and optionally accept zipcode as a query parameter
@app.route('/map.html')
def map_page():
    zipcode = request.args.get('zipcode', '')
    return send_from_directory('.', 'map.html')

if __name__ == '__main__':
    app.run(debug=True)