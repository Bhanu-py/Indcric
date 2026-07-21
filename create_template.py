template = r'''{% extends "base.html" %}
{% block title %}Jersey Store - Premium Team Kits{% endblock %}
{% block content %}
<style>
:root {
    --primary: #2563eb;
    --primary-dark: #1e40af;
    --danger: #ef4444;
    --warning: #f59e0b;
}

.hero-banner {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 3rem 2rem;
    border-radius: 20px;
    margin-bottom: 3rem;
    position: relative;
    overflow: hidden;
}

.product-showcase {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 1.5rem;
    margin-bottom: 3rem;
}

.product-card {
    background: white;
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    transition: all 0.3s ease;
}

.product-card:hover {
    transform: translateY(-8px);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
}

.order-form {
    background: white;
    border-radius: 16px;
    padding: 2rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    margin-bottom: 2rem;
}

.info-section {
    background: white;
    border-radius: 16px;
    padding: 2rem;
    margin-bottom: 2rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.grid-layout {
    display: grid;
    grid-template-columns: 1fr 380px;
    gap: 2rem;
}

@media (max-width: 1024px) {
    .grid-layout { grid-template-columns: 1fr; }
    .sidebar { order: -1; }
}

.sidebar {
    position: sticky;
    top: 2rem;
    height: fit-content;
}

.order-summary {
    background: white;
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    margin-bottom: 1.5rem;
}

.alert {
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 1.5rem;
    font-size: 0.95rem;
}

.alert-warning {
    background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
    border: 2px solid #fcd34d;
    color: #78350f;
}

.alert h4 { margin: 0 0 0.5rem 0; font-weight: 700; }
.alert p { margin: 0; line-height: 1.6; }

.btn-primary {
    background: linear-gradient(135deg, var(--primary), var(--primary-dark));
    color: white;
    width: 100%;
    padding: 1rem;
    font-size: 1rem;
    border: none;
    border-radius: 8px;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.3s ease;
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 30px rgba(37, 99, 235, 0.3);
}

.btn-danger {
    background: var(--danger);
    color: white;
    font-size: 0.85rem;
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 700;
}

.btn-danger:hover { background: #dc2626; }

.form-label { font-weight: 700; margin-bottom: 0.5rem; display: block; }
.form-group { margin-bottom: 1rem; }

.badge {
    display: inline-block;
    padding: 0.4rem 0.8rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
}

.badge-status {
    background: linear-gradient(135deg, #10b981, #059669);
    color: white;
}

.badge-closed {
    background: var(--danger);
    color: white;
}

.info-card {
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
}

.info-card h3 {
    font-size: 0.85rem;
    font-weight: 700;
    text-transform: uppercase;
    margin: 0 0 0.5rem 0;
    color: #475569;
}

.info-card p {
    font-size: 0.875rem;
    color: #64748b;
    line-height: 1.6;
    margin: 0;
}

@media (max-width: 768px) {
    .hero-banner h1 { font-size: 1.8rem; }
    .product-showcase { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); }
}
</style>

<div class="page-content">
    <div class="hero-banner">
        <h1>🏏 Jersey Store</h1>
        <p>Premium team kits for players and supporters</p>
        {% if request.user.is_staff %}
        <a href="{% url 'jersey-orders-admin' %}" style="display: inline-block; margin-top: 1rem; background: white; color: #667eea; padding: 0.75rem 1.5rem; border-radius: 8px; font-weight: 700; text-decoration: none;">📊 Admin Dashboard</a>
        {% endif %}
    </div>

    {% if not ordering_open %}
    <div class="alert alert-warning">
        <h4>⚠️ Jersey Ordering Closed</h4>
        <p>Ordering is currently closed. You can review your submitted order, but new orders cannot be placed.</p>
    </div>
    {% endif %}

    <div class="alert alert-warning">
        <h4>📍 Important Information</h4>
        <p><strong>Prices in Indian Rupees (₹)</strong> • Excludes shipping charges • Family & kids can reuse jersey numbers • Jersey numbers are for reference only, not reserved</p>
    </div>

    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-bottom: 3rem;">
        <div class="info-card">
            <h3>📏 How to Choose Size</h3>
            <p>Compare garment measurements from our charts with a shirt that fits you well.</p>
        </div>
        <div class="info-card">
            <h3>👶 Kids Size</h3>
            <p>Measure a well-fitting item your child owns and enter exact measurements.</p>
        </div>
        <div class="info-card">
            <h3>✅ After Ordering</h3>
            <p>Review your order and admin will process all orders in batches.</p>
        </div>
    </div>

    <div class="grid-layout">
        <div>
            <div class="info-section">
                <h2>🛍️ Select Your Items</h2>
                <p style="color: #64748b; margin-bottom: 1.5rem;">Browse and select items you need.</p>
                <div class="product-showcase">
                    {% for item in catalog %}
                    <div class="product-card">
                        <div style="font-size: 28px; font-weight: 700; margin-bottom: 1rem;">{{ item.visual }}</div>
                        <div style="font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; margin-bottom: 0.75rem;">{{ item.group }}</div>
                        <div style="font-weight: 700; color: #1e293b; margin-bottom: 0.25rem;">{{ item.label }}</div>
                        <div style="font-size: 1.3rem; color: var(--primary); font-weight: 800;">₹{{ item.rate }}</div>
                    </div>
                    {% endfor %}
                </div>
            </div>

            {% if ordering_open %}
            <div class="order-form">
                <h2>📝 Create Your Order</h2>
                <form method="post">
                    {% csrf_token %}
                    {{ form.as_p }}
                    <button type="submit" class="btn-primary">✨ Add Order</button>
                </form>
            </div>
            {% endif %}

            <div class="order-form" style="background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border: 2px solid #e2e8f0;">
                <h2 style="display: flex; align-items: center; gap: 0.5rem;">📦 Your Orders <span style="font-size: 0.85rem; background: var(--primary); color: white; padding: 0.3rem 0.8rem; border-radius: 20px;">{{ own_orders|length }}</span></h2>
                {% if own_orders %}
                <div style="display: grid; gap: 1rem;">
                    {% for order in own_orders %}
                    <div style="background: white; border-radius: 12px; padding: 1rem; border-left: 4px solid var(--primary);">
                        <div style="display: flex; justify-content: space-between; align-items: start; gap: 1rem;">
                            <div>
                                <div style="font-weight: 700; color: #1e293b; margin-bottom: 0.5rem;">{{ order.wearer_name }} • {{ order.get_item_type_display }}</div>
                                <div style="font-size: 0.9rem; color: #64748b; margin-bottom: 0.5rem;">{{ order.get_gender_display }} • Size {{ order.display_size }} • Qty {{ order.quantity }}{% if order.jersey_number %} • #{{ order.jersey_number }}{% endif %}</div>
                                <div style="font-size: 1.1rem; font-weight: 700; color: var(--primary);">₹{{ order.line_total }}</div>
                            </div>
                            {% if ordering_open %}
                            <form method="post" action="{% url 'jersey-order-delete' order.id %}">
                                {% csrf_token %}
                                <button type="submit" class="btn-danger">🗑️ Remove</button>
                            </form>
                            {% else %}
                            <span style="background: #f1f5f9; color: #475569; padding: 0.5rem 1rem; border-radius: 6px; font-weight: 700; font-size: 0.85rem;">🔒 Locked</span>
                            {% endif %}
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% else %}
                <div style="text-align: center; padding: 2rem; color: #94a3b8;">
                    <p style="margin: 0;">No orders yet. Create your first order using the form above!</p>
                </div>
                {% endif %}
            </div>
        </div>

        <aside class="sidebar">
            <div class="order-summary">
                <h3 style="margin: 0 0 1rem 0; font-weight: 700; color: #1e293b; font-size: 1.1rem;">💳 Order Summary</h3>
                <p style="text-align: center; padding: 1.5rem; color: #94a3b8; margin: 0;">Select items to see summary</p>
            </div>

            <div class="order-summary">
                <h3 style="margin: 0 0 1rem 0; font-weight: 700; color: #1e293b; font-size: 1.1rem;">ℹ️ Quick Tips</h3>
                <div style="display: grid; gap: 0.75rem; font-size: 0.9rem; color: #475569; line-height: 1.6;">
                    <div style="padding-bottom: 0.75rem; border-bottom: 1px solid #e2e8f0;">
                        <strong style="color: #1e293b;">📐 Size Matters</strong><br>Use the size charts to find your perfect fit.
                    </div>
                    <div style="padding-bottom: 0.75rem; border-bottom: 1px solid #e2e8f0;">
                        <strong style="color: #1e293b;">👶 Kids Measurement</strong><br>Measure a well-fitting item for accuracy.
                    </div>
                    <div style="padding-bottom: 0.75rem; border-bottom: 1px solid #e2e8f0;">
                        <strong style="color: #1e293b;">🎯 Jersey Numbers</strong><br>Optional. Can be reused across categories.
                    </div>
                    <div>
                        <strong style="color: #1e293b;">💰 Final Price</strong><br>Excludes shipping. Confirmed later.
                    </div>
                </div>
            </div>
        </aside>
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    console.log('Jersey Store loaded successfully');
});
</script>
{% endblock %}'''

with open('apps/jerseys/templates/jerseys/order_form.html', 'w', encoding='utf-8') as f:
    f.write(template)
print('✓ Template created successfully')
