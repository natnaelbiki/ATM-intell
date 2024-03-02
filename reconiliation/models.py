from django.conf import settings
from django.db import models

class FinancialReportManager(models.Manager):
    def cbe(self):
        """Return queryset of FinancialReport instances where bank is 'CBE'."""
        return self.filter(bank='CBE')

    def other(self):
        """Return queryset of FinancialReport instances where bank is 'Other'."""
        return self.filter(bank='Other')

class FinancialReport(models.Model):
    BANK_CHOICES = (
        ('CBE', 'CBE'),
        ('OTHER', 'Other'),
    )
    
    TERMINAL_ID = models.CharField(max_length=100)
    CARD_NUMBER = models.CharField(max_length=16)
    FROM_ACCOUNT_NO = models.CharField(max_length=20)
    REQUESTED_AMOUNT = models.DecimalField(max_digits=10, decimal_places=2)
    BUSINESS_DATE = models.DateField()
    TRXN_TIME = models.TimeField()
    STATUS = models.CharField(max_length=100)
    bank = models.CharField(max_length=5, choices=BANK_CHOICES, default='CBE')
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='financial_reports')

    
    # Default manager
    objects = models.Manager()
    # Custom manager
    filtered_by_bank = FinancialReportManager()


    def __str__(self):
        return self.TERMINAL_ID



    @classmethod
    def create_cbe_instance(cls, **kwargs):
        kwargs['bank'] = 'CBE'
        return cls.objects.create(**kwargs)

    @classmethod
    def create_other_instance(cls, **kwargs):
        kwargs['bank'] = 'Other'
        return cls.objects.create(**kwargs)


class ActivityReportManager(models.Manager):
    def cbe(self):
        """Return queryset of FinancialReport instances where bank is 'CBE'."""
        return self.filter(bank='CBE')

    def other(self):
        """Return queryset of FinancialReport instances where bank is 'Other'."""
        return self.filter(bank='OTHER')

class ActivtyReport(models.Model):
    BANK_CHOICES = (
        ('CBE', 'CBE'),
        ('OTHER', 'Other'),
    )
    
    ATM_BR_NUMBER = models.CharField(max_length=100)
    PAN = models.CharField(max_length=16)
    DR_ACCT = models.CharField(max_length=20)
    TXN_AMOUNT = models.DecimalField(max_digits=10, decimal_places=2)
    TXN_DATE = models.DateField()
    TXN_TIME = models.TimeField()
    bank = models.CharField(max_length=5, choices=BANK_CHOICES, default='CBE')
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activity_reports')

    
    # Default manager
    objects = models.Manager()

    # filter
    filtered_by_bank = ActivityReportManager()


    def __str__(self):
        return self.ATM_BR_NUMBER

    @classmethod
    def create_cbe_instance(cls, **kwargs):
        kwargs['bank'] = 'CBE'
        return cls.objects.create(**kwargs)

    @classmethod
    def create_other_instance(cls, **kwargs):
        kwargs['bank'] = 'OTHER'
        return cls.objects.create(**kwargs)


    