# Copyright (c) 2023, Aerele and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

class ScarpTyre(Document):
	def on_submit(self):
		frappe.db.sql("UPDATE `tabSerial No` SET scarped_datetime='{0}',tyre_status='Scarped' WHERE name='{1}'".format(self.time_stamp,self.serial_no))
	
	def validate(self):
		serial_doc = frappe.get_doc("Serial No",{"name":self.serial_no})
		if serial_doc.operational_end_date and serial_doc.tyre_status == "Operation Ended":
			serial_no_fields = [
				"front_left_1",
				"front_right_1",
				"middle_left_1",
				"middle_right_1",
				"middle_left_2",
				"middle_right_2",
				"middle_left_3",
				"middle_right_3",
				"middle_left_4",
				"middle_right_4",
				"rear_left_1",
				"rear_right_1",
				"rear_left_2",
				"rear_right_2",
				"rear_left_3",
				"rear_right_3",
				"rear_left_4",
				"rear_right_4"
			]
			previous_tyre_position_doc = frappe.db.get_value("Vehicle Tire Position",{"vehicle_no":serial_doc.vehicle_no,"docstatus":1},serial_no_fields,as_dict=True)
			if previous_tyre_position_doc:
				previous_tyres = list(filter(lambda x: x is not None, previous_tyre_position_doc.values()))
				if self.serial_no in previous_tyres:
					frappe.throw(_(f"Tyre still active in {serial_doc.vehicle_no}"))
		elif serial_doc.scarped_datetime and serial_doc.tyre_status == "Scarped":
			frappe.throw(_(f"Tyre Already Scarped"))
		elif serial_doc.installed_datetime and serial_doc.tyre_status == "Installed":
			frappe.throw(_(f"Tyre still active in {serial_doc.vehicle_no}"))
		else:
			frappe.throw(_(f"Tyre still in company warehouse {serial_doc.warehouse}"))