import operator

from django.test import TestCase

from .models import FillingRequirement, ColumnRule


# Create your tests here.
class FillingRequirementModelTests(TestCase):

    def test_can_do_it(self):
        fr = FillingRequirement.objects.get(pk=4909971267584)
        column_rule_list = ColumnRule.objects.filter(filling_requirement_id__exact=fr.id)
        for column_rule in sorted(column_rule_list, key=operator.attrgetter('rule.fill_order')):
            print(column_rule.column_name)
            print(column_rule.rule.fill_order)

        self.assertIsNotNone(fr)
