import sqlite3
from pathlib import Path
from datetime import date
import pandas as pd
import streamlit as st

st.set_page_config(page_title='One Faculty | One Quality Ecosystem',page_icon='🎓',layout='wide')
BASE=Path(__file__).resolve().parent
DB=BASE/'quality_demo.db'
DEPTS=['Intelligent Informatics (II)','Business Intelligence, Humanities & Governance (BIHG)','Computational Artificial Intelligence (CAI)','Software Engineering & Advanced Technology (SEAT)']
AREAS={1:'Programme Development and Delivery',2:'Assessment of Student Learning',3:'Student Selection and Support Services',4:'Academic Staff',5:'Educational Resources',6:'Programme Management',7:'Programme Monitoring, Review and CQI'}
STAGES=['Provisional Accreditation','Programme Delivery / CQI','Full Accreditation','Compliance Evaluation','Curriculum Review']

def con():
    cx=sqlite3.connect(DB,check_same_thread=False)
    cx.row_factory=sqlite3.Row
    cx.execute('PRAGMA foreign_keys=ON')
    return cx

def setup():
    with con() as cx:
        cx.executescript('''
        CREATE TABLE IF NOT EXISTS programmes(id INTEGER PRIMARY KEY, code TEXT UNIQUE, department TEXT NOT NULL, stage TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS evidence(id INTEGER PRIMARY KEY, title TEXT NOT NULL, area INTEGER NOT NULL, scope TEXT NOT NULL, owner TEXT NOT NULL, status TEXT NOT NULL, version TEXT, link TEXT, updated TEXT);
        CREATE TABLE IF NOT EXISTS mappings(programme_id INTEGER, evidence_id INTEGER, PRIMARY KEY(programme_id,evidence_id), FOREIGN KEY(programme_id) REFERENCES programmes(id), FOREIGN KEY(evidence_id) REFERENCES evidence(id));
        CREATE TABLE IF NOT EXISTS requests(id INTEGER PRIMARY KEY, programme_id INTEGER, title TEXT, assigned_to TEXT, status TEXT, created TEXT, FOREIGN KEY(programme_id) REFERENCES programmes(id));
        ''')
        if cx.execute('SELECT COUNT(*) FROM programmes').fetchone()[0]==0:
            # Programme identifiers are placeholders, not official UTM programme names.
            distribution=[5,5,4,3]
            i=0
            for d,n in zip(DEPTS,distribution):
                for _ in range(n):
                    i+=1
                    cx.execute('INSERT INTO programmes(code,department,stage) VALUES(?,?,?)',(f'DEMO-P{i:02}',d,STAGES[(i-1)%len(STAGES)]))
            examples=[
            ('University mission and educational goals',1,'Faculty-wide','Faculty QA Team','Approved','1.0'),
            ('Academic staff development policy',4,'Faculty-wide','Faculty HR','Approved','2.0'),
            ('Academic assessment regulations',2,'Faculty-wide','Academic Office','Approved','1.1'),
            ('Laboratory and digital resource inventory',5,'Department','Department Coordinator','Under Review','0.9'),
            ('Programme PEO–PLO mapping',1,'Programme-specific','Programme Coordinator','Draft','0.5'),
            ('Programme CQI report',7,'Programme-specific','Programme QA Coordinator','Approved','1.0')]
            for x in examples:
                cx.execute('INSERT INTO evidence(title,area,scope,owner,status,version,updated) VALUES(?,?,?,?,?,?,?)',(*x,str(date.today())))
            for pid in range(1,18):
                for eid in ([1,2,3] if pid%2 else [1,2,3,4,5]):
                    cx.execute('INSERT INTO mappings(programme_id,evidence_id) VALUES(?,?)',(pid,eid))
            cx.execute('INSERT INTO requests(programme_id,title,assigned_to,status,created) VALUES(?,?,?,?,?)',(1,'Update programme-specific PEO–PLO mapping','Programme Coordinator','Open',str(date.today())))

def df(query,params=()):
    with con() as cx: return pd.read_sql_query(query,cx,params=params)

def execute(query,params=()):
    with con() as cx: cx.execute(query,params)

setup()
st.markdown('''<style>
.block-container{padding-top:1.7rem;padding-bottom:2rem;max-width:1500px}
h1,h2,h3{color:#14334c} div[data-testid="stMetric"]{border:1px solid #d6e2ed;background:#f3f7fb;border-radius:12px;padding:13px}
.small-note{color:#6d7782;font-size:.86rem}
</style>''',unsafe_allow_html=True)
st.title('One Faculty, One Quality Ecosystem')
st.caption('EDLP Digital Transformation Proof of Concept | Faculty of Artificial Intelligence, UTM')
st.info('**DEMONSTRATION ONLY:** The 4 departments and 17-programme scope is user supplied. Programme codes, evidence records, readiness values and requests are synthetic. No live UTM data is connected.')

pages=['Executive Dashboard','Programme Portfolio','Evidence Register','Evidence Mapping & Reuse','Request Workflow','Pilot Measurement']
page=st.sidebar.radio('Navigate',pages)
st.sidebar.markdown('---')
st.sidebar.caption('CoPPA 2nd Edition · 7 evaluation areas. Readiness is a demo coverage indicator, **not an MQA compliance decision**.')

p=df('SELECT * FROM programmes ORDER BY id')
e=df('SELECT * FROM evidence ORDER BY id')
m=df('SELECT * FROM mappings')
r=df('SELECT * FROM requests')

if page=='Executive Dashboard':
    st.subheader('Faculty-wide overview')
    k1,k2,k3,k4=st.columns(4)
    k1.metric('Departments',len(DEPTS));k2.metric('Academic programmes',len(p));k3.metric('Registered evidence',len(e));k4.metric('Evidence reuse links',len(m))
    left,right=st.columns([1,1])
    with left:
        st.markdown('#### Programmes by department')
        counts=p.groupby('department').size().rename('Programmes')
        st.bar_chart(counts)
    with right:
        st.markdown('#### Evidence by review status')
        st.bar_chart(e.groupby('status').size().rename('Evidence'))
    st.markdown('#### Evidence coverage by programme (illustrative proxy)')
    # denominator is demonstration-only seven Areas, NOT full 98 CoPPA standards.
    coverage=df('''SELECT p.code, p.department, COUNT(DISTINCT e.area) AS areas_with_mapped_evidence
                   FROM programmes p LEFT JOIN mappings m ON p.id=m.programme_id
                   LEFT JOIN evidence e ON e.id=m.evidence_id AND e.status='Approved'
                   GROUP BY p.id ORDER BY p.id''')
    coverage['Demo area coverage (%)']=(coverage['areas_with_mapped_evidence']/7*100).round(1)
    st.dataframe(coverage[['code','department','areas_with_mapped_evidence','Demo area coverage (%)']],hide_index=True,use_container_width=True)
    st.caption('Coverage calculation = number of CoPPA Areas having at least one mapped approved evidence item ÷ 7. This does not establish compliance with individual CoPPA standards.')

elif page=='Programme Portfolio':
    st.subheader('4 departments · 17 programmes')
    d=st.selectbox('Filter department',['All']+DEPTS)
    view=p if d=='All' else p[p.department==d]
    st.dataframe(view.rename(columns={'code':'Programme (demo code)','department':'Department','stage':'Current exercise'}).drop(columns=['id']),hide_index=True,use_container_width=True)
    with st.expander('Update programme stage'):
        code=st.selectbox('Programme',p.code)
        old=p.loc[p.code==code,'stage'].iloc[0]
        new=st.selectbox('Accreditation / QA exercise',STAGES,index=STAGES.index(old))
        if st.button('Save programme stage'):
            execute('UPDATE programmes SET stage=? WHERE code=?',(new,code));st.rerun()
    st.caption('The distribution of 17 sample programmes by department and their stages must be replaced by verified FAI records.')

elif page=='Evidence Register':
    st.subheader('Register, review and version evidence once')
    st.dataframe(e[['id','title','area','scope','owner','status','version','updated','link']].rename(columns={'area':'CoPPA Area'}),hide_index=True,use_container_width=True)
    with st.expander('➕ Add new evidence',expanded=False):
        with st.form('new_evidence'):
            title=st.text_input('Evidence title')
            area=st.selectbox('CoPPA evaluation area',list(AREAS),format_func=lambda n:f'Area {n}: {AREAS[n]}')
            scope=st.selectbox('Reuse scope',['Faculty-wide','Department','Programme-specific'])
            owner=st.text_input('Evidence owner')
            status=st.selectbox('Review status',['Draft','Under Review','Approved'])
            version=st.text_input('Version',value='1.0')
            link=st.text_input('Existing secure document link (optional; no file is uploaded)')
            if st.form_submit_button('Create evidence'):
                if title.strip() and owner.strip():
                    execute('INSERT INTO evidence(title,area,scope,owner,status,version,link,updated) VALUES(?,?,?,?,?,?,?,?)',(title,area,scope,owner,status,version,link,str(date.today())))
                    st.success('Evidence registered');st.rerun()
                else: st.error('Evidence title and owner are required.')
    with st.expander('✅ Update evidence review status'):
        eid=st.selectbox('Evidence',e.id.tolist(),format_func=lambda n:f'#{n} – {e.set_index("id").loc[n,"title"]}')
        status=st.selectbox('New status',['Draft','Under Review','Approved'],key='review')
        version=st.text_input('Updated version',value=str(e.set_index('id').loc[eid,'version']))
        if st.button('Save review'):
            execute('UPDATE evidence SET status=?,version=?,updated=? WHERE id=?',(status,version,str(date.today()),int(eid)));st.rerun()

elif page=='Evidence Mapping & Reuse':
    st.subheader('One approved evidence item → multiple programme requirements')
    st.caption('Mappings represent candidate evidence references. Human review remains necessary to check relevance, scope and current validity.')
    ec=st.selectbox('Evidence item',e.id.tolist(),format_func=lambda n:f'#{n} | {e.set_index("id").loc[n,"title"]} ({e.set_index("id").loc[n,"status"]})')
    registered=m[m.evidence_id==ec].programme_id.tolist()
    selection=st.multiselect('Mapped programmes',p.id.tolist(),default=registered,format_func=lambda n:f'{p.set_index("id").loc[n,"code"]} · {p.set_index("id").loc[n,"department"].split(" (")[0]}')
    if st.button('Save programme mappings',type='primary'):
        with con() as cx:
            cx.execute('DELETE FROM mappings WHERE evidence_id=?',(int(ec),))
            cx.executemany('INSERT INTO mappings(programme_id,evidence_id) VALUES(?,?)',[(int(pid),int(ec)) for pid in selection])
        st.success('Programme mappings updated');st.rerun()
    st.markdown('#### Reuse report')
    reuse=df('''SELECT e.title,e.status,e.scope,COUNT(m.programme_id) AS programme_links
    FROM evidence e LEFT JOIN mappings m ON m.evidence_id=e.id GROUP BY e.id ORDER BY programme_links DESC''')
    st.dataframe(reuse,hide_index=True,use_container_width=True)
    st.metric('Repeated-document requests avoided (potential, not measured)', 'Not yet measured')

elif page=='Request Workflow':
    st.subheader('Evidence requests and ownership')
    requests=df('''SELECT r.id,p.code AS programme,r.title,r.assigned_to,r.status,r.created
    FROM requests r LEFT JOIN programmes p ON p.id=r.programme_id ORDER BY r.id DESC''')
    st.dataframe(requests,hide_index=True,use_container_width=True)
    with st.form('request'):
        st.markdown('#### Request missing evidence')
        program=st.selectbox('Programme',p.id.tolist(),format_func=lambda n:p.set_index('id').loc[n,'code'])
        title=st.text_input('Requirement / evidence needed')
        assignee=st.text_input('Assigned owner')
        if st.form_submit_button('Create request'):
            if title.strip() and assignee.strip():
                execute('INSERT INTO requests(programme_id,title,assigned_to,status,created) VALUES(?,?,?,?,?)',(int(program),title,assignee,'Open',str(date.today())))
                st.success('Request created');st.rerun()
            else:st.error('Provide a requirement and owner.')
    if len(r):
        with st.expander('Update a request'):
            reqid=st.selectbox('Request ID',r.id.tolist())
            status=st.selectbox('Status',['Open','In Progress','Resolved'])
            if st.button('Update request'):
                execute('UPDATE requests SET status=? WHERE id=?',(status,int(reqid)));st.rerun()

elif page=='Pilot Measurement':
    st.subheader('EDLP six-month pilot: measurement framework')
    st.caption('Targets are proposed—not confirmed UTM findings.')
    goals=pd.DataFrame([
      {'KPI':'Preparation time per exercise','Baseline':'Record hours during Month 1','Target':'40% reduction','How to measure':'Time logs: preparation hours per comparable audit exercise'},
      {'KPI':'Duplicate requests','Baseline':'Count repeated requests in Month 1','Target':'50% reduction','How to measure':'Request register: same evidence item requested more than once'},
      {'KPI':'Evidence completeness','Baseline':'Assess approved evidence at agreed cutoff','Target':'90% complete','How to measure':'Approved requirements satisfied / applicable requirements'},
      {'KPI':'Workflow adoption','Baseline':'Track invited pilot users','Target':'80% adoption','How to measure':'Active users completing assigned workflow / invited pilot users'},
    ])
    st.dataframe(goals,hide_index=True,use_container_width=True)
    st.markdown('#### Simple baseline-to-result calculator')
    a,b=st.columns(2)
    with a: before=st.number_input('Baseline preparation hours',min_value=0.0,value=100.0,step=5.0)
    with b: after=st.number_input('Post-pilot preparation hours',min_value=0.0,value=60.0,step=5.0)
    if before>0:
        reduction=(before-after)/before*100
        st.metric('Observed change based on entered values',f'{reduction:.1f}%')
    else: st.warning('Baseline hours must be greater than zero.')
    st.caption('Calculator input is illustrative until validated audit workload data is entered.')

st.divider()
st.caption('Prototype v1.0 · Local SQLite demo · Not an accreditation assessment system · Use synthetic data only in Google Colab.')
