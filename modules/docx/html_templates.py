"""
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
"""

# html_templates.py
# Contains the HTML/JS/CSS templates for generating reports.


def get_html_template(rows, timestamp):
    """
    Returns the complete HTML string for the report.
    Includes:
    - CSS for styling (red/green highlights).
    - JavaScript for LocalStorage (saving comments in browser).
    - JavaScript for CSV Export.
    """
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>DOCX Comparison Report</title>
        <style>
            /* --- CSS Styles --- */
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background: #f4f4f9; }}
            h1 {{ color: #333; margin-bottom: 5px; }}
            .timestamp {{ color: #666; font-size: 0.9em; margin-bottom: 20px; }}
            table {{ width: 100%; border-collapse: collapse; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.2); }}
            th, td {{ border: 1px solid #ddd; padding: 12px; vertical-align: top; text-align: left; }}
            th {{ background-color: #007bff; color: white; position: sticky; top: 0; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            tr.reviewed {{ background-color: #e8f5e9; }}
            
            /* Visual Diff Colors */
            .del {{ color: #d9534f; text-decoration: line-through; background-color: #fdf7f7; }}
            .ins {{ color: #28a745; text-decoration: underline; background-color: #f0fff4; }}
            
            textarea {{ width: 100%; height: 60px; border: 1px solid #ccc; border-radius: 4px; padding: 5px; }}
            .meta {{ font-size: 0.85em; color: #666; width: 100px; word-break: break-all; }}
            .content {{ min-width: 250px; }}
            .status-cell {{ text-align: center; width: 50px; }}
        </style>
        <script>
            /* --- JavaScript Logic --- */
            document.addEventListener('DOMContentLoaded', () => {{ loadState(); }});
            const STORAGE_KEY = 'docx_review_v1';
            
            // Load saved comments/checks from Browser LocalStorage
            function loadState() {{
                const data = JSON.parse(localStorage.getItem(STORAGE_KEY)) || {{}};
                document.querySelectorAll('tr[data-id]').forEach(row => {{
                    const id = row.getAttribute('data-id');
                    if (data[id]) {{
                        if (data[id].checked) {{
                            row.querySelector('input').checked = true;
                            row.classList.add('reviewed');
                        }}
                        if (data[id].comment) row.querySelector('textarea').value = data[id].comment;
                    }}
                }});
            }}
            
            // Save state to LocalStorage
            function saveData(id, key, value) {{
                const data = JSON.parse(localStorage.getItem(STORAGE_KEY)) || {{}};
                if (!data[id]) data[id] = {{}};
                data[id][key] = value;
                localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
            }}
            
            // Handle Checkbox clicks
            function updateStatus(cb) {{
                const row = cb.closest('tr');
                const id = row.getAttribute('data-id');
                row.classList.toggle('reviewed', cb.checked);
                saveData(id, 'checked', cb.checked);
            }}
            
            // Handle Comment typing
            function updateComment(ta) {{
                const row = ta.closest('tr');
                const id = row.getAttribute('data-id');
                saveData(id, 'comment', ta.value);
            }}
            
            // Export data to CSV
            function exportToCSV() {{
                const rows = document.querySelectorAll('tr[data-id]');
                const now = new Date();
                // Format timestamp for filename
                const year = now.getFullYear();
                const month = String(now.getMonth() + 1).padStart(2, '0');
                const day = String(now.getDate()).padStart(2, '0');
                const hour = String(now.getHours()).padStart(2, '0');
                const min = String(now.getMinutes()).padStart(2, '0');
                const timeStr = `${{year}}-${{month}}-${{day}}_${{hour}}-${{min}}`;

                // BOM + Header Row
                let csv = "\\uFEFF" + '"ID","File","Status","Original Text","Edited Text","Comments"\\n';
                
                rows.forEach(row => {{
                    const idVal = row.children[1].innerText.replace(/"/g, '""');
                    const f = row.querySelector('.meta').innerText.replace(/"/g, '""');
                    const o = row.children[3].innerText.replace(/"/g, '""'); 
                    const e = row.children[4].innerText.replace(/"/g, '""');   
                    const s = row.querySelector('input').checked ? "Reviewed" : "Pending";
                    const c = row.querySelector('textarea').value.replace(/"/g, '""');
                    csv += `"${{idVal}}","${{f}}","${{s}}","${{o}}","${{e}}","${{c}}"\\n`;
                }});

                const blob = new Blob([csv], {{ type: 'text/csv;charset=utf-8;' }});
                const link = document.createElement("a");
                link.href = URL.createObjectURL(blob);
                link.download = `docx_review_export_${{timeStr}}.csv`;
                link.click();
            }}
        </script>
    </head>
    <body>
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1>DOCX Tracked Changes Report</h1>
                <div class="timestamp">Generated on: {timestamp}</div>
            </div>
            <button onclick="exportToCSV()" style="padding: 10px 20px; background-color: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer;">Export to Excel (CSV)</button>
        </div>
        <p>This report extracts internal tracked changes found within DOCX files containing tracked changes.</p>
        <p>Clicking the checkboxes below changes the review status from "Pending" to "Reviewed" in the Exported CSV file.</p>
        <p><strong>Important:</strong> Your comments and checkboxes are stored temporarily in your browser.</p>
        <p><strong>To Save:</strong> You must click <strong>Export to Excel</strong> to save your work permanently. This saves a CSV to your <strong>Downloads</strong> folder unless user settings vary.</p>
        <table>
            <thead>
                <tr><th>Done</th><th>ID</th><th>File</th><th>Original Text</th><th>Edited Text</th><th>Visual Diff</th><th>Comments</th></tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
    </body>
    </html>
    '''