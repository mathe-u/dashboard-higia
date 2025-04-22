def render_row(row):
    return f"""
<tr>
    <td style="text-align: left; padding: 8px;">{row['doctor']}</td>
    <td style="text-align: left; padding: 8px;">{row['patient']}</td>
    <td style="text-align: center; padding: 8px;">{row['date']}</td>
    <td style="text-align: center; padding: 8px;">{row['description']}</td>
    <td style="text-align: center; padding: 8px; color: {row['color']}; font-weight: bold;">{row['status']}</td>
</tr>
"""

status_colors = {
    'CD': '#48c78e',
    'CL': '#ffcc00',
    'OP': '#1e90ff',
    'RW': '#ffa07a',
    'TY': '#8a2be2',
    'TO': '#ff6347',
}

def render_table(df):
    table_html = f"""
    <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
        <thead>
            <tr style="background-color: #f5f5f5; border-bottom: 1px solid #ddd;">
                <th style="text-align: left; padding: 8px;">Doctor</th>
                <th style="text-align: left; padding: 8px;">Patient</th>
                <th style="text-align: center; padding: 8px;">Date</th>
                <th style="text-align: center; padding: 8px;">Description</th>
                <th style="text-align: center; padding: 8px;">Status</th>
            </tr>
        </thead>
        <tbody>
            {''.join(df.apply(render_row, axis=1))}
        </tbody>
    </table>
    """
    return table_html

