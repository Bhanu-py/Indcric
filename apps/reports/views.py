"""Views for tax compliance reports."""

from datetime import datetime, timedelta
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone

from apps.sessions.models import Session
from .excel_export import TaxComplianceExcelExport


@staff_member_required
def tax_report_download(request):
    """Download tax compliance report as Excel."""
    
    if request.method == 'POST':
        # Get filter parameters
        from_date_str = request.POST.get('from_date')
        to_date_str = request.POST.get('to_date')
        venue = request.POST.get('venue')
        
        # Parse dates
        from_date = None
        to_date = None
        
        try:
            if from_date_str:
                from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            if to_date_str:
                to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
            else:
                to_date = timezone.now().date()
        except ValueError:
            from django.contrib import messages
            messages.error(request, "Invalid date format. Use YYYY-MM-DD.")
            return redirect('tax_report_download')
        
        # Generate Excel
        try:
            exporter = TaxComplianceExcelExport(
                from_date=from_date,
                to_date=to_date,
                venue=venue if venue else None,
                generated_by=request.user
            )
            excel_buffer = exporter.generate()
            
            # Return as file download
            filename = f"IndCric_Tax_Report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            response = HttpResponse(
                excel_buffer.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        except Exception as e:
            from django.contrib import messages
            messages.error(request, f"Error generating report: {str(e)}")
            return redirect('tax_report_download')
    
    # GET: Show form
    # Get all possible venues (hardcoded options + any from database)
    hardcoded_venues = ['GUSB', 'Henry Storyplein', 'HOGENT Sports hall']
    db_venues = list(Session.objects.filter(location__isnull=False).values_list('location', flat=True).distinct())
    all_venues = sorted(set(hardcoded_venues + db_venues))
    
    # Default date range: full current year (01-01 to 31-12)
    today = timezone.now().date()
    from_date = today.replace(month=1, day=1)
    to_date = today.replace(month=12, day=31)
    
    context = {
        'venues': all_venues,
        'default_from_date': from_date.strftime('%Y-%m-%d'),
        'default_to_date': to_date.strftime('%Y-%m-%d'),
    }
    
    return render(request, 'reports/tax_report_form.html', context)
