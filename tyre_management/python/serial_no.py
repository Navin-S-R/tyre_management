import frappe
from frappe.model.naming import parse_naming_series
import time

def validate_serial_no(doc,event):
	if doc.item_group.lower() in ['tires','tyres','tire','tyre']:
		if not doc.erp_serial_no:
			ym = time.strftime("%y%m")
			abbr = frappe.get_cached_value('Company',  doc.company,  'abbr')
			doc.erp_serial_no = parse_naming_series(f'Tyre-{abbr}-{ym}-.#####')