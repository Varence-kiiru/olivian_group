from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count, Avg, Q, F
from django.db import models
from .models import Activity, Opportunity, Company, Lead
import logging

logger = logging.getLogger(__name__)

class ReportGenerator:
    def __init__(self, start_date=None, end_date=None, user=None):
        self.end_date = end_date or timezone.now()
        self.start_date = start_date or (self.end_date - timedelta(days=30))
        self.user = user

    def get_date_range_filter(self):
        return Q(created_at__range=[self.start_date, self.end_date])

    def safe_aggregate(self, queryset, operation, field, default=0):
        try:
            result = queryset.aggregate(value=operation(field))
            return result['value'] or default
        except Exception as e:
            logger.error(f"Error in aggregation: {str(e)}")
            return default

class ActivityReport(ReportGenerator):
    def generate(self):
        try:
            activities = Activity.objects.filter(
                scheduled_datetime__range=[self.start_date, self.end_date]
            )
            if self.user:
                activities = activities.filter(assigned_to=self.user)

            # Get activity types safely
            activity_types = activities.values('activity_type').annotate(
                count=Count('id'),
                completed_count=Count('id', filter=Q(status='completed'))
            )

            # Calculate completion rates safely
            by_type = []
            for activity_type in activity_types:
                total = activity_type['count']
                completed = activity_type['completed_count']
                completion_rate = (completed / total * 100) if total > 0 else 0
                by_type.append({
                    'activity_type': activity_type['activity_type'],
                    'count': total,
                    'completion_rate': completion_rate
                })

            return {
                'total_activities': activities.count(),
                'by_type': by_type,
                'by_status': list(activities.values('status').annotate(count=Count('id'))),
                'recent_activities': list(activities.order_by('-scheduled_datetime')[:10].values(
                    'subject', 'activity_type', 'status', 'scheduled_datetime'
                ))
            }
        except Exception as e:
            logger.error(f"Error generating activity report: {str(e)}")
            raise

class PipelineReport(ReportGenerator):
    def generate(self):
        try:
            opportunities = Opportunity.objects.filter(
                created_at__range=[self.start_date, self.end_date]
            )
            if self.user:
                opportunities = opportunities.filter(assigned_to=self.user)

            # Calculate stage data with separate queries
            stages_data = []
            for stage_code, stage_name in Opportunity.STAGE_CHOICES:
                stage_opps = opportunities.filter(stage=stage_code)
                stage_data = {
                    'stage': stage_code,
                    'count': stage_opps.count(),
                    'value': float(stage_opps.aggregate(Sum('value'))['value__sum'] or 0),
                    'weighted_value': float(sum(
                        opp.value * opp.probability / 100.0 
                        for opp in stage_opps
                    ))
                }
                stages_data.append(stage_data)

            # Calculate totals
            total_value = sum(stage['value'] for stage in stages_data)
            total_count = sum(stage['count'] for stage in stages_data)

            return {
                'total_value': total_value,
                'by_stage': stages_data,
                'conversion_rate': self.calculate_conversion_rate(opportunities),
                'avg_deal_size': total_value / total_count if total_count > 0 else 0
            }

        except Exception as e:
            logger.error(f"Error generating pipeline report: {str(e)}", exc_info=True)
            return {
                'total_value': 0,
                'by_stage': [],
                'conversion_rate': 0,
                'avg_deal_size': 0
            }

    def calculate_conversion_rate(self, opportunities):
        try:
            total = opportunities.count()
            if total == 0:
                return 0
            won = opportunities.filter(stage='closed_won').count()
            return round((won / total) * 100, 2)
        except Exception as e:
            logger.error(f"Error calculating conversion rate: {str(e)}")
            return 0

class RevenueReport(ReportGenerator):
    def generate(self):
        try:
            opportunities = Opportunity.objects.filter(
                stage='closed_won',
                actual_close_date__range=[self.start_date, self.end_date]
            )
            if self.user:
                opportunities = opportunities.filter(assigned_to=self.user)
            
            return {
                'total_revenue': self.safe_aggregate(opportunities, Sum, 'value'),
                'by_month': list(self.get_monthly_revenue(opportunities)),
                'by_product_type': list(opportunities.values(
                    'lead__system_type'
                ).annotate(
                    revenue=Sum('value', default=0),
                    count=Count('id')
                )),
                'top_customers': list(self.get_top_customers(opportunities))
            }
        except Exception as e:
            logger.error(f"Error generating revenue report: {str(e)}")
            raise

    def get_monthly_revenue(self, opportunities):
        return opportunities.annotate(
            month=models.functions.ExtractMonth('actual_close_date')
        ).values('month').annotate(
            revenue=Sum('value', default=0),
            deals=Count('id')
        ).order_by('month')

    def get_top_customers(self, opportunities):
        return opportunities.values(
            'company__name'
        ).annotate(
            revenue=Sum('value', default=0),
            deals=Count('id')
        ).order_by('-revenue')[:5]

class CustomerReport(ReportGenerator):
    def generate(self):
        try:
            customers = Company.objects.filter(
                created_at__range=[self.start_date, self.end_date]
            )
            
            return {
                'total_customers': customers.count(),
                'new_customers': self.get_new_customers_count(),
                'customer_segments': list(self.get_customer_segments()),
                'retention_rate': self.calculate_retention_rate(),
                'customer_lifetime_value': self.calculate_customer_ltv()
            }
        except Exception as e:
            logger.error(f"Error generating customer report: {str(e)}")
            raise

    def get_new_customers_count(self):
        try:
            return Company.objects.filter(
                created_at__range=[self.start_date, self.end_date]
            ).count()
        except Exception as e:
            logger.error(f"Error getting new customers count: {str(e)}")
            return 0

    def get_customer_segments(self):
        try:
            return Company.objects.values(
                'company_type'
            ).annotate(
                count=Count('id'),
                total_revenue=Sum('opportunities__value', 
                    filter=Q(opportunities__stage='closed_won'),
                    default=0
                )
            )
        except Exception as e:
            logger.error(f"Error getting customer segments: {str(e)}")
            return []

    def calculate_retention_rate(self):
        try:
            start_customers = Company.objects.filter(
                created_at__lt=self.start_date
            ).count()
            
            if start_customers == 0:
                return 0
                
            retained = Company.objects.filter(
                created_at__lt=self.start_date,
                opportunities__actual_close_date__gte=self.start_date
            ).distinct().count()
            
            return (retained / start_customers * 100)
        except Exception as e:
            logger.error(f"Error calculating retention rate: {str(e)}")
            return 0

    def calculate_customer_ltv(self):
        try:
            return self.safe_aggregate(
                Opportunity.objects.filter(stage='closed_won'),
                Avg,
                'value'
            )
        except Exception as e:
            logger.error(f"Error calculating customer LTV: {str(e)}")
            return 0