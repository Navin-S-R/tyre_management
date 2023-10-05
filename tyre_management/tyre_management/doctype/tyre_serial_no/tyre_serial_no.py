# Copyright (c) 2023, Aerele and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import parse_naming_series
import time
import datetime
from frappe.utils import nowdate


class TyreSerialNo(Document):
	def validate(self):
		#Generate ERP Serial No
		if not self.erp_serial_no:
			item_details=frappe.db.get_value("Item",{"name":self.item_code},["tyre_size","is_smart_tyre"],as_dict=True)
			ym = time.strftime("%y%m")
			abbr = frappe.get_cached_value('Company',  self.company,  'abbr')
			self.erp_serial_no = parse_naming_series(f'Tyre-{abbr}-{ym}-.#####')
			self.tyre_size = item_details.get('tyre_size')
			self.is_smart_tyre = item_details.get('is_smart_tyre')

#update Selling Rate
def update_outgoing_rate():
	serial_no_list =frappe.get_all("Tyre Serial No",{"invoiced_rate":0,"sales_invoice":['not in',None]},['name','sales_invoice','item_code'])
	for serial in serial_no_list:
		item_details = frappe.db.get_value("Sales Invoice Item",{"parent":serial.get('sales_invoice'),"item_code":serial.get('item_code')},['rate','serial_no'],as_dict=True)
		serial_numbers = item_details['serial_no'].split('\n')
		serial_numbers = [serial.strip() for serial in serial_numbers if serial.strip()]
		if serial['name'] in serial_numbers and item_details['rate']:
			frappe.db.sql("UPDATE `tabTyre Serial No` SET invoiced_rate = {0} WHERE name = '{1}'".format(item_details['rate'], serial['name']))

#update Serial No
def update_field_from_serial_no():
	tyre_str_list=['tires','tyres','tire','tyre','Tires','Tyres','Tire','Tyre']
	time_change=datetime.timedelta(minutes=10)
	start_datetime=(datetime.datetime.now()-time_change)
	end_datetime = datetime.datetime.now()
	serial_doc_list = frappe.get_all("Serial No", {
		"item_group": ["in", tyre_str_list],
		"modified": [">=",start_datetime,"<=",end_datetime]
	}, pluck='name')
	for serial in serial_doc_list:
		serial_doc = frappe.get_doc("Serial No",{"name": serial})
		if frappe.db.exists("Tyre Serial No",{"name": serial}):
			tyre_serial_doc=frappe.get_doc("Tyre Serial No",{"name": serial})
			if tyre_serial_doc.enable_manual_change == 0:
				serial_doc=frappe.get_doc("Serial No",{"name":tyre_serial_doc.serial_no})
				serial_doc_fields = [field.fieldname for field in frappe.get_meta("Serial No").fields if not field.fieldname.startswith("column")]
				for field in serial_doc_fields:
					tyre_serial_doc.set(field, serial_doc.get(field))
				else:
					tyre_serial_doc.save(ignore_permissions=None, ignore_version=True)
		else:
			tyre_serial_doc=frappe.new_doc("Tyre Serial No")
			tyre_serial_doc.enable_manual_change=0
			serial_doc=frappe.get_doc("Serial No",{"name":serial})
			serial_doc_fields = [field.fieldname for field in frappe.get_meta("Serial No").fields if not field.fieldname.startswith("column")]
			for field in serial_doc_fields:
				tyre_serial_doc.set(field, serial_doc.get(field))
			else:
				tyre_serial_doc.save(ignore_permissions=None)
	#update Selling Rate
	update_outgoing_rate()
