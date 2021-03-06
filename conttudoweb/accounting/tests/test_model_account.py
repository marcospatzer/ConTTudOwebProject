from django.test import TestCase
import datetime

from ..models import Account
# from ...core.tests.test_model_entity import get_or_create_entity


def create_account(_description, **kwargs):
    account = {
        # 'entity': get_or_create_entity(),
        'document': None,
        'description': _description,
        'amount': 0.01,
        'due_date': datetime.date.today(),
        'type': Account.AccountTypes.normal.value,
        'frequency': None,
        'number_of_parcels': None,
        'parcel': None,
        'category': None,
        'document_emission_date': None,
        'expected_deposit_account_id': None,
        'person': None,
        'classification_center': None,
        'observation': None,
        'parent': None
    }
    return dict(account, **kwargs)


class AccountAdminTest:
    exclude = ('entity',)
