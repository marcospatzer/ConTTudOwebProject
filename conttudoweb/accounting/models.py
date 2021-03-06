import enum
from copy import deepcopy

from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.timezone import now

from conttudoweb.accounting.utils import get_due_date, AccountFrequencys, years_in_future_for_recurrence


class Category(models.Model):
    description = models.CharField('descrição', max_length=255)

    def __str__(self):
        return self.description

    class Meta:
        verbose_name = 'categoria'
        ordering = ['description']


class Bank(models.Model):
    code = models.CharField('código', max_length=5, unique=True)
    description = models.CharField('descrição', max_length=255)

    def __str__(self):
        return "{0} - {1}".format(self.code, self.description)

    class Meta:
        verbose_name = 'banco'
        ordering = ('code',)


class DepositAccount(models.Model):
    class DepositAccountTypes(enum.Enum):
        current_account = 'cur'
        money = 'mon'
        investment = 'inv'

    # entity = models.ForeignKey('core.Entity', on_delete=models.CASCADE)

    type = models.CharField('tipo', max_length=3, default=DepositAccountTypes.current_account.value, choices=[
        (DepositAccountTypes.current_account.value, 'Conta corrente'),
        (DepositAccountTypes.money.value, 'Dinheiro'),
        (DepositAccountTypes.investment.value, 'Conta de investimento'),
    ])
    bank = models.ForeignKey('Bank', on_delete=models.CASCADE, null=True, blank=True,
                             help_text="Obrigatório quando o tipo é 'Conta corrente'.",
                             verbose_name=Bank._meta.verbose_name)
    agency_number = models.CharField('número da agência', max_length=30, null=True, blank=True)
    agency_digit = models.CharField('dígito da agência', max_length=2, null=True, blank=True)
    account_number = models.CharField('número da conta', max_length=30, null=True, blank=True)
    account_digit = models.CharField('dígito da conta', max_length=2, null=True, blank=True)

    name = models.CharField('nome da conta', max_length=30)

    def __str__(self):
        return self.name

    def clean(self):
        # Quanto o tipo for "Conta corrente" deve obrigar a preencher o banco.
        if self.type == self.DepositAccountTypes.current_account.value and self.bank is None:
            raise ValidationError({'bank': [
                'O "' + self._meta.get_field('bank').verbose_name +
                '" deve ser preenchido quando o "Tipo" for "Conta corrente"!',
            ]})
        # Quando o tipo não é "Conta corrente" o banco não deve estar preenchido.
        if self.type != self.DepositAccountTypes.current_account.value:
            self.bank = None
            self.agency_number = None
            self.agency_digit = None
            self.account_number = None
            self.account_digit = None

    class Meta:
        verbose_name = 'conta financeira'
        verbose_name_plural = 'contas financeiras'


class ClassificationCenter(models.Model):
    # entity = models.ForeignKey('core.Entity', on_delete=models.CASCADE)
    name = models.CharField('nome', max_length=30, unique=True)
    cost_center = models.BooleanField('centro de custo', default=False)
    revenue_center = models.BooleanField('centro de receita', default=False)

    def is_cost_center(self):
        return self.cost_center

    def is_revenue_center(self):
        return self.revenue_center

    def __str__(self):
        return self.name

    def clean(self):
        # Ao menos uma das opções deve ser escolhida! "centro de custo" ou "centro de receita"
        if self.cost_center is False and self.revenue_center is False:
            _msg_error = 'Ao menos uma das opções deve ser escolhida. "Centro de custo" ou "Centro de receita"'
            raise ValidationError({
                'cost_center': [_msg_error],
                'revenue_center': [_msg_error]
            })

    class Meta:
        verbose_name = 'centro de custo/receita'
        verbose_name_plural = 'centros de custo/receita'


class Recurrence(models.Model):
    # Está é a data final cuja a recorrência foi gerada
    date = models.DateField(auto_now_add=True)
    original_date_day = models.IntegerField(null=True)
    # entity = models.ForeignKey('core.Entity', on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if AccountPayable.objects.filter(recurrence_key=self).exists() or AccountReceivables.objects.filter(recurrence_key=self).exists():
            if AccountPayable.objects.filter(recurrence_key=self).exists():
                last = AccountPayable.objects.filter(recurrence_key=self).order_by('-recurrence_count').first()
            else:
                last = AccountReceivables.objects.filter(recurrence_key=self).order_by('-recurrence_count').first()

            if self.date > last.due_date:
                due_date = last.due_date
                recurrence_count = last.recurrence_count
                while True:
                    if due_date > self.date:
                        break
                    else:
                        due_date = get_due_date(due_date, last.frequency, day=self.original_date_day)
                        recurrence_count += recurrence_count
                        new_instance = deepcopy(last)
                        new_instance.id = None
                        new_instance.recurrence_count = recurrence_count
                        new_instance.due_date = due_date
                        new_instance.save()


class Account(models.Model):
    class AccountTypes(enum.Enum):
        normal = 'nor'
        recurrent = 'rec'
        parcelled = 'par'

    # entity = models.ForeignKey('core.Entity', on_delete=models.CASCADE)
    document = models.CharField('documento', max_length=60, null=True, blank=True)
    description = models.CharField('descrição', max_length=255)
    amount = models.DecimalField('valor', max_digits=15, decimal_places=2)
    due_date = models.DateField('data de vencimento')
    recurrence_key = models.ForeignKey('Recurrence', on_delete=models.PROTECT, null=True, blank=True, editable=False)
    recurrence_count = models.IntegerField(null=True, blank=True, editable=False)
    type = models.CharField('tipo', max_length=3, default=AccountTypes.normal.value,
                            help_text="<a href='#' title='"
                                      "Contas normais vencem apenas uma vez. \n"
                                      "Contas recorrentes vencem uma vez por período indefinidamente. \n"
                                      "Contas parceladas têm um número fixo de vencimentos pré-estipulado.'>?</a>",
                            choices=[
                                (AccountTypes.normal.value, 'Normal'),
                                (AccountTypes.recurrent.value, 'Recorrente'),
                                (AccountTypes.parcelled.value, 'Parcelada'),
                            ])
    frequency = models.CharField('frequência', max_length=15, null=True, blank=True,
                                 help_text="Obrigatório quando o tipo é 'Recorrente'.",
                                 choices=[
                                     (AccountFrequencys.weekly.value, 'Semanal'),
                                     (AccountFrequencys.biweekly.value, 'Quinzenal'),
                                     (AccountFrequencys.monthly.value, 'Mensal'),
                                     (AccountFrequencys.bimonthly.value, 'Bimestral'),
                                     (AccountFrequencys.quarterly.value, 'Trimestral'),
                                     (AccountFrequencys.semiannual.value, 'Semestral'),
                                     (AccountFrequencys.annual.value, 'Anual'),
                                 ])
    number_of_parcels = models.PositiveIntegerField('número de parcelas', null=True, blank=True,
                                                    help_text="Obrigatório caso o tipo seja 'Parcelada'.", )
    parcel = models.PositiveIntegerField(null=True, blank=True, editable=False)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, null=True, blank=True,
                                 verbose_name=Category._meta.verbose_name)
    document_emission_date = models.DateField('data de emissão', null=True, blank=True)
    expected_deposit_account = models.ForeignKey('DepositAccount', on_delete=models.CASCADE, null=True, blank=True)
    observation = models.TextField('observação', null=True, blank=True)
    parent = models.IntegerField(null=True, blank=True, editable=False)
    reconciled = models.BooleanField('conciliado', default=False)

    __original_description = None

    def __str__(self):
        if self.type == self.AccountTypes.parcelled.value:
            return "{} - {}/{}".format(self.description, str(self.parcel), str(self.number_of_parcels))
        else:
            return self.description

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_description = self.description

    def clean(self):
        # Quanto o tipo for "Recorrente" deve obrigar a preencher a frequência.
        if self.type != self.AccountTypes.normal.value and self.frequency is None:
            raise ValidationError({'frequency': [
                'A "Frequência" deve ser preenchida quando o "Tipo" for diferente de "Normal"!',
            ]})
        # Quando o tipo é "Normal" a frequência não deve estar preenchida.
        if self.type == self.AccountTypes.normal.value and self.frequency is not None:
            self.frequency = None

        # Quanto o tipo for "Parcelada" deve obrigar a preencher o número de parcelas.
        if self.type == self.AccountTypes.parcelled.value and self.number_of_parcels is None:
            raise ValidationError({'number_of_parcels': [
                'O "Número de Parcelas" deve ser preenchido quando o "Tipo" for "Parcelada"!',
            ]})
        # Quando o tipo não é "Parcelada" o número de parcelas não deve estar preenchido.
        if self.type != self.AccountTypes.parcelled.value and self.number_of_parcels is not None:
            self.number_of_parcels = None
        # Quando o tipo é "Normal" o parent não deve estar preenchido.
        if self.type == self.AccountTypes.normal.value and self.parent is not None:
            self.parent = None

    def save(self, *args, **kwargs):
        super(Account, self).save(*args, **kwargs)

        if self.type == self.AccountTypes.parcelled.value and self.parent is None:
            self.parent = self.pk
            self.parcel = 1
            self.save()

            x = self.parcel + 1
            while x <= self.number_of_parcels:
                from copy import deepcopy
                new_instance = deepcopy(self)
                new_instance.id = None
                new_instance.parcel = x
                new_instance.due_date = get_due_date(self.due_date, self.frequency, parcel=x)
                new_instance.save()
                x += 1

        if self.type == self.AccountTypes.recurrent.value:
            if self.recurrence_key is None:
                # recur = Recurrence.objects.create(entity=self.entity, original_date_day=self.due_date.day)
                recur = Recurrence.objects.create(original_date_day=self.due_date.day)
                self.recurrence_key = recur
                self.recurrence_count = 1
                self.save()
                self.recurrence_key.date = now().date() + relativedelta(years=years_in_future_for_recurrence)
                self.recurrence_key.save()
            else:
                if self.description != self.__original_description:
                    self._meta.model.objects.filter(recurrence_key=self.recurrence_key, recurrence_count__gt=self.recurrence_count, liquidated=False).update(description=self.description)

                date_max = now().date() + relativedelta(years=years_in_future_for_recurrence)
                if self.recurrence_key.date < date_max:
                    self.recurrence_key.date = date_max
                    self.recurrence_key.save()

        # super(Account, self).save(*args, **kwargs)

    class Meta:
        abstract = True


class AccountPayable(Account):
    person = models.ForeignKey('core.People', on_delete=models.CASCADE, null=True, blank=True,
                               verbose_name='fornecedor', limit_choices_to={'supplier': True})
    classification_center = models.ForeignKey('ClassificationCenter', on_delete=models.CASCADE, null=True, blank=True,
                                              verbose_name='classificação', limit_choices_to={'cost_center': True})
    liquidated = models.BooleanField('pago?', default=False)

    class Meta:
        verbose_name = 'conta à pagar'
        verbose_name_plural = 'contas à pagar'


class AccountReceivables(Account):
    person = models.ForeignKey('core.People', on_delete=models.CASCADE, null=True, blank=True,
                               verbose_name='cliente', limit_choices_to={'customer': True})
    classification_center = models.ForeignKey('ClassificationCenter', on_delete=models.CASCADE, null=True, blank=True,
                                              verbose_name='classificação', limit_choices_to={'revenue_center': True})
    liquidated = models.BooleanField('recebido?', default=False)

    class Meta:
        verbose_name = 'conta à receber'
        verbose_name_plural = 'contas à receber'
