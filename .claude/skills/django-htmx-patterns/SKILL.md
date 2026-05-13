---
name: django-htmx-patterns
description: Use when building any new view, template, form, or interactive feature in the IndCric Django app. Covers the project's HTMX 2.0 + Alpine.js + Hyperscript stack (no JS framework, no REST/JSON), the `request.htmx` partial-vs-full-page response pattern, hx-target/hx-swap conventions, @staff_member_required for mutations, named URL patterns under the `cric:` namespace, Tailwind utility classes used across the app, and the new-feature checklist (model → form → view → URL → template → nav → admin → tests).
---

# Django + HTMX Patterns for IndCric

Use this skill when building new views, templates, or interactive features in this project.

## Core Stack Behaviour

- **No JavaScript framework** — all interactivity is HTMX + Alpine.js + Hyperscript
- **HTMX version**: 2.0.2 (included in base.html via CDN)
- **Partial responses**: views detect `request.htmx` and return a partial template instead of a full page
- **No REST API**: all responses are HTML, not JSON

## Request Detection Pattern

```python
from django.shortcuts import render, redirect

def my_view(request, pk):
    obj = get_object_or_404(MyModel, pk=pk)
    context = {'obj': obj}

    if request.htmx:
        return render(request, 'cric/partials/my_partial.html', context)
    return render(request, 'cric/pages/my_page.html', context)
```

## HTMX Trigger Patterns Used in This Project

```html
<!-- Swap a section on button click -->
<button hx-post="/session/{{ session.id }}/save-teams/"
        hx-target="#teams-section"
        hx-swap="outerHTML">
  Save Teams
</button>

<!-- Inline edit that swaps in a form -->
<span hx-get="/users/edit/{{ user.id }}/"
      hx-target="#user-row-{{ user.id }}"
      hx-swap="outerHTML">
  Edit
</span>

<!-- Polling / live update -->
<div hx-get="/session/{{ session.id }}/poll-votes/"
     hx-trigger="every 10s"
     hx-swap="innerHTML">
  ...
</div>
```

## Alpine.js Usage

Alpine.js handles purely client-side state (toggling panels, showing/hiding elements).

```html
<!-- Toggle visibility -->
<div x-data="{ open: false }">
  <button @click="open = !open">Toggle</button>
  <div x-show="open">Content</div>
</div>

<!-- Dynamic team assignment (client-side before HTMX submit) -->
<div x-data="{ teamA: [], teamB: [] }">
  ...
</div>
```

## Form Submission Pattern (HTMX + Django)

```python
def my_form_view(request):
    if request.method == 'POST':
        form = MyForm(request.POST)
        if form.is_valid():
            form.save()
            if request.htmx:
                return render(request, 'cric/partials/success_partial.html')
            return redirect('cric:home')
        # Re-render form with errors
        if request.htmx:
            return render(request, 'cric/partials/my_form_partial.html', {'form': form})
    else:
        form = MyForm()
    return render(request, 'cric/pages/my_form_page.html', {'form': form})
```

## Staff-Only Views

```python
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def admin_only_view(request):
    ...
```

## URL Naming Convention

```python
# cric/urls.py — all URLs use app_name = 'cric'
app_name = 'cric'
urlpatterns = [
    path('session/<int:pk>/', views.session_detail_view, name='session_detail'),
    ...
]

# In templates:
# {% url 'cric:session_detail' session.id %}
```

## Template Inheritance

```html
<!-- Full page -->
{% extends "base.html" %}
{% block content %}
...
{% endblock %}

<!-- Partial (no extends — returned for HTMX swaps) -->
<div id="my-target">
  {{ data }}
</div>
```

## Django Messages with HTMX

Messages need special handling when the response is a partial. Either:
1. Include `templates/includes/messages.html` in the partial and target it to swap into the messages container
2. Or use `HX-Trigger` response header to fire a toast event

```python
# In view
from django.contrib import messages
messages.success(request, 'Teams saved!')

# Return partial that includes messages partial
return render(request, 'cric/partials/teams_with_messages.html', context)
```

## Custom Template Tags (templatetags/custom_filters.py)

```python
# Access dict key in template
{{ my_dict|get_item:key_variable }}

# Multiply two numbers
{{ value|mul:2 }}
```

## Tailwind CSS Conventions

- Use utility classes directly in templates
- No custom CSS unless absolutely necessary (check `static/css/user_table.css`)
- Status badges: `bg-green-100 text-green-700` (paid), `bg-yellow-100 text-yellow-700` (pending)
- Cards: `bg-white rounded-lg shadow p-4`
- Primary button: `bg-indigo-600 text-white hover:bg-indigo-700 px-4 py-2 rounded`
- Danger button: `bg-red-600 text-white hover:bg-red-700 px-4 py-2 rounded`

## Adding a New Feature: Checklist

1. **Model** — add to `cric/models.py`, create migration
2. **Form** — add to `cric/forms.py` if user input needed
3. **View** — add to appropriate `views_*.py` file, handle both HTMX and full-page cases
4. **URL** — add to `cric/urls.py` with a named pattern
5. **Template** — add full-page template in `cric/templates/cric/pages/` and partial in `partials/` if needed
6. **Nav link** — add to `templates/includes/header.html` if top-level feature
7. **Admin** — register model in `cric/admin.py`
8. **Tests** — at minimum test the happy-path view response code
