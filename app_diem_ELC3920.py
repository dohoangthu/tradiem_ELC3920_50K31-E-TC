import re
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd
import streamlit as st

# 1. Configuration
FILE_PATH = '271_ELC3920_ELC3920_50K31-E-TC.xlsx'   # Excel file name (must match the file name on GitHub exactly)
LECTURER = 'Đỗ Hoàng Thu'

st.set_page_config(page_title='Grade Lookup ELC3920', page_icon='🎓')


# 2. Load the Excel file
@st.cache_data
def load_data(path):
    df = pd.read_excel(path)
    df.columns = [' '.join(str(c).split()) for c in df.columns]   # remove line breaks / extra spaces
    return df


try:
    df = load_data(FILE_PATH)
except FileNotFoundError:
    st.error(f"Error: File '{FILE_PATH}' not found. Please check the file name on GitHub.")
    st.stop()
except Exception as e:
    st.error(f'Error reading the Excel file: {e}')
    st.stop()

# 3. Detect columns
#    First 3 columns: ClassID | UID (student ID) | FullName.
#    All other columns are shown in the same order and with the same names as in Excel.
#    Columns whose name starts with "Component" (Component 1, Component 2...) are the overall scores:
#    they are shown in bold with 1 decimal place.
COL_CLASS, COL_ID, COL_NAME = df.columns[0], df.columns[1], df.columns[2]
df[COL_ID] = df[COL_ID].astype(str).str.strip()

SCORE_COLS = list(df.columns[3:])


def is_overall(col):
    return col.lower().startswith('component')


# 4. Formatting helpers
def fmt(v):
    if pd.isna(v):
        return '-'                      # empty cell (e.g. no bonus points)
    v = round(float(v), 3)
    return str(int(v)) if v.is_integer() else str(v)


def fmt_overall(v):
    """Component 1, 2: always 1 decimal place, rounded half up (same as Excel)."""
    if pd.isna(v):
        return '-'
    d = Decimal(str(round(float(v), 6))).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
    return str(d)


def clean_label(label):
    label = re.sub(r'(\d),(\d)', r'\1.\2', label)   # 12,5% -> 12.5%
    return label.replace('*', '×')                  # avoid '*' being read as text formatting


# 5. Lookup
def lookup_scores(id_input):
    id_input = str(id_input).strip()
    result = df[df[COL_ID] == id_input]
    if result.empty:
        return None
    row = result.iloc[0]
    scores = [
        (c, fmt_overall(row[c]) if is_overall(c) else fmt(row[c]), is_overall(c))
        for c in SCORE_COLS
    ]
    return {'Name': row[COL_NAME], 'Class': row[COL_CLASS], 'Scores': scores}


# 6. User interface
st.title('🤖 Grade Lookup ELC3920')
st.markdown('---')

st.header('Enter your Student ID')
id_input = st.text_input('Your Student ID:', placeholder='Example: 241123098101')

if st.button('Look Up Grades', type='primary'):
    if id_input:
        with st.spinner('Searching...'):
            data = lookup_scores(id_input)

        if data:
            st.success(f'✅ Found: **{data["Name"]}** - Class **{data["Class"]}**')
            st.subheader('Grade Details')

            # Grade table, with the Component rows in bold
            lines = ['| Component | Score |', '|:--|:--:|']
            for label, value, is_bold in data['Scores']:
                label = clean_label(label)
                if is_bold:
                    lines.append(f'| **{label}** | **{value}** |')
                else:
                    lines.append(f'| {label} | {value} |')
            st.markdown('\n'.join(lines))
        else:
            st.error(f'❌ No data found for Student ID: **{id_input}**.')
    else:
        st.warning('⚠️ Please enter your Student ID.')

st.markdown('---')
st.caption(f'Lecturer: {LECTURER}')