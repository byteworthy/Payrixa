"""
DriftWatch views.

V1: Dashboard reading from existing DriftEvent model.
No new models - reuses payrixa.models.DriftEvent.
"""

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Avg, Max

from payrixa.utils import get_current_customer
from payrixa.models import DriftEvent, ReportRun


class DriftWatchDashboardView(LoginRequiredMixin, TemplateView):
    """
    DriftWatch dashboard showing volume and decision time drift signals.
    
    Uses existing DriftEvent model - NO new models for V1.
    """
    template_name = 'payrixa/products/driftwatch_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            customer = get_current_customer(self.request)
            context['customer'] = customer

            # Get base queryset (unsliced for filtering)
            base_queryset = DriftEvent.objects.filter(customer=customer)
            
            # Get recent drift events for display (sliced)
            drift_events = base_queryset.order_by('-created_at')[:50]

            # Summary metrics (from unsliced queryset)
            total_events = base_queryset.count()
            
            # Group by drift type (from unsliced queryset)
            denial_rate_count = base_queryset.filter(drift_type='DENIAL_RATE').count()
            decision_time_count = base_queryset.filter(drift_type='DECISION_TIME').count()

            # Top payers by drift frequency
            top_payers = DriftEvent.objects.filter(
                customer=customer
            ).values('payer').annotate(
                event_count=Count('id'),
                avg_severity=Avg('severity'),
                max_delta=Max('delta_value')
            ).order_by('-event_count')[:5]

            # Recent report runs
            recent_runs = ReportRun.objects.filter(
                customer=customer
            ).order_by('-started_at')[:5]

            # Evidence payload (shared schema)
            context.update({
                'drift_events': drift_events,
                'total_events': total_events,
                'denial_rate_count': denial_rate_count,
                'decision_time_count': decision_time_count,
                'top_payers': top_payers,
                'recent_runs': recent_runs,
                # V1 signal type for DriftWatch
                'v1_signal_type': 'volume_spike',
            })

        except ValueError as e:
            context['error'] = str(e)

        return context
