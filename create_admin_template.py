template_admin = r'''{% extends "base.html" %}
{% block title %}Jersey Orders Admin Dashboard{% endblock %}
{% block content %}
<style>
:root {
    --primary: #2563eb;
    --primary-dark: #1e40af;
    --secondary: #10b981;
    --danger: #ef4444;
}

.admin-dashboard {
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    min-height: 100vh;
    padding: 2rem;
}

.header-section {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    color: white;
    padding: 3rem 2rem;
    border-radius: 20px;
    margin-bottom: 2rem;
}

.header-section h1 {
    font-size: 2rem;
    font-weight: 800;
    margin: 0;
}

.header-section p {
    margin: 0.5rem 0 0 0;
    opacity: 0.9;
}

.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
}

.metric-card {
    background: white;
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.metric-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748b;
    font-weight: 700;
    margin-bottom: 0.5rem;
}

.metric-value {
    font-size: 2rem;
    font-weight: 800;
    color: var(--primary);
}

.card {
    background: white;
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    margin-bottom: 1.5rem;
}

.card h2 {
    margin: 0 0 1rem 0;
    font-size: 1.25rem;
    font-weight: 700;
    color: #1e293b;
}

.alert {
    background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
    border: 2px solid #fcd34d;
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 1.5rem;
    color: #78350f;
}

.alert h4 {
    margin: 0 0 0.5rem 0;
    font-weight: 700;
}

.alert p {
    margin: 0.25rem 0;
    font-size: 0.9rem;
}

.btn {
    display: inline-block;
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    border: none;
    font-weight: 700;
    text-decoration: none;
    cursor: pointer;
    transition: all 0.3s ease;
}

.btn-primary {
    background: linear-gradient(135deg, var(--primary), var(--primary-dark));
    color: white;
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(37, 99, 235, 0.3);
}

.btn-secondary {
    background: white;
    color: var(--primary);
    border: 2px solid var(--primary);
}

.btn-secondary:hover {
    background: #f0f9ff;
}

.tabs {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
    border-bottom: 2px solid #e2e8f0;
}

.tab-btn {
    padding: 1rem 1.5rem;
    border: none;
    background: transparent;
    font-weight: 700;
    color: #94a3b8;
    cursor: pointer;
    border-bottom: 3px solid transparent;
    transition: all 0.3s ease;
}

.tab-btn.active {
    color: var(--primary);
    border-bottom-color: var(--primary);
}

.tab-content {
    display: none;
}

.tab-content.active {
    display: block;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th {
    background: #f8fafc;
    padding: 1rem;
    text-align: left;
    font-weight: 700;
    font-size: 0.85rem;
    text-transform: uppercase;
    border-bottom: 2px solid #e2e8f0;
    color: #475569;
}

td {
    padding: 1rem;
    border-bottom: 1px solid #e2e8f0;
}

tbody tr:hover {
    background: #f8fafc;
}

.badge {
    display: inline-block;
    padding: 0.3rem 0.7rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    background: linear-gradient(135deg, #e0f2fe, #bae6fd);
    color: #0c4a6e;
}

.form-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-bottom: 1rem;
}

.form-group {
    display: flex;
    flex-direction: column;
}

.form-label {
    font-weight: 700;
    margin-bottom: 0.5rem;
    color: #1e293b;
}

.form-input {
    padding: 0.75rem;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    font-size: 0.95rem;
}

.form-input:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.summary-total {
    background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
    border: 2px solid var(--primary);
    border-radius: 12px;
    padding: 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: 700;
}

.summary-total-value {
    font-size: 1.8rem;
    color: var(--primary);
}

@media (max-width: 768px) {
    .metrics-grid {
        grid-template-columns: 1fr;
    }
    
    .header-section {
        padding: 1.5rem;
    }
}
</style>

<div class="admin-dashboard">
    <div class="header-section">
        <h1>📊 Jersey Orders Admin</h1>
        <p>Review and manage all jersey orders before sending to supplier</p>
    </div>

    <div style="display: flex; gap: 1rem; margin-bottom: 2rem;">
        <a href="{% url 'jersey-orders' %}" class="btn btn-secondary">← Back to Member Form</a>
        <a href="{% url 'jersey-orders-export' %}" class="btn btn-primary">📥 Download Order Data</a>
    </div>

    <div class="alert">
        <h4>💡 Important Info</h4>
        <p><strong>Prices in Indian Rupees (₹)</strong> - Excludes postal/courier charges</p>
        <p style="margin-top: 0.5rem;">Add postage separately when final shipment cost is known.</p>
        <p style="margin-top: 0.5rem;"><strong>Order Status:</strong> {{ ordering_status }}</p>
        {% if ordering_deadline %}<p style="margin-top: 0.5rem;"><strong>Close Date:</strong> {{ ordering_deadline }}</p>{% endif %}
    </div>

    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-label">Total Items</div>
            <div class="metric-value">{{ total_quantity }}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Members</div>
            <div class="metric-value">{{ orders|length }}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Grand Total</div>
            <div class="metric-value">₹{{ grand_total }}</div>
        </div>
    </div>

    <div class="card">
        <h2>📋 Order Summary by Item Type</h2>
        <div style="overflow-x: auto;">
            <table>
                <thead>
                    <tr>
                        <th>Item</th>
                        <th>Size</th>
                        <th>Gender</th>
                        <th>Quantity</th>
                        <th>Rate (₹)</th>
                        <th>Total (₹)</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item_type, rows in summary.items %}
                        {% for row in rows %}
                        <tr>
                            <td><strong>{{ row.display_item }}</strong></td>
                            <td>{{ row.size }}</td>
                            <td><span class="badge">{{ row.gender }}</span></td>
                            <td style="text-align: center; font-weight: 700;">{{ row.quantity }}</td>
                            <td style="text-align: right;">{{ row.rate }}</td>
                            <td style="text-align: right; font-weight: 700; color: var(--primary);">{{ row.total }}</td>
                        </tr>
                        {% endfor %}
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <div class="summary-total">
        <div>Grand Total Amount</div>
        <div class="summary-total-value">₹{{ grand_total }}</div>
    </div>

    <div class="card" style="margin-top: 2rem;">
        <h2>👥 Members ({{ orders|length }})</h2>
        <div style="overflow-x: auto;">
            <table>
                <thead>
                    <tr>
                        <th>Member</th>
                        <th>Wearer</th>
                        <th>Items</th>
                        <th>Total (₹)</th>
                    </tr>
                </thead>
                <tbody>
                    {% for order in orders %}
                    <tr>
                        <td><strong>{{ order.user.username }}</strong></td>
                        <td>{{ order.wearer_name }}</td>
                        <td style="text-align: center;">{{ order.item_count }}</td>
                        <td style="text-align: right;">{{ order.member_total }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<script>
function switchTab(btn, index) {
    const parent = btn.parentElement.parentElement;
    parent.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    parent.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    parent.querySelectorAll('.tab-content')[index].classList.add('active');
}
</script>
{% endblock %}'''

with open('apps/jerseys/templates/jerseys/admin_summary.html', 'w', encoding='utf-8') as f:
    f.write(template_admin)
print('✓ Admin summary template created successfully')
