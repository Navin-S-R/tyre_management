import frappe
from frappe.model.naming import parse_naming_series
import time

def validate_serial_no(doc,event):
	if doc.item_group.lower() in ['tires','tyres','tire','tyre']:
		if not doc.erp_serial_no:
			ym = time.strftime("%y%m")
			abbr = frappe.get_cached_value('Company',  doc.company,  'abbr')
			doc.erp_serial_no = parse_naming_series(f'Tyre-{abbr}-{ym}-.#####')
			doc.tyre_size = frappe.db.get_value("Item",{"name":doc.item_code},"tyre_size")

def update_outgoing_rate():
	serial_no_list =frappe.get_all("Serial No",{"invoiced_rate":0,"sales_invoice":['not in',None]},['name','sales_invoice','item_code'])
	for serial in serial_no_list:
		item_details = frappe.db.get_value("Sales Invoice Item",{"parent":serial.get('sales_invoice'),"item_code":serial.get('item_code')},['rate','serial_no'],as_dict=True)
		serial_numbers = item_details['serial_no'].split('\n')
		serial_numbers = [serial.strip() for serial in serial_numbers if serial.strip()]
		if serial['name'] in serial_numbers and item_details['rate']:
			frappe.db.sql("UPDATE `tabSerial No` SET invoiced_rate = {0} WHERE name = '{1}'".format(item_details['rate'], serial['name']))
