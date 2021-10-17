from django.db.models.signals import post_save
from django.dispatch import receiver

from bar.models import RegularInventoryRecordsTrunk, RegularInventoryRecordBroken, TequilaInventoryRecordsTrunk, \
    TequilaInventoryRecordBroken
from core.models import Item


@receiver(post_save, sender=Item)
def create_inventory_trunk(sender, instance, created, **kwargs):
    if created:
        if instance.item_for == "bar" and not instance.tequila:
            RegularInventoryRecordsTrunk.objects.create(item=instance)
        elif instance.item_for == "bar" and instance.tequila:
            TequilaInventoryRecordsTrunk.objects.create(item=instance)
        # elif instance.item_for == "restaurant":
        #     pass


@receiver(post_save, sender=RegularInventoryRecordBroken)
def deduct_regular_inventory_record_on_broken_items(sender, instance, created, **kwargs):
    if created:
        regular_inventory_record = instance.regular_inventory_record
        regular_inventory_record.available_quantity = regular_inventory_record.available_quantity - instance.quantity_broken
        regular_inventory_record.save()
        if regular_inventory_record.available_quantity <= 0:
            regular_inventory_record.stock_status = "unavailable"
            regular_inventory_record.save()


@receiver(post_save, sender=TequilaInventoryRecordBroken)
def deduct_tequila_inventory_record_on_broken_items(sender, instance, created, **kwargs):
    if created:
        tequila_inventory_record = instance.tequila_inventory_record
        tequila_inventory_record.available_quantity = tequila_inventory_record.available_quantity - instance.quantity_broken
        tequila_inventory_record.save()
        if tequila_inventory_record.available_quantity <= 0:
            tequila_inventory_record.stock_status = "unavailable"
            tequila_inventory_record.save()
