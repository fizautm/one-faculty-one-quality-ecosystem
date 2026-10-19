# One Faculty, One Quality Ecosystem — New prototype

Working Streamlit demonstration for EDLP: 4 departments, 17 synthetic programme records, CoPPA evidence register, mapping and reuse, requests, dashboard and pilot metrics.

**Data caution:** all programme identifiers, status, documents and readiness figures are fabricated demonstration records. The four-department/17-programme scope is user-supplied. Never upload personal, confidential or restricted UTM audit evidence to a temporary Colab demo.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Run in Colab

Upload `app.py`, `requirements.txt`, and `.streamlit/config.toml` (optional) to `/content/`, then run notebook code:

```python
%cd /content
!pip -q install -r requirements.txt
!streamlit run /content/app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true --server.enableWebsocketCompression=false > /content/streamlit.log 2>&1 &
```

Next cell:

```python
import time
from google.colab import output
time.sleep(3)
print(output.eval_js('google.colab.kernel.proxyPort(8501)'))
```

If Colab proxy stays blank, check `!tail -n 80 /content/streamlit.log` and `!curl http://127.0.0.1:8501/_stcore/health`. A healthy server plus blank proxy indicates likely session/browser websocket connectivity; local execution or Streamlit Community Cloud is more reliable for presentation.

Database `quality_demo.db` is auto-generated when first opened. Delete it to reset all demo data.
