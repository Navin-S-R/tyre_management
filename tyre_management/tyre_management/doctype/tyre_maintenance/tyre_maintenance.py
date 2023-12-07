# Copyright (c) 2023, Aerele and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import get_site_path,now
import base64
from frappe.model.naming import parse_naming_series
import json
from frappe import _
import requests
from tyre_management.python.frontend_api import get_smart_tyre_data_bulk

class TyreMaintenance(Document):
	def after_insert(self):
		if self.vehicle_no:
			if self.attach_img_byte:
				if not self.attach_img_extension:
					frappe.throw("Please mention the extension of the attachment")
				byte = self.attach_img_byte
				img_details = (parse_naming_series(f'{self.attach_img_name}-.#####') or now()) + "." + self.attach_img_extension
				path = f"{get_site_path()}/public/files/" + img_details
				decodeit = open(path, 'wb')
				decodeit.write(base64.b64decode(byte))
				decodeit.close()
				file_doc = frappe.new_doc("File")
				file_doc.file_url = "/files/"+img_details
				file_doc.is_private = 0
				file_doc.attached_to_doctype = self.doctype
				file_doc.attached_to_name = self.name
				file_doc.insert(ignore_permissions=True)
				self.attach_document = file_doc.file_url
				self.db_set("attach_document", self.attach_document)

	def validate(self):
		tyre_position = frappe.get_value("Vehicle Tire Position",{"ref_doctype":self.ref_doctype,
																		"docstatus" : 1,
																		"vehicle_no":self.vehicle_no},"name")
		if not self.vehicle_tire_position:
			self.vehicle_tire_position = tyre_position
		if self.vehicle_tire_position == tyre_position:
			position_doc = frappe.get_doc("Vehicle Tire Position",{"name":self.vehicle_tire_position})
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
				"rear_right_4",
				"spare_1",
				"spare_2"
			]
			for field in serial_no_fields:
				if position_doc.get(field)==self.serial_no:
					self.tire_position = field
		else:
			frappe.throw("This is not the latest tyre psition for this vehicle")
		if not self.vehicle_odometer_value_at_service:
			response=get_odometer_value([self.vehicle_no])
			for row in response:
				if row.get('plate') == self.vehicle_no:
					self.vehicle_odometer_value_at_service = row.get('end').get('odo_km')
		odometer_value_at_installation=frappe.db.get_value("Tyre Serial No",{"name": self.serial_no},'odometer_value_at_installation')
		self.tyre_milage_at_service = self.vehicle_odometer_value_at_service - odometer_value_at_installation
		if self.attach_document:
			self.attach_document_link=frappe.utils.get_url()+self.attach_document
		if not self.time_stamp:
			self.time_stamp = frappe.utils.now()

	def onsubmit(self):
		if not self.ref_tracking_log:
			frappe.throw(_("Fill the Vehicle Tracking Log"))
@frappe.whitelist()
def get_latest_tyre_position_for_vehicle(doctype, vehicle_no):
	tyre_position = frappe.get_value("Vehicle Tire Position",{"ref_doctype":doctype,"vehicle_no":vehicle_no},"name")
	return tyre_position

#Get Odometer value
@frappe.whitelist()
def get_odometer_value(vehicle_no):
	url = "http://service.lnder.in/api/method/tyre_management_connector.python.intangles_api.get_intangles_odometer_data"
	payload = json.dumps({
		"vehicle_no": vehicle_no
	})
	headers = {
		'Authorization': 'token 4567d5a4c58d5ba:50f7dcc70df884f',
		'Content-Type': 'application/json'
	}
	response = requests.request("GET", url, headers=headers, data=payload)
	if response.ok:
		response=response.json().get('message')
		return response
	else:
		response.raise_for_status()
