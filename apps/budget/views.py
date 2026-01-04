from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.utils import timezone
from .models import (
    Budget, BudgetCategory, BudgetApproval, BudgetRevision, 
    ExpenseRequest, PaymentSchedule, BudgetReport
)

# Budget Views
class BudgetListView(LoginRequiredMixin, ListView):
    model = Budget
    template_name = 'budget/budget_list.html'
    context_object_name = 'budgets'
    paginate_by = 20

    def get_queryset(self):
        queryset = Budget.objects.select_related('owner', 'project')
        
        # Filter by search query
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(department__icontains=search)
            )
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        # Filter by budget type
        budget_type = self.request.GET.get('budget_type')
        if budget_type:
            queryset = queryset.filter(budget_type=budget_type)
            
        return queryset

class BudgetDetailView(LoginRequiredMixin, DetailView):
    model = Budget
    template_name = 'budget/budget_detail.html'
    context_object_name = 'budget'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        budget = self.get_object()
        context['categories'] = budget.categories.all()
        context['approvals'] = budget.approvals.all()
        context['revisions'] = budget.revisions.all()
        return context

class BudgetCreateView(LoginRequiredMixin, CreateView):
    model = Budget
    template_name = 'budget/budget_form.html'
    fields = ['name', 'description', 'budget_type', 'total_amount', 'period_start', 'period_end', 'department', 'project']

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, f'Budget "{form.instance.name}" created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('budget:detail', kwargs={'pk': self.object.pk})

class BudgetUpdateView(LoginRequiredMixin, UpdateView):
    model = Budget
    template_name = 'budget/budget_form.html'
    fields = ['name', 'description', 'budget_type', 'total_amount', 'period_start', 'period_end', 'department']

    def form_valid(self, form):
        messages.success(self.request, f'Budget "{form.instance.name}" updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('budget:detail', kwargs={'pk': self.object.pk})

class BudgetDeleteView(LoginRequiredMixin, DeleteView):
    model = Budget
    template_name = 'budget/budget_confirm_delete.html'
    success_url = reverse_lazy('budget:list')

    def delete(self, request, *args, **kwargs):
        budget = self.get_object()
        messages.success(request, f'Budget "{budget.name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)

# Budget Category Views
class BudgetCategoryListView(LoginRequiredMixin, ListView):
    model = BudgetCategory
    template_name = 'budget/category_list.html'
    context_object_name = 'categories'
    paginate_by = 25

    def get_queryset(self):
        budget_id = self.kwargs.get('budget_id')
        if budget_id:
            return BudgetCategory.objects.filter(budget_id=budget_id).select_related('budget')
        return BudgetCategory.objects.select_related('budget')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        budget_id = self.kwargs.get('budget_id')
        if budget_id:
            context['budget'] = get_object_or_404(Budget, pk=budget_id)
        return context

class BudgetCategoryCreateView(LoginRequiredMixin, CreateView):
    model = BudgetCategory
    template_name = 'budget/category_form.html'
    fields = ['budget', 'name', 'category_type', 'description', 'allocated_amount', 'requires_approval', 'approval_threshold']

    def get_initial(self):
        initial = super().get_initial()
        budget_id = self.kwargs.get('budget_id')
        if budget_id:
            initial['budget'] = budget_id
        return initial

    def form_valid(self, form):
        messages.success(self.request, f'Budget category "{form.instance.name}" created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        budget_id = self.kwargs.get('budget_id')
        if budget_id:
            return reverse('budget:category_list', kwargs={'budget_id': budget_id})
        return reverse('budget:category_list')

class BudgetCategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = BudgetCategory
    template_name = 'budget/category_form.html'
    fields = ['name', 'category_type', 'description', 'allocated_amount', 'requires_approval', 'approval_threshold', 'is_active']

    def form_valid(self, form):
        messages.success(self.request, f'Budget category "{form.instance.name}" updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('budget:category_list', kwargs={'budget_id': self.object.budget.pk})

class BudgetCategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = BudgetCategory
    template_name = 'budget/category_confirm_delete.html'

    def get_success_url(self):
        return reverse('budget:category_list', kwargs={'budget_id': self.object.budget.pk})

    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        messages.success(request, f'Budget category "{category.name}" deleted successfully.')
        return super().delete(request, *args, **kwargs)

# Payment Schedule Views
class PaymentScheduleListView(LoginRequiredMixin, ListView):
    model = PaymentSchedule
    template_name = 'budget/payment_schedule_list.html'
    context_object_name = 'schedules'
    paginate_by = 25

    def get_queryset(self):
        queryset = PaymentSchedule.objects.select_related('project', 'milestone', 'budget_category')
        
        # Filter by project
        project_id = self.request.GET.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
            
        # Filter by status
        status = self.request.GET.get('status')
        if status == 'paid':
            queryset = queryset.filter(is_paid=True)
        elif status == 'pending':
            queryset = queryset.filter(is_paid=False)
        elif status == 'overdue':
            queryset = queryset.filter(is_paid=False, due_date__lt=timezone.now().date())
            
        return queryset.order_by('due_date')

class PaymentScheduleCreateView(LoginRequiredMixin, CreateView):
    model = PaymentSchedule
    template_name = 'budget/payment_schedule_form.html'
    fields = ['project', 'milestone', 'description', 'amount', 'percentage', 'due_date', 'budget_category']

    def form_valid(self, form):
        messages.success(self.request, f'Payment schedule "{form.instance.description}" created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('budget:payment_schedule_list')

class PaymentScheduleUpdateView(LoginRequiredMixin, UpdateView):
    model = PaymentSchedule
    template_name = 'budget/payment_schedule_form.html'
    fields = ['project', 'milestone', 'description', 'amount', 'percentage', 'due_date', 'payment_date', 'is_paid', 'invoice_number', 'payment_reference', 'budget_category']

    def form_valid(self, form):
        messages.success(self.request, f'Payment schedule "{form.instance.description}" updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('budget:payment_schedule_list')

class PaymentScheduleDeleteView(LoginRequiredMixin, DeleteView):
    model = PaymentSchedule
    template_name = 'budget/payment_schedule_confirm_delete.html'
    success_url = reverse_lazy('budget:payment_schedule_list')

    def delete(self, request, *args, **kwargs):
        schedule = self.get_object()
        messages.success(request, f'Payment schedule "{schedule.description}" deleted successfully.')
        return super().delete(request, *args, **kwargs)

# Budget Approval Views
class BudgetApprovalListView(LoginRequiredMixin, ListView):
    model = BudgetApproval
    template_name = 'budget/approval_list.html'
    context_object_name = 'approvals'
    paginate_by = 25

    def get_queryset(self):
        queryset = BudgetApproval.objects.select_related('budget', 'approver')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset.order_by('-created_at')

class BudgetApprovalUpdateView(LoginRequiredMixin, UpdateView):
    model = BudgetApproval
    template_name = 'budget/approval_form.html'
    fields = ['status', 'comments', 'approved_amount']

    def form_valid(self, form):
        form.instance.approver = self.request.user
        form.instance.decision_date = timezone.now()
        
        # Update budget status based on approval
        if form.instance.status == 'approved':
            form.instance.budget.status = 'approved'
            form.instance.budget.save()
            
        messages.success(self.request, f'Approval decision for "{form.instance.budget.name}" updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('budget:approval_list')

# Budget Revision Views
class BudgetRevisionListView(LoginRequiredMixin, ListView):
    model = BudgetRevision
    template_name = 'budget/revision_list.html'
    context_object_name = 'revisions'
    paginate_by = 25

    def get_queryset(self):
        return BudgetRevision.objects.select_related('budget', 'requested_by', 'approved_by').order_by('-created_at')

class BudgetRevisionCreateView(LoginRequiredMixin, CreateView):
    model = BudgetRevision
    template_name = 'budget/revision_form.html'
    fields = ['budget', 'revision_type', 'reason', 'new_amount', 'new_end_date']

    def form_valid(self, form):
        form.instance.requested_by = self.request.user
        form.instance.previous_amount = form.instance.budget.total_amount
        if form.instance.budget.period_end:
            form.instance.previous_end_date = form.instance.budget.period_end
            
        messages.success(self.request, f'Budget revision for "{form.instance.budget.name}" submitted successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('budget:revision_list')

class BudgetRevisionUpdateView(LoginRequiredMixin, UpdateView):
    model = BudgetRevision
    template_name = 'budget/revision_approval_form.html'
    fields = ['approved']

    def form_valid(self, form):
        if form.instance.approved:
            form.instance.approved_by = self.request.user
            form.instance.approved_date = timezone.now()
            
            # Apply the revision to the budget
            budget = form.instance.budget
            if form.instance.revision_type in ['increase', 'decrease']:
                budget.total_amount = form.instance.new_amount
            if form.instance.new_end_date:
                budget.period_end = form.instance.new_end_date
            budget.save()
            
        messages.success(self.request, f'Budget revision decision updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('budget:revision_list')

# Expense Request Views (Enhanced)
class ExpenseRequestListView(LoginRequiredMixin, ListView):
    model = ExpenseRequest
    template_name = 'budget/expense_request_list.html'
    context_object_name = 'expense_requests'
    paginate_by = 20

    def get_queryset(self):
        queryset = ExpenseRequest.objects.select_related('budget', 'budget_category', 'requested_by', 'approved_by', 'project')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset.order_by('-created_at')

class ExpenseRequestCreateView(LoginRequiredMixin, CreateView):
    model = ExpenseRequest
    template_name = 'budget/expense_request_form.html'
    fields = ['title', 'description', 'expense_type', 'requested_amount', 'budget', 'budget_category', 'project', 'vendor_name', 'vendor_contact', 'required_date', 'supporting_documents']

    def form_valid(self, form):
        form.instance.requested_by = self.request.user
        messages.success(self.request, f'Expense request "{form.instance.title}" submitted successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('budget:expense_request_list')

class ExpenseRequestUpdateView(LoginRequiredMixin, UpdateView):
    model = ExpenseRequest
    template_name = 'budget/expense_request_form.html'
    fields = ['title', 'description', 'expense_type', 'requested_amount', 'budget', 'budget_category', 'project', 'vendor_name', 'vendor_contact', 'required_date', 'supporting_documents']

    def form_valid(self, form):
        messages.success(self.request, f'Expense request "{form.instance.title}" updated successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('budget:expense_request_list')

class ExpenseRequestApprovalView(LoginRequiredMixin, UpdateView):
    model = ExpenseRequest
    template_name = 'budget/expense_request_approval.html'
    fields = ['status', 'approved_amount']

    def form_valid(self, form):
        if form.instance.status == 'approved':
            form.instance.approved_by = self.request.user
            form.instance.approved_date = timezone.now()
            
        messages.success(self.request, f'Expense request "{form.instance.title}" {form.instance.status}.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('budget:expense_request_list')

# Budget Report Views
class BudgetReportListView(LoginRequiredMixin, ListView):
    model = BudgetReport
    template_name = 'budget/report_list.html'
    context_object_name = 'reports'
    paginate_by = 25

class BudgetReportCreateView(LoginRequiredMixin, CreateView):
    model = BudgetReport
    template_name = 'budget/report_form.html'
    fields = ['name', 'report_type', 'period_start', 'period_end', 'budgets', 'departments']

    def form_valid(self, form):
        form.instance.generated_by = self.request.user
        messages.success(self.request, f'Budget report "{form.instance.name}" created successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('budget:report_list')
