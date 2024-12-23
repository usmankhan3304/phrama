import logging
from celery import shared_task
from scraper.models import *
from .models import ConsolidatedDrugData, ConsolidatedDrugPrice
from django.db.models import Min, Max, Case, When
# Set up logging
logger = logging.getLogger(__name__)

@shared_task
def populate_consolidated_table():
    logger.info("Starting to populate the consolidated table.")

    # Populate from FSSDrug
    fss_drugs = FSSDrug.objects.all()
    logger.info(f"Found {fss_drugs.count()} FSSDrug records to process.")

    for drug in fss_drugs:
        try:
            # Get all related pricing records for the drug
            pricings = FSSPricing.objects.filter(drug=drug)

            price_ranges = pricings.aggregate(
            fss_min_price=Min(Case(When(price_type='FSS', then='price'))),
            fss_max_price=Max(Case(When(price_type='FSS', then='price'))),
            nc_min_price=Min(Case(When(price_type='NC', then='price'))),
            nc_max_price=Max(Case(When(price_type='NC', then='price'))),
            big4_min_price=Min(Case(When(price_type='Big4', then='price'))),
            big4_max_price=Max(Case(When(price_type='Big4', then='price')))
    )

            consolidated_drug, created = ConsolidatedDrugData.objects.update_or_create(
                ndc_code=drug.ndc_with_dashes,
                defaults={
                    'trade_name': drug.trade_name,
                    'generic_name': drug.generic_name,
                    'package_description': drug.package_description,
                    'dosage_form': drug.dosage_form,
                    'strength': drug.strength,
                    'route': drug.route,
                    'ingredient': drug.ingredient,
                    'covered': drug.covered,
                    'prime_vendor': drug.prime_vendor,
                    'va_class': drug.va_class,
                    
                    'vendor_name': drug.vendor.vendor_name if drug.vendor else None,
                    'contract_number': drug.contract.contract_number,
                    'contract_awardee': drug.contract.awardee,
                    'contract_awarded_value': drug.contract.awarded_value,
                    'contract_start_date': drug.contract.contract_start_date,
                    'contract_stop_date': drug.contract.contract_stop_date,
                    
                    'manufactured_by': drug.manufactured_by.name if drug.manufactured_by else None,
                    'manufactured_by_address': drug.manufactured_by.address if drug.manufactured_by else None,
                    'manufactured_for': drug.manufactured_for.name if drug.manufactured_for else None,
                    'distributed_by': drug.distributed_by.name if drug.distributed_by else None,
                    'notes': drug.notes,
                    'source': 'VA',

                    # Insert the min/max prices for each price type
                    'min_fss_price':  price_ranges['fss_min_price'],
                    'max_fss_price':  price_ranges['fss_max_price'],
                    'min_nc_price':  price_ranges['nc_min_price'],
                    'max_nc_price':  price_ranges['nc_max_price'],
                    'min_big4_price':  price_ranges['big4_min_price'],
                    'max_big4_price':  price_ranges['big4_max_price'],
                }
            )
            action = "Created" if created else "Updated"
            logger.info(f"{action} ConsolidatedDrugData for NDC {drug.ndc_with_dashes} from FSSDrug.")

            # Now populate the related prices
            for price in pricings:
                ConsolidatedDrugPrice.objects.update_or_create(
                    drug=consolidated_drug,
                    price=price.price,
                    price_start_date=price.price_start_date,
                    price_stop_date=price.price_stop_date,
                    price_type=price.price_type,
                    defaults={
                        'non_taa_compliance': price.non_taa_compliance,
                    }
                )
                logger.info(f"Updated price for NDC {drug.ndc_with_dashes} with price {price.price}.")
        except Exception as e:
            logger.error(f"Error processing FSSDrug with NDC {drug.ndc_with_dashes}: {e}")

    # Populate from FOIAUniqueNDCData
    foia_drugs = FOIAUniqueNDCData.objects.all()
    logger.info(f"Found {foia_drugs.count()} FOIAUniqueNDCData records to process.")

    for foia in foia_drugs:
        try:
            consolidated_drug, created = ConsolidatedDrugData.objects.update_or_create(
                ndc_code=foia.ndc_code,
                defaults={
                    'description': foia.description,
                    'dosage_form': foia.dosage_form,
                    'strength': foia.strength,
                    'ingredient': foia.ingredient,
                    'total_quantity_purchased': foia.total_quantity_purchased,
                    'total_publishable_dollars_spent': foia.total_publishable_dollars_spent,
                    'manufactured_by': foia.manufactured_by.name if foia.manufactured_by else None,
                    'manufactured_for': foia.manufactured_for.name if foia.manufactured_for else None,
                    'distributed_by': foia.distributed_by.name if foia.distributed_by else None,
                    'notes': foia.notes,
                    'source': 'FOIA'
                }
            )
            logger.info(f"Updated ConsolidatedDrugData for NDC {foia.ndc_code} from FOIAUniqueNDCData.")
        except Exception as e:
            logger.error(f"Error processing FOIAUniqueNDCData with NDC {foia.ndc_code}: {e}")

    # Populate from DODDrugData
    dod_drugs = DODDrugData.objects.all()
    logger.info(f"Found {dod_drugs.count()} DODDrugData records to process.")

    for dod in dod_drugs:
        try:
            consolidated_drug, created = ConsolidatedDrugData.objects.update_or_create(
                ndc_code=dod.ndc_code,
                defaults={
                    'source': 'DOD'
                }
            )
            action = "Created" if created else "Updated"
            logger.info(f"{action} ConsolidatedDrugData for NDC {dod.ndc_code} from DODDrugData.")

            # Now populate the related prices
            ConsolidatedDrugPrice.objects.update_or_create(
                drug=consolidated_drug,
                price=dod.price,
                price_start_date=None,  # Assuming there's no start date for DOD prices
                price_stop_date=None,   # Assuming there's no stop date for DOD prices
                price_type= None,       # Assuming DOD has a distinct price type
                defaults={
                    'non_taa_compliance': None,  # Assuming no non-TAA compliance info for DOD
                }
            )
            logger.info(f"Updated price for NDC {dod.ndc_code} with price {dod.price}.")
        except Exception as e:
            logger.error(f"Error processing DODDrugData with NDC {dod.ndc_code}: {e}")

    logger.info("Consolidated table populated successfully.")