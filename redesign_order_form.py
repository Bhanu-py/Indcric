modern_design = r'''{% extends "base.html" %}
{% block title %}Jersey Store - Premium Team Kits{% endblock %}
{% block content %}
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; }

/* Hero Section */
.hero {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 5rem 2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
}

.hero::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
    opacity: 0.5;
}

.hero-content {
    position: relative;
    z-index: 1;
    max-width: 800px;
    margin: 0 auto;
}

.hero h1 {
    font-size: 3.5rem;
    font-weight: 900;
    letter-spacing: -2px;
    margin-bottom: 1rem;
    text-shadow: 0 2px 10px rgba(0,0,0,0.2);
}

.hero p {
    font-size: 1.3rem;
    opacity: 0.95;
    margin-bottom: 2rem;
}

.hero-badge {
    display: inline-block;
    background: rgba(255,255,255,0.2);
    backdrop-filter: blur(10px);
    padding: 0.75rem 1.5rem;
    border-radius: 50px;
    border: 1px solid rgba(255,255,255,0.3);
    font-weight: 600;
    margin-right: 1rem;
}

.hero-cta {
    display: inline-block;
    background: white;
    color: #667eea;
    padding: 1rem 2rem;
    border-radius: 50px;
    font-weight: 700;
    text-decoration: none;
    transition: all 0.3s ease;
    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
}

.hero-cta:hover {
    transform: translateY(-3px);
    box-shadow: 0 15px 40px rgba(0,0,0,0.3);
}

/* Container */
.container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 2rem;
}

.section {
    margin-bottom: 5rem;
}

.section-title {
    font-size: 2.5rem;
    font-weight: 900;
    text-align: center;
    margin-bottom: 3rem;
    color: #1a202c;
}

/* Product Grid */
.product-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 2rem;
    margin-bottom: 3rem;
}

.product-card {
    background: white;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
    display: flex;
    flex-direction: column;
}

.product-card:hover {
    transform: translateY(-12px);
    box-shadow: 0 20px 40px rgba(102, 126, 234, 0.2);
}

.product-visual {
    background: linear-gradient(135deg, #667eea15, #764ba215);
    padding: 2.5rem;
    text-align: center;
    font-size: 3.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 180px;
}

.product-info {
    padding: 1.5rem;
    flex-grow: 1;
    display: flex;
    flex-direction: column;
}

.product-category {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #a0aec0;
    font-weight: 700;
    margin-bottom: 0.5rem;
}

.product-name {
    font-size: 1rem;
    font-weight: 700;
    color: #1a202c;
    margin-bottom: 0.5rem;
}

.product-desc {
    font-size: 0.85rem;
    color: #718096;
    margin-bottom: 1rem;
    flex-grow: 1;
}

.product-price {
    font-size: 1.5rem;
    font-weight: 900;
    color: #667eea;
}

/* Info Cards */
.info-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 2rem;
    margin-bottom: 3rem;
}

.info-card {
    background: white;
    border-radius: 16px;
    padding: 2rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    border-left: 5px solid #667eea;
}

.info-card h3 {
    font-size: 1.2rem;
    font-weight: 700;
    color: #1a202c;
    margin-bottom: 1rem;
}

.info-card p {
    color: #4a5568;
    line-height: 1.6;
    font-size: 0.95rem;
}

/* Main Layout */
.main-layout {
    display: grid;
    grid-template-columns: 1fr 380px;
    gap: 3rem;
    margin-bottom: 3rem;
}

@media (max-width: 1024px) {
    .main-layout {
        grid-template-columns: 1fr;
    }
    .sidebar {
        order: -1;
    }
}

/* Form Section */
.form-card {
    background: white;
    border-radius: 16px;
    padding: 2.5rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}

.form-card h2 {
    font-size: 1.5rem;
    font-weight: 700;
    margin-bottom: 2rem;
    color: #1a202c;
}

.form-step {
    margin-bottom: 2.5rem;
    padding-bottom: 2.5rem;
    border-bottom: 1px solid #e2e8f0;
}

.form-step:last-child {
    border-bottom: none;
}

.form-step-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #1a202c;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
}

.step-number {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    flex-shrink: 0;
}

.form-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin-bottom: 1.5rem;
}

.form-group {
    display: flex;
    flex-direction: column;
}

.form-label {
    font-weight: 700;
    color: #1a202c;
    margin-bottom: 0.5rem;
    font-size: 0.95rem;
}

.form-label .required {
    color: #e53e3e;
}

.form-input,
.form-select,
.form-textarea {
    padding: 0.75rem 1rem;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    font-size: 0.95rem;
    font-family: inherit;
    transition: all 0.3s ease;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    background: #f7fafc;
}

.form-textarea {
    min-height: 100px;
    resize: vertical;
}

/* Checkbox Items */
.checkbox-grid {
    display: grid;
    gap: 1rem;
}

.checkbox-item {
    display: flex;
    gap: 1rem;
    padding: 1rem;
    border: 2px solid #e2e8f0;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.3s ease;
    align-items: flex-start;
}

.checkbox-item:hover {
    border-color: #667eea;
    background: #f7fafc;
}

.checkbox-item input[type="checkbox"] {
    margin-top: 4px;
    cursor: pointer;
    width: 20px;
    height: 20px;
    flex-shrink: 0;
}

.checkbox-item.checked {
    border-color: #667eea;
    background: linear-gradient(135deg, #f7fafc, #edf2f7);
}

.checkbox-content {
    flex: 1;
}

.checkbox-label {
    font-weight: 700;
    color: #1a202c;
    margin-bottom: 0.25rem;
}

.checkbox-price {
    font-size: 1.2rem;
    font-weight: 900;
    color: #667eea;
    margin-top: 0.5rem;
}

.checkbox-desc {
    font-size: 0.85rem;
    color: #718096;
    margin-top: 0.5rem;
}

.qty-input {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-shrink: 0;
}

.qty-btn {
    background: #e2e8f0;
    color: #1a202c;
    border: none;
    width: 32px;
    height: 32px;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 700;
    transition: all 0.2s ease;
}

.qty-btn:hover {
    background: #667eea;
    color: white;
}

.qty-input input {
    width: 50px;
    text-align: center;
    border: 2px solid #e2e8f0;
    border-radius: 6px;
    padding: 0.4rem;
    font-weight: 700;
}

/* Sidebar */
.sidebar {
    position: sticky;
    top: 2rem;
}

.order-summary {
    background: white;
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}

.order-summary h3 {
    font-size: 1.1rem;
    font-weight: 700;
    color: #1a202c;
    margin-bottom: 1rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid #e2e8f0;
}

.order-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 0;
    font-size: 0.9rem;
    color: #4a5568;
    border-bottom: 1px solid #f1f5f9;
}

.order-item:last-child {
    border-bottom: none;
}

.order-item-name {
    font-weight: 600;
    color: #1a202c;
    flex: 1;
}

.order-item-qty {
    color: #a0aec0;
    font-size: 0.8rem;
    margin: 0 0.5rem;
}

.order-item-price {
    font-weight: 700;
    color: #667eea;
}

.order-total {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    background: linear-gradient(135deg, #f7fafc, #edf2f7);
    border-radius: 8px;
    margin-top: 1rem;
    font-weight: 700;
}

.order-total-price {
    font-size: 1.5rem;
    color: #667eea;
}

/* Buttons */
.btn {
    display: inline-block;
    padding: 1rem 2rem;
    border: none;
    border-radius: 8px;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.3s ease;
    text-decoration: none;
    text-align: center;
    font-size: 1rem;
}

.btn-primary {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    width: 100%;
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
}

.btn-secondary {
    background: white;
    color: #667eea;
    border: 2px solid #667eea;
}

.btn-secondary:hover {
    background: #f7fafc;
}

.btn-danger {
    background: #e53e3e;
    color: white;
    padding: 0.5rem 1rem;
    font-size: 0.85rem;
}

.btn-danger:hover {
    background: #c53030;
}

/* Alerts */
.alert {
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    font-size: 0.95rem;
}

.alert-warning {
    background: linear-gradient(135deg, #fffbeb, #fef3c7);
    border: 2px solid #fcd34d;
    color: #78350f;
}

.alert-warning h4 {
    margin: 0 0 0.5rem 0;
    font-weight: 700;
}

.alert-warning p {
    margin: 0.25rem 0;
    line-height: 1.6;
}

/* Orders Display */
.orders-list {
    display: grid;
    gap: 1rem;
}

.order-item-card {
    background: white;
    border-radius: 12px;
    padding: 1rem;
    border-left: 4px solid #667eea;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.order-item-info {
    flex: 1;
}

.order-item-info-title {
    font-weight: 700;
    color: #1a202c;
    margin-bottom: 0.25rem;
}

.order-item-info-details {
    font-size: 0.85rem;
    color: #718096;
    margin-bottom: 0.5rem;
}

.order-item-info-price {
    font-weight: 700;
    color: #667eea;
    font-size: 1.1rem;
}

/* Utilities */
.text-center { text-align: center; }
.mb-1 { margin-bottom: 0.5rem; }
.mb-2 { margin-bottom: 1rem; }
.mb-3 { margin-bottom: 1.5rem; }
.mb-4 { margin-bottom: 2rem; }
.mt-1 { margin-top: 0.5rem; }
.mt-2 { margin-top: 1rem; }
.text-gray { color: #718096; }
.text-sm { font-size: 0.875rem; }

@media (max-width: 768px) {
    .hero h1 {
        font-size: 2.2rem;
    }
    
    .section-title {
        font-size: 1.8rem;
    }
    
    .product-grid {
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 1rem;
    }
    
    .form-row {
        grid-template-columns: 1fr;
    }
    
    .main-layout {
        gap: 1.5rem;
    }
    
    .checkbox-item {
        flex-direction: column;
    }
    
    .qty-input {
        width: 100%;
        justify-content: space-between;
    }
}
</style>

<div class="hero">
    <div class="hero-content">
        <h1>🏏 Jersey Store</h1>
        <p>Premium team kits - Order now with custom sizing</p>
        <div style="margin-top: 1.5rem;">
            {% if ordering_open %}
            <span class="hero-badge">✓ Open for orders</span>
            {% else %}
            <span class="hero-badge" style="background: rgba(239,68,68,0.2); color: white;">⊗ Closed</span>
            {% endif %}
            {% if request.user.is_staff %}
            <a href="{% url 'jersey-orders-admin' %}" class="hero-cta">📊 Admin Dashboard</a>
            {% endif %}
        </div>
    </div>
</div>

<div class="container">
    {% if not ordering_open %}
    <div class="alert alert-warning" style="margin-top: 3rem;">
        <h4>⚠️ Ordering is closed</h4>
        <p>We're not accepting new orders right now, but you can still review your submitted orders below.</p>
    </div>
    {% endif %}

    <div class="alert alert-warning">
        <h4>💡 Important</h4>
        <p><strong>Prices in Indian Rupees (₹)</strong> • Excludes shipping • Family & kids can reuse jersey numbers</p>
    </div>

    <!-- Info Cards -->
    <div class="info-grid section">
        <div class="info-card">
            <h3>📏 Sizing Guide</h3>
            <p>Compare measurements from our charts with a shirt that fits well. We focus on Full Chest + Length for accuracy.</p>
        </div>
        <div class="info-card">
            <h3>👶 Kids Measurement</h3>
            <p>Measure a well-fitting garment your child owns, enter exact measurements, and our makers will customize perfectly.</p>
        </div>
        <div class="info-card">
            <h3>✅ After Ordering</h3>
            <p>Review your complete order and our team will process all orders in batches. You'll be notified of delivery dates.</p>
        </div>
    </div>

    <!-- Main Layout -->
    <div class="main-layout">
        <!-- Left: Main Content -->
        <div>
            <!-- Product Showcase -->
            <div class="section">
                <h2 class="section-title">🛍️ Browse Our Items</h2>
                <div class="product-grid">
                    {% for item in catalog %}
                    <div class="product-card">
                        <div class="product-visual">{{ item.visual }}</div>
                        <div class="product-info">
                            <div class="product-category">{{ item.group }}</div>
                            <div class="product-name">{{ item.label }}</div>
                            {% if item.note %}<div class="product-desc">{{ item.note }}</div>{% endif %}
                            <div class="product-price">₹{{ item.rate }}</div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Order Form -->
            {% if ordering_open %}
            <div class="form-card section">
                <h2>📝 Create Your Order</h2>
                <form method="post">
                    {% csrf_token %}

                    {% if form.non_field_errors %}
                    <div class="alert alert-warning" style="color: #c53030; background: linear-gradient(135deg, #fee, #fdd);">
                        {{ form.non_field_errors }}
                    </div>
                    {% endif %}

                    <!-- Step 1: Wearer Info -->
                    <div class="form-step">
                        <div class="form-step-title">
                            <span class="step-number">1</span>
                            Wearer Information
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">For <span class="required">*</span></label>
                                {{ form.for_person }}
                                {{ form.for_person.errors }}
                            </div>
                            <div class="form-group">
                                <label class="form-label">Gender / Fit <span class="required">*</span></label>
                                {{ form.gender }}
                                {{ form.gender.errors }}
                            </div>
                            <div class="form-group">
                                <label class="form-label">Wearer Name <span class="required">*</span></label>
                                {{ form.wearer_name }}
                                {{ form.wearer_name.errors }}
                            </div>
                            <div class="form-group">
                                <label class="form-label">Jersey Number</label>
                                {{ form.jersey_number }}
                                <p class="text-sm text-gray mt-1">Optional. Family & kids can reuse numbers.</p>
                                {{ form.jersey_number.errors }}
                            </div>
                        </div>
                    </div>

                    <!-- Step 2: Items Selection -->
                    <div class="form-step">
                        <div class="form-step-title">
                            <span class="step-number">2</span>
                            Select Items & Quantities
                        </div>
                        <p class="text-gray mb-2">Choose items you need, then adjust quantities.</p>
                        <div class="checkbox-grid">
                            {% for item in item_rows %}
                            <div class="checkbox-item" onclick="this.querySelector('input').checked = !this.querySelector('input').checked; updateItemSelection(this.querySelector('input'));">
                                <input type="checkbox" name="item_types" value="{{ item.code }}" {% if item.checked %}checked{% endif %} onchange="updateItemSelection(this)">
                                <div class="checkbox-content">
                                    <div class="checkbox-label">{{ item.label }}</div>
                                    <div class="checkbox-desc">{{ item.group }}</div>
                                    <div class="checkbox-price">₹{{ item.rate }}</div>
                                </div>
                                <div class="qty-input">
                                    <button type="button" class="qty-btn" onclick="decrementQty(event)">−</button>
                                    {{ item.quantity_field }}
                                    <button type="button" class="qty-btn" onclick="incrementQty(event)">+</button>
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                        {{ form.item_types.errors }}
                    </div>

                    <!-- Step 3: Size Selection -->
                    <div class="form-step">
                        <div class="form-step-title">
                            <span class="step-number">3</span>
                            Choose Size
                        </div>
                        <div style="background: linear-gradient(135deg, #f0f9ff, #e0f2fe); border: 2px solid #bfdbfe; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;">
                            <h4 style="font-weight: 700; color: #0c4a6e; margin-bottom: 1rem;">👔 Adult Standard Sizes</h4>
                            <div class="form-row">
                                <div class="form-group">
                                    <label class="form-label">Shirt Size</label>
                                    {{ form.shirt_size }}
                                    <p class="text-sm text-gray mt-1">Pick by Full Chest + Length from the chart below.</p>
                                    {{ form.shirt_size.errors }}
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Pant / Shorts Size</label>
                                    {{ form.pant_size }}
                                    <p class="text-sm text-gray mt-1">Pick by Length + Relaxed Waist from the chart below.</p>
                                    {{ form.pant_size.errors }}
                                </div>
                            </div>
                        </div>

                        <div style="background: linear-gradient(135deg, #faf5ff, #f3e8ff); border: 2px solid #ddd6fe; border-radius: 12px; padding: 1.5rem;">
                            <h4 style="font-weight: 700; color: #6b21a8; margin-bottom: 1rem;">👶 Kids Custom Measurements</h4>
                            <p class="text-sm text-gray mb-2">Measure a well-fitting item and enter exact measurements.</p>
                            <div class="form-row">
                                <div class="form-group">
                                    <label class="form-label">Shirt: Full Chest (in)</label>
                                    {{ form.kid_shirt_full_chest }}
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Shirt: Half Chest (in)</label>
                                    {{ form.kid_shirt_half_chest }}
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Shirt: Length (in)</label>
                                    {{ form.kid_shirt_length }}
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Shirt: Shoulder (in)</label>
                                    {{ form.kid_shirt_shoulder }}
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Pant: Length (in)</label>
                                    {{ form.kid_pant_length }}
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Pant: Relaxed Waist (in)</label>
                                    {{ form.kid_pant_relaxed_waist }}
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Pant: Half Hip (in)</label>
                                    {{ form.kid_pant_half_hip }}
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Step 4: Notes -->
                    <div class="form-step">
                        <div class="form-step-title">
                            <span class="step-number">4</span>
                            Special Requests
                        </div>
                        <div class="form-group">
                            <label class="form-label">Notes (Optional)</label>
                            {{ form.notes }}
                            <p class="text-sm text-gray mt-1">Any special requests or customization notes?</p>
                            {{ form.notes.errors }}
                        </div>
                    </div>

                    <button type="submit" class="btn btn-primary">✨ Submit Order</button>
                </form>
            </div>
            {% endif %}

            <!-- Your Orders -->
            <div class="form-card section">
                <h2>📦 Your Orders ({{ own_orders|length }})</h2>
                {% if own_orders %}
                <div class="orders-list">
                    {% for order in own_orders %}
                    <div class="order-item-card">
                        <div class="order-item-info">
                            <div class="order-item-info-title">{{ order.wearer_name }} • {{ order.get_item_type_display }}</div>
                            <div class="order-item-info-details">{{ order.get_gender_display }} • Size {{ order.display_size }} • Qty {{ order.quantity }}{% if order.jersey_number %} • #{{ order.jersey_number }}{% endif %}</div>
                            <div class="order-item-info-price">₹{{ order.line_total }}</div>
                        </div>
                        {% if ordering_open %}
                        <form method="post" action="{% url 'jersey-order-delete' order.id %}">
                            {% csrf_token %}
                            <button type="submit" class="btn btn-danger">🗑️ Remove</button>
                        </form>
                        {% else %}
                        <span style="background: #f1f5f9; color: #4a5568; padding: 0.5rem 1rem; border-radius: 6px; font-weight: 700; font-size: 0.85rem;">🔒 Locked</span>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
                {% else %}
                <p style="text-align: center; color: #a0aec0; padding: 2rem;">No orders yet. Create your first order above!</p>
                {% endif %}
            </div>
        </div>

        <!-- Right: Sidebar -->
        <aside class="sidebar">
            <div class="order-summary">
                <h3>💳 Order Summary</h3>
                <div id="orderSummaryItems">
                    <p style="text-align: center; padding: 1rem; color: #a0aec0;">Select items to see summary</p>
                </div>
                <div class="order-total">
                    <div>Total:</div>
                    <div class="order-total-price" id="totalAmount">₹0</div>
                </div>
            </div>

            <div class="order-summary" style="margin-top: 1.5rem;">
                <h3>ℹ️ Quick Guide</h3>
                <div style="display: grid; gap: 1rem; font-size: 0.9rem; color: #4a5568; line-height: 1.6;">
                    <div style="padding-bottom: 1rem; border-bottom: 1px solid #e2e8f0;">
                        <strong style="color: #1a202c;">📐 Sizing</strong><br>
                        Use our size charts. Compare Full Chest + Length.
                    </div>
                    <div style="padding-bottom: 1rem; border-bottom: 1px solid #e2e8f0;">
                        <strong style="color: #1a202c;">👶 Kids</strong><br>
                        Measure a well-fitting item for best results.
                    </div>
                    <div style="padding-bottom: 1rem; border-bottom: 1px solid #e2e8f0;">
                        <strong style="color: #1a202c;">🎯 Numbers</strong><br>
                        Optional, can be reused across categories.
                    </div>
                    <div>
                        <strong style="color: #1a202c;">💰 Price</strong><br>
                        Final amount excludes shipping charges.
                    </div>
                </div>
            </div>
        </aside>
    </div>
</div>

<script>
function incrementQty(e) {
    e.preventDefault();
    const input = e.target.parentElement.querySelector('input[type="number"]');
    input.value = Math.max(0, (parseInt(input.value) || 0) + 1);
    updateOrderSummary();
}

function decrementQty(e) {
    e.preventDefault();
    const input = e.target.parentElement.querySelector('input[type="number"]');
    input.value = Math.max(0, (parseInt(input.value) || 0) - 1);
    updateOrderSummary();
}

function updateItemSelection(checkbox) {
    const item = checkbox.closest('.checkbox-item');
    if (checkbox.checked) {
        item.classList.add('checked');
    } else {
        item.classList.remove('checked');
    }
    updateOrderSummary();
}

function updateOrderSummary() {
    let total = 0;
    const items = [];
    
    document.querySelectorAll('.checkbox-item').forEach(item => {
        const checkbox = item.querySelector('input[type="checkbox"]');
        const input = item.querySelector('input[type="number"]');
        
        if (checkbox && checkbox.checked && input && input.value > 0) {
            const label = item.querySelector('.checkbox-label').textContent;
            const price = parseFloat(item.querySelector('.checkbox-price').textContent.replace('₹', ''));
            const qty = parseInt(input.value) || 0;
            const itemTotal = price * qty;
            total += itemTotal;
            
            items.push({
                name: label,
                qty: qty,
                price: price,
                total: itemTotal
            });
        }
    });

    const summaryDiv = document.getElementById('orderSummaryItems');
    if (items.length === 0) {
        summaryDiv.innerHTML = '<p style="text-align: center; padding: 1rem; color: #a0aec0;">Select items to see summary</p>';
    } else {
        summaryDiv.innerHTML = items.map(item => `
            <div class="order-item">
                <span class="order-item-name">${item.name}</span>
                <span class="order-item-qty">×${item.qty}</span>
                <span class="order-item-price">₹${item.total.toFixed(2)}</span>
            </div>
        `).join('');
    }
    
    document.getElementById('totalAmount').textContent = `₹${total.toFixed(2)}`;
}

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('input[type="number"]').forEach(input => {
        input.addEventListener('change', updateOrderSummary);
        input.addEventListener('input', updateOrderSummary);
    });
    updateOrderSummary();
});
</script>
{% endblock %}'''

with open('apps/jerseys/templates/jerseys/order_form.html', 'w', encoding='utf-8') as f:
    f.write(modern_design)
print('✓ Modern e-commerce redesign created!')
