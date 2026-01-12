from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from .models import Settings
from .utils import get_current_customer

class UploadsView(LoginRequiredMixin, TemplateView):
    template_name = "driftwatch/uploads.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            customer = get_current_customer(self.request)
            context['customer'] = customer
        except ValueError as e:
            messages.error(self.request, str(e))
        return context

class SettingsView(LoginRequiredMixin, View):
    template_name = "driftwatch/settings.html"

    def get(self, request):
        try:
            customer = get_current_customer(request)

            # Get or create settings for the customer
            settings, created = Settings.objects.get_or_create(customer=customer)

            return render(request, self.template_name, {
                'settings': settings,
                'customer': customer
            })

        except ValueError as e:
            messages.error(request, str(e))
            return redirect('portal_root')

    def post(self, request):
        try:
            customer = get_current_customer(request)

            # Get or create settings for the customer
            settings, created = Settings.objects.get_or_create(customer=customer)

            # Update settings from form data
            settings.to_email = request.POST.get('to_email', '')
            settings.cc_email = request.POST.get('cc_email', '') or None
            settings.attach_pdf = 'attach_pdf' in request.POST

            settings.save()

            messages.success(request, "Settings saved successfully!")
            return redirect('settings')

        except ValueError as e:
            messages.error(request, str(e))
            return redirect('portal_root')

class DriftFeedView(LoginRequiredMixin, TemplateView):
    template_name = "driftwatch/drift_feed.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            customer = get_current_customer(self.request)
            context['customer'] = customer
        except ValueError as e:
            messages.error(self.request, str(e))
        return context

class ReportsView(LoginRequiredMixin, TemplateView):
    template_name = "driftwatch/reports.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            customer = get_current_customer(self.request)
            context['customer'] = customer
        except ValueError as e:
            messages.error(self.request, str(e))
        return context
