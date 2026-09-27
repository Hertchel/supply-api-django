# use this code to delete certain data from the database
# make sure to add comment to newly added delete method

from django.core.management.base import BaseCommand
from django.db import transaction

from api.models import (
    StockItems,
    ICSItem,
    InventoryCustodianSlip,
    DeliveredItems,
    InspectionAndAcceptance,
    PurchaseOrderItem,
    PurchaseOrder,
    SupplierItem,
    Supplier,
    Bidding,
    AbstractOfQuotation,
    ItemQuotation,
    RequestForQuotation,
    TrackStatus,
    Item,
    PurchaseRequest,
    SupplierProfile,
)


class Command(BaseCommand):
    help = "Delete test data while preserving AOQ 2026-08-0002."

    @transaction.atomic
    def handle(self, *args, **options):

        # AOQ that must be preserved.
        KEEP_AOQ = "2026-08-0002"

        # ---------------------------------------------------------
        # Find the AOQ that must be preserved.
        # ---------------------------------------------------------
        try:
            keep_aoq = AbstractOfQuotation.objects.get(
                aoq_no=KEEP_AOQ
            )
        except AbstractOfQuotation.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f"AOQ {KEEP_AOQ} was not found."
                )
            )
            return

        # Get the Purchase Request belonging to the preserved AOQ.
        keep_pr = keep_aoq.purchase_request

        self.stdout.write(
            self.style.WARNING(
                f"Preserving AOQ: {KEEP_AOQ}"
            )
        )

        self.stdout.write(
            self.style.WARNING(
                f"Preserving PR: {keep_pr.pr_no}"
            )
        )

        # ---------------------------------------------------------
        # Find the suppliers belonging to the preserved AOQ.
        #
        # These suppliers must also be preserved because they are
        # part of the AOQ transaction.
        # ---------------------------------------------------------
        keep_supplier_ids = Supplier.objects.filter(
            aoq=keep_aoq
        ).values_list(
            "supplier_no",
            flat=True
        )

        self.stdout.write(
            self.style.WARNING(
                f"Preserving suppliers: {keep_supplier_ids.count()}"
            )
        )

        # ---------------------------------------------------------
        # 1. Delete ICS items first.
        #
        # ICSItem.delivered_item uses PROTECT, so ICSItems must
        # be deleted before DeliveredItems.
        # ---------------------------------------------------------
        ICSItem.objects.exclude(
            ics__purchase_order__purchase_request=keep_pr
        ).delete()

        # ---------------------------------------------------------
        # 2. Delete Inventory Custodian Slips except those
        # belonging to the preserved Purchase Request.
        #
        # InventoryCustodianSlip.purchase_order uses PROTECT.
        # Therefore these must be removed before deleting POs.
        # ---------------------------------------------------------
        InventoryCustodianSlip.objects.exclude(
            purchase_order__purchase_request=keep_pr
        ).delete()

        # ---------------------------------------------------------
        # 3. Delete Delivered Items except those belonging
        # to the preserved Purchase Request.
        # ---------------------------------------------------------
        DeliveredItems.objects.exclude(
            purchase_request=keep_pr
        ).delete()

        # ---------------------------------------------------------
        # 4. Delete Stock Items except those belonging
        # to the preserved Purchase Request.
        # ---------------------------------------------------------
        StockItems.objects.exclude(
            inspection__purchase_request=keep_pr
        ).delete()

        # ---------------------------------------------------------
        # 5. Delete Inspections except those belonging
        # to the preserved Purchase Request.
        # ---------------------------------------------------------
        InspectionAndAcceptance.objects.exclude(
            purchase_request=keep_pr
        ).delete()

        # ---------------------------------------------------------
        # 6. Delete Purchase Order Items except those belonging
        # to the preserved Purchase Request.
        # ---------------------------------------------------------
        PurchaseOrderItem.objects.exclude(
            purchase_request=keep_pr
        ).delete()

        # ---------------------------------------------------------
        # 7. Delete Purchase Orders except those belonging
        # to the preserved Purchase Request.
        # ---------------------------------------------------------
        PurchaseOrder.objects.exclude(
            purchase_request=keep_pr
        ).delete()

        # ---------------------------------------------------------
        # 8. Delete Supplier Items except those belonging
        # to the preserved Purchase Request.
        # ---------------------------------------------------------
        SupplierItem.objects.exclude(
            rfq__purchase_request=keep_pr
        ).delete()

        # ---------------------------------------------------------
        # 9. Delete Bidding records except those belonging
        # to the preserved Purchase Request.
        # ---------------------------------------------------------
        Bidding.objects.exclude(
            purchase_request=keep_pr
        ).delete()

        # ---------------------------------------------------------
        # 10. Delete Suppliers except suppliers belonging
        # to the preserved AOQ.
        # ---------------------------------------------------------
        Supplier.objects.exclude(
            supplier_no__in=keep_supplier_ids
        ).delete()

        # ---------------------------------------------------------
        # 11. Delete Item Quotations except those belonging
        # to the preserved Purchase Request.
        # ---------------------------------------------------------
        ItemQuotation.objects.exclude(
            rfq__purchase_request=keep_pr
        ).delete()

        # ---------------------------------------------------------
        # 12. Delete RFQs except those belonging to the
        # preserved Purchase Request.
        # ---------------------------------------------------------
        RequestForQuotation.objects.exclude(
            purchase_request=keep_pr
        ).delete()

        # ---------------------------------------------------------
        # 13. Delete AOQs except the preserved AOQ.
        # ---------------------------------------------------------
        AbstractOfQuotation.objects.exclude(
            aoq_no=KEEP_AOQ
        ).delete()

        # ---------------------------------------------------------
        # 14. Delete Track Status records except those belonging
        # to the preserved Purchase Request.
        # ---------------------------------------------------------
        TrackStatus.objects.exclude(
            pr_no=keep_pr
        ).delete()

        # ---------------------------------------------------------
        # 15. Delete Items except those belonging to the
        # preserved Purchase Request.
        # ---------------------------------------------------------
        Item.objects.exclude(
            purchase_request=keep_pr
        ).delete()

        # ---------------------------------------------------------
        # 16. Delete Purchase Requests except the preserved PR.
        # ---------------------------------------------------------
        PurchaseRequest.objects.exclude(
            pr_no=keep_pr.pr_no
        ).delete()

        # ---------------------------------------------------------
        # 17. Delete Supplier Profiles that no longer have
        # any Supplier records.
        #
        # SupplierProfile is protected by Supplier using PROTECT,
        # so profiles still used by the preserved supplier will
        # remain untouched.
        # ---------------------------------------------------------
        SupplierProfile.objects.filter(
            supplier_records__isnull=True
        ).delete()

        # ---------------------------------------------------------
        # Cleanup completed.
        # ---------------------------------------------------------
        self.stdout.write(
            self.style.SUCCESS(
                "\nTest data cleanup completed successfully."
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Preserved AOQ: {KEEP_AOQ}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Preserved PR: {keep_pr.pr_no}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Preserved suppliers: {keep_supplier_ids.count()}"
            )
        )